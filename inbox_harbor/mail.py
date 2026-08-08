from __future__ import annotations

import imaplib
import ssl
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from inbox_harbor.message_parser import parse_message
from inbox_harbor.models import AccountRecord, FetchSettings
from inbox_harbor.oauth import OAuthClient, OAuthError, make_tls_context

IMAP_HOST = "outlook.office365.com"
IMAP_PORT = 993


class MailboxError(RuntimeError):
    """Sanitized mailbox failure that never reflects server text."""


def xoauth2_payload(email_address: str, access_token: str) -> bytes:
    return f"user={email_address}\x01auth=Bearer {access_token}\x01\x01".encode()


def _message_bytes(fetch_data: Any) -> bytes | None:
    if not isinstance(fetch_data, list):
        return None
    for item in fetch_data:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            return item[1]
    return None


def fetch_account(
    account: AccountRecord,
    settings: FetchSettings,
    *,
    oauth_client: OAuthClient | None = None,
    imap_factory: Callable[..., Any] = imaplib.IMAP4_SSL,
) -> dict[str, object]:
    oauth_client = oauth_client or OAuthClient(timeout=settings.timeout)
    try:
        access_token = oauth_client.refresh(account)
    except OAuthError as exc:
        return {"account": account.masked_email, "status": "error", "error": str(exc), "messages": []}

    last_network_error: BaseException | None = None
    for attempt in range(2):
        client = None
        try:
            client = imap_factory(
                IMAP_HOST,
                IMAP_PORT,
                ssl_context=make_tls_context(),
                timeout=settings.timeout,
            )
            client.authenticate("XOAUTH2", lambda _: xoauth2_payload(account.email, access_token))
            status, _ = client.select("INBOX", readonly=True)
            if status != "OK":
                raise MailboxError("无法只读打开收件箱")
            status, search_data = client.uid("search", None, "ALL")
            if status != "OK" or not search_data:
                raise MailboxError("无法读取邮件索引")
            raw_ids = search_data[0] if isinstance(search_data[0], bytes) else b""
            message_ids = raw_ids.split()[-settings.limit :]
            messages: list[dict[str, object]] = []
            skipped_oversize = 0
            for message_id in reversed(message_ids):
                query = f"(BODY.PEEK[]<0.{settings.max_message_bytes}>)"
                status, data = client.uid("fetch", message_id, query)
                if status != "OK":
                    continue
                raw = _message_bytes(data)
                if not raw:
                    continue
                if len(raw) >= settings.max_message_bytes:
                    skipped_oversize += 1
                    continue
                messages.append(parse_message(raw, settings.preview_chars))
            try:
                client.close()
            except imaplib.IMAP4.error:
                pass
            try:
                client.logout()
            except (imaplib.IMAP4.error, OSError):
                pass
            client = None
            return {
                "account": account.masked_email,
                "status": "ok",
                "messages": messages,
                "skipped_oversize": skipped_oversize,
            }
        except imaplib.IMAP4.abort as exc:
            last_network_error = exc
            if attempt == 0:
                time.sleep(0.25)
                continue
        except imaplib.IMAP4.error:
            return {
                "account": account.masked_email,
                "status": "error",
                "error": "Microsoft IMAP 认证或邮箱访问被拒绝",
                "messages": [],
            }
        except MailboxError as exc:
            return {"account": account.masked_email, "status": "error", "error": str(exc), "messages": []}
        except (TimeoutError, ConnectionError, OSError, ssl.SSLError) as exc:
            last_network_error = exc
            if attempt == 0:
                time.sleep(0.25)
                continue
        finally:
            if client is not None:
                try:
                    client.logout()
                except (imaplib.IMAP4.error, OSError):
                    pass
    raise MailboxError("连接 Microsoft IMAP 服务超时或中断") from last_network_error


def fetch_batch(accounts: list[AccountRecord], settings: FetchSettings) -> list[dict[str, object]]:
    results: list[dict[str, object] | None] = [None] * len(accounts)
    with ThreadPoolExecutor(max_workers=min(settings.concurrency, len(accounts))) as executor:
        futures = {
            executor.submit(fetch_account, account, settings): index for index, account in enumerate(accounts)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except MailboxError as exc:
                results[index] = {
                    "account": accounts[index].masked_email,
                    "status": "error",
                    "error": str(exc),
                    "messages": [],
                }
            except Exception:  # noqa: BLE001 - this boundary deliberately hides all exception text
                results[index] = {
                    "account": accounts[index].masked_email,
                    "status": "error",
                    "error": "处理邮箱时发生未公开的内部错误",
                    "messages": [],
                }
    return [result for result in results if result is not None]
