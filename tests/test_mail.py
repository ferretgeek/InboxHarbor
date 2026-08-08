import imaplib
import unittest

from inbox_harbor.mail import IMAP_HOST, IMAP_PORT, fetch_account
from inbox_harbor.models import AccountRecord, FetchSettings

ACCOUNT = AccountRecord(
    email="lina@example.com",
    client_id="12345678-1234-4234-9234-1234567890ab",
    refresh_token="synthetic-refresh-token-value",
)


class FakeOAuth:
    def refresh(self, account: AccountRecord) -> str:
        return "safe-access-token-for-tests"


class FakeImap:
    def __init__(self, host: str, port: int, **kwargs: object) -> None:
        self.host = host
        self.port = port
        self.kwargs = kwargs
        self.auth_payload = b""
        self.logout_calls = 0

    def authenticate(self, mechanism: str, callback: object) -> tuple[str, list[bytes]]:
        self.auth_payload = callback(b"")  # type: ignore[operator]
        return "OK", [b""]

    def select(self, mailbox: str, readonly: bool = False) -> tuple[str, list[bytes]]:
        return "OK", [b"2"]

    def uid(self, command: str, *args: object) -> tuple[str, list[object]]:
        if command == "search":
            return "OK", [b"1 2"]
        raw = (
            b"From: Northwind <hello@northwind.example>\r\n"
            b"Subject: Verification code 482731\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            b"Your code is 482731."
        )
        return "OK", [(b"header", raw)]

    def close(self) -> tuple[str, list[bytes]]:
        return "OK", [b""]

    def logout(self) -> tuple[str, list[bytes]]:
        self.logout_calls += 1
        return "BYE", [b""]


class MailFetchTests(unittest.TestCase):
    def test_uses_only_fixed_microsoft_imap_and_readonly_select(self) -> None:
        instances: list[FakeImap] = []

        def factory(host: str, port: int, **kwargs: object) -> FakeImap:
            instance = FakeImap(host, port, **kwargs)
            instances.append(instance)
            return instance

        result = fetch_account(
            ACCOUNT,
            FetchSettings(limit=2),
            oauth_client=FakeOAuth(),  # type: ignore[arg-type]
            imap_factory=factory,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["messages"]), 2)
        self.assertEqual(instances[0].host, IMAP_HOST)
        self.assertEqual(instances[0].port, IMAP_PORT)
        self.assertNotIn(ACCOUNT.refresh_token.encode(), instances[0].auth_payload)

    def test_retries_one_transient_imap_abort(self) -> None:
        calls = 0

        class AbortOnceImap(FakeImap):
            def authenticate(self, mechanism: str, callback: object) -> tuple[str, list[bytes]]:
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise imaplib.IMAP4.abort("synthetic disconnect")
                return super().authenticate(mechanism, callback)

        result = fetch_account(
            ACCOUNT,
            FetchSettings(limit=1),
            oauth_client=FakeOAuth(),  # type: ignore[arg-type]
            imap_factory=AbortOnceImap,
        )
        self.assertEqual(calls, 2)
        self.assertEqual(result["status"], "ok")


if __name__ == "__main__":
    unittest.main()
