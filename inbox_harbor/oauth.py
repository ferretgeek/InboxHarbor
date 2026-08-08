from __future__ import annotations

import http.client
import json
import re
import ssl
import urllib.parse
from dataclasses import dataclass
from typing import Any

from inbox_harbor.models import AccountRecord

LOGIN_HOST = "login.microsoftonline.com"
MAX_TOKEN_RESPONSE = 128_000
SAFE_ERROR_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,80}$")


class OAuthError(RuntimeError):
    """Sanitized OAuth failure; never includes a token or upstream body."""


def make_tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def oauth_scope() -> str:
    return "https://outlook.office.com/IMAP.AccessAsUser.All offline_access"


@dataclass(slots=True)
class OAuthClient:
    timeout: int = 20
    connection_factory: Any = http.client.HTTPSConnection

    def refresh(self, account: AccountRecord) -> str:
        body = urllib.parse.urlencode(
            {
                "client_id": account.client_id,
                "refresh_token": account.refresh_token,
                "grant_type": "refresh_token",
                "scope": oauth_scope(),
            }
        ).encode()
        path = f"/{account.tenant}/oauth2/v2.0/token"
        connection = self.connection_factory(
            LOGIN_HOST,
            timeout=self.timeout,
            context=make_tls_context(),
        )
        try:
            connection.request(
                "POST",
                path,
                body=body,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": "InboxHarbor/1.0",
                },
            )
            response = connection.getresponse()
            raw = response.read(MAX_TOKEN_RESPONSE + 1)
        except (OSError, TimeoutError, http.client.HTTPException) as exc:
            raise OAuthError("无法安全连接 Microsoft 登录服务") from exc
        finally:
            connection.close()
        if len(raw) > MAX_TOKEN_RESPONSE:
            raise OAuthError("Microsoft 登录响应超过安全上限")
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OAuthError("Microsoft 登录响应无法解析") from exc
        if response.status != 200:
            code = data.get("error") if isinstance(data, dict) else None
            safe_code = code if isinstance(code, str) and SAFE_ERROR_RE.fullmatch(code) else "oauth_failed"
            raise OAuthError(f"Microsoft OAuth 拒绝请求（{safe_code}）")
        token = data.get("access_token") if isinstance(data, dict) else None
        if not isinstance(token, str) or not 20 <= len(token) <= 65_536:
            raise OAuthError("Microsoft 登录响应未包含有效 access_token")
        return token
