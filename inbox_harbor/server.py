from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import socket
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from inbox_harbor import __version__
from inbox_harbor.mail import fetch_batch
from inbox_harbor.models import AccountRecord, FetchSettings, ValidationError

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
MAX_REQUEST_BYTES = 256_000
MAX_ACCOUNTS = 50
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/core.js": ("core.js", "text/javascript; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
    "/favicon.ico": ("favicon.ico", "image/x-icon"),
}
HOST_RE = re.compile(r"^(?:[a-zA-Z0-9.-]+|\[[0-9a-fA-F:]+\])(?::\d{1,5})?$")


@dataclass(frozen=True, slots=True)
class ServerConfig:
    host: str
    port: int
    access_token: str | None
    allowed_hosts: frozenset[str]
    loopback: bool


class RateLimiter:
    def __init__(self, limit: int = 12, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, client: str) -> bool:
        now = time.monotonic()
        with self.lock:
            history = self.requests[client]
            while history and now - history[0] > self.window_seconds:
                history.popleft()
            if len(history) >= self.limit:
                return False
            history.append(now)
            if len(self.requests) > 2048:
                self.requests = defaultdict(deque, {client: history})
            return True


def is_loopback_host(host: str) -> bool:
    return host.lower() in {"127.0.0.1", "localhost", "::1"}


def build_config(host: str, port: int) -> ServerConfig:
    loopback = is_loopback_host(host)
    access_token = os.environ.get("INBOXHARBOR_ACCESS_TOKEN", "").strip() or None
    if not loopback and (access_token is None or len(access_token) < 32):
        raise SystemExit("对外监听必须设置至少 32 字符的 INBOXHARBOR_ACCESS_TOKEN")
    raw_hosts = os.environ.get("INBOXHARBOR_ALLOWED_HOSTS", "")
    configured = {item.strip().lower() for item in raw_hosts.split(",") if item.strip()}
    if loopback:
        configured.update({"localhost", "127.0.0.1", "::1"})
    elif not configured:
        raise SystemExit("对外监听必须设置 INBOXHARBOR_ALLOWED_HOSTS")
    if not 1 <= port <= 65_535:
        raise SystemExit("端口必须在 1 到 65535 之间")
    return ServerConfig(host, port, access_token, frozenset(configured), loopback)


def make_handler(config: ServerConfig) -> type[BaseHTTPRequestHandler]:
    limiter = RateLimiter()

    class InboxHarborHandler(BaseHTTPRequestHandler):
        server_version = "InboxHarbor"
        sys_version = ""

        def log_message(self, format: str, *args: object) -> None:
            return

        def _security_headers(self, content_type: str) -> None:
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            )
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header(
                "Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
            )
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")

        def _host_allowed(self) -> bool:
            raw_host = self.headers.get("Host", "").strip().lower()
            if not raw_host or not HOST_RE.fullmatch(raw_host):
                return False
            hostname = urlsplit(f"//{raw_host}").hostname
            return bool(hostname and hostname.lower() in config.allowed_hosts)

        def _origin_allowed(self) -> bool:
            origin = self.headers.get("Origin")
            if not origin:
                return True
            parsed = urlsplit(origin)
            host = self.headers.get("Host", "").lower()
            return parsed.scheme in {"http", "https"} and parsed.netloc.lower() == host

        def _authorized(self) -> bool:
            if config.access_token is None:
                return config.loopback and self.client_address[0] in {"127.0.0.1", "::1"}
            supplied = self.headers.get("X-InboxHarbor-Key", "")
            return hmac.compare_digest(supplied.encode(), config.access_token.encode())

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
            self.send_response(status)
            self._security_headers("application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _reject_boundary(self) -> bool:
            if not self._host_allowed():
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Host 不在允许列表"})
                return True
            if not self._origin_allowed():
                self._json(HTTPStatus.FORBIDDEN, {"error": "跨来源请求已拒绝"})
                return True
            return False

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if self._reject_boundary():
                return
            if path == "/api/health":
                self._json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "version": __version__,
                        "auth_required": config.access_token is not None,
                        "privacy": "memory-only",
                    },
                )
                return
            static = STATIC_FILES.get(path)
            if static is None:
                self._json(HTTPStatus.NOT_FOUND, {"error": "页面不存在"})
                return
            filename, content_type = static
            file_path = WEB_ROOT / filename
            if not file_path.is_file():
                self._json(HTTPStatus.NOT_FOUND, {"error": "静态资源不存在"})
                return
            body = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self._security_headers(content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            if self._reject_boundary():
                return
            if path != "/api/fetch":
                self._json(HTTPStatus.NOT_FOUND, {"error": "接口不存在"})
                return
            if not self._authorized():
                self._json(HTTPStatus.UNAUTHORIZED, {"error": "访问密钥无效"})
                return
            if not limiter.allow(self.client_address[0]):
                self._json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "请求过于频繁，请稍后再试"})
                return
            if self.headers.get_content_type() != "application/json":
                self._json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "仅接受 application/json"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if not 1 <= length <= MAX_REQUEST_BYTES:
                self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "请求体大小不符合限制"})
                return
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "JSON 无法解析"})
                return
            try:
                if not isinstance(payload, dict):
                    raise ValidationError("请求必须是对象")
                raw_accounts = payload.get("accounts")
                if not isinstance(raw_accounts, list) or not 1 <= len(raw_accounts) <= MAX_ACCOUNTS:
                    raise ValidationError(f"账号数量必须在 1 到 {MAX_ACCOUNTS} 之间")
                accounts = [AccountRecord.from_payload(item) for item in raw_accounts]
                if len({account.email for account in accounts}) != len(accounts):
                    raise ValidationError("账号列表包含重复邮箱")
                settings = FetchSettings.from_payload(payload.get("settings"))
            except ValidationError as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            results = fetch_batch(accounts, settings)
            message_count = sum(len(item.get("messages", [])) for item in results)
            self._json(
                HTTPStatus.OK,
                {"results": results, "account_count": len(results), "message_count": message_count},
            )

    return InboxHarborHandler


def create_server(config: ServerConfig) -> ThreadingHTTPServer:
    server_class = ThreadingHTTPServer
    if config.host == "::1":

        class IPv6ThreadingHTTPServer(ThreadingHTTPServer):
            address_family = socket.AF_INET6

        server_class = IPv6ThreadingHTTPServer
    server = server_class((config.host, config.port), make_handler(config))
    server.daemon_threads = True
    return server


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="InboxHarbor privacy-first Outlook inbox viewer")
    parser.add_argument("--host", default="127.0.0.1", help="default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=4174, help="default: 4174")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = build_config(args.host, args.port)
    server = create_server(config)
    print(f"InboxHarbor {__version__} running at http://{config.host}:{config.port}")
    print("Credentials stay in request memory and are never written or logged.")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
