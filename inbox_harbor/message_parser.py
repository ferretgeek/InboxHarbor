from __future__ import annotations

import re
from email import policy
from email.message import Message
from email.parser import BytesParser
from html.parser import HTMLParser

SPACE_RE = re.compile(r"\s+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
CODE_CONTEXT_RE = re.compile(
    r"(?i)(?:verification|security|login|one[- ]?time|auth(?:entication)?|otp|pin|验证码|校验码|动态码|登录码|安全码)"
)
CODE_RE = re.compile(r"(?<![A-Za-z0-9])(?:\d{4,8}|[A-Z0-9]{6,10})(?![A-Za-z0-9])")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)

    def text(self) -> str:
        return " ".join(self.parts)


def clean_text(value: str, maximum: int) -> str:
    value = CONTROL_RE.sub(" ", value)
    value = SPACE_RE.sub(" ", value).strip()
    return value[:maximum]


def header_value(message: Message, name: str, maximum: int = 300) -> str:
    value = message.get(name, "")
    return clean_text(str(value), maximum)


def message_body(message: Message, maximum: int = 20_000) -> str:
    body = message.get_body(preferencelist=("plain", "html"))
    if body is None:
        candidates = [message] if not message.is_multipart() else list(message.walk())
        body = next(
            (
                part
                for part in candidates
                if part.get_content_maintype() == "text" and part.get_content_disposition() != "attachment"
            ),
            None,
        )
    if body is None:
        return ""
    try:
        content = body.get_content()
    except (LookupError, UnicodeError):
        payload = body.get_payload(decode=True) or b""
        content = payload.decode("utf-8", errors="replace")
    if not isinstance(content, str):
        return ""
    if body.get_content_type() == "text/html":
        parser = TextExtractor()
        parser.feed(content[: maximum * 8])
        content = parser.text()
    return clean_text(content, maximum)


def extract_codes(subject: str, body: str) -> list[str]:
    text = f"{subject} {body}"
    contexts = list(CODE_CONTEXT_RE.finditer(text))
    if not contexts:
        return []
    seen: set[str] = set()
    codes: list[str] = []
    for match in CODE_RE.finditer(text):
        code = match.group(0)
        if not any(
            match.start() <= context.end() + 40 and match.end() >= context.start() - 40
            for context in contexts
        ):
            continue
        if code not in seen:
            seen.add(code)
            codes.append(code)
        if len(codes) == 8:
            break
    return codes


def parse_message(raw: bytes, preview_chars: int) -> dict[str, object]:
    message = BytesParser(policy=policy.default).parsebytes(raw)
    subject = header_value(message, "Subject") or "（无主题）"
    sender = header_value(message, "From") or "（未知发件人）"
    date = header_value(message, "Date", 120)
    body = message_body(message)
    return {
        "subject": subject,
        "sender": sender,
        "date": date,
        "preview": clean_text(body, preview_chars),
        "codes": extract_codes(subject, body),
    }
