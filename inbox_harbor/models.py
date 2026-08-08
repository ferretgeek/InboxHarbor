from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

EMAIL_RE = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,190}$")
CLIENT_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
TENANT_RE = re.compile(r"^(?:common|consumers|organizations|[0-9a-fA-F-]{36}|[a-zA-Z0-9.-]{1,190})$")
ALLOWED_TENANTS = {"common", "consumers", "organizations"}


class ValidationError(ValueError):
    """A safe, user-facing validation error with no credential material."""


def _require_string(payload: dict[str, Any], field: str, maximum: int) -> str:
    value = payload.get(field)
    if not isinstance(value, str):
        raise ValidationError(f"{field} 必须是文本")
    value = value.strip()
    if not value or len(value) > maximum or any(ord(char) < 32 for char in value):
        raise ValidationError(f"{field} 的格式或长度不正确")
    return value


def mask_email(address: str) -> str:
    local, separator, domain = address.partition("@")
    if not separator:
        return "***"
    visible = local[:1]
    return f"{visible}{'*' * max(3, min(8, len(local) - 1))}@{domain}"


@dataclass(frozen=True, slots=True)
class AccountRecord:
    email: str
    client_id: str
    refresh_token: str
    tenant: str = "consumers"

    @classmethod
    def from_payload(cls, payload: Any) -> AccountRecord:
        if not isinstance(payload, dict):
            raise ValidationError("账号记录必须是对象")
        email = _require_string(payload, "email", 254).lower()
        client_id = _require_string(payload, "client_id", 36)
        refresh_token = _require_string(payload, "refresh_token", 8192)
        tenant = payload.get("tenant", "consumers")
        if not isinstance(tenant, str):
            raise ValidationError("tenant 必须是文本")
        tenant = tenant.strip().lower()
        if not EMAIL_RE.fullmatch(email):
            raise ValidationError("邮箱地址格式不正确")
        if not CLIENT_ID_RE.fullmatch(client_id):
            raise ValidationError("client_id 必须是有效的 UUID")
        if not TENANT_RE.fullmatch(tenant) or ".." in tenant:
            raise ValidationError("tenant 格式不正确")
        if tenant not in ALLOWED_TENANTS and "." not in tenant and len(tenant) != 36:
            raise ValidationError("tenant 必须是官方别名、租户 UUID 或已验证域名")
        return cls(email=email, client_id=client_id.lower(), refresh_token=refresh_token, tenant=tenant)

    @property
    def masked_email(self) -> str:
        return mask_email(self.email)


@dataclass(frozen=True, slots=True)
class FetchSettings:
    limit: int = 5
    preview_chars: int = 220
    timeout: int = 20
    max_message_bytes: int = 2_000_000
    concurrency: int = 3

    @classmethod
    def from_payload(cls, payload: Any) -> FetchSettings:
        if payload is None:
            return cls()
        if not isinstance(payload, dict):
            raise ValidationError("读取设置必须是对象")

        def bounded(name: str, default: int, low: int, high: int) -> int:
            value = payload.get(name, default)
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise ValidationError(f"{name} 必须在 {low} 到 {high} 之间")
            return value

        return cls(
            limit=bounded("limit", 5, 1, 20),
            preview_chars=bounded("preview_chars", 220, 80, 800),
            timeout=bounded("timeout", 20, 5, 60),
            max_message_bytes=bounded("max_message_bytes", 2_000_000, 64_000, 5_000_000),
            concurrency=bounded("concurrency", 3, 1, 4),
        )
