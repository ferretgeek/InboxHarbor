import json
import unittest
import urllib.parse

from inbox_harbor.models import AccountRecord
from inbox_harbor.oauth import LOGIN_HOST, OAuthClient, OAuthError

ACCOUNT = AccountRecord(
    email="lina@example.com",
    client_id="12345678-1234-4234-9234-1234567890ab",
    refresh_token="synthetic-refresh-token-value",
    tenant="consumers",
)


class FakeResponse:
    def __init__(self, status: int, payload: dict[str, object]) -> None:
        self.status = status
        self.payload = json.dumps(payload).encode()

    def read(self, size: int) -> bytes:
        return self.payload


class FakeConnection:
    instances: list["FakeConnection"] = []
    response = FakeResponse(200, {"access_token": "a" * 40})

    def __init__(self, host: str, **kwargs: object) -> None:
        self.host = host
        self.kwargs = kwargs
        self.request_data: tuple[object, ...] | None = None
        self.closed = False
        self.__class__.instances.append(self)

    def request(self, method: str, path: str, *, body: bytes, headers: dict[str, str]) -> None:
        self.request_data = (method, path, body, headers)

    def getresponse(self) -> FakeResponse:
        return self.__class__.response

    def close(self) -> None:
        self.closed = True


class OAuthClientTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeConnection.instances.clear()
        FakeConnection.response = FakeResponse(200, {"access_token": "a" * 40})

    def test_uses_fixed_microsoft_host_and_v2_path(self) -> None:
        token = OAuthClient(connection_factory=FakeConnection).refresh(ACCOUNT)
        connection = FakeConnection.instances[0]
        self.assertEqual(connection.host, LOGIN_HOST)
        self.assertEqual(token, "a" * 40)
        method, path, body, _ = connection.request_data or (None, None, b"", None)
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/consumers/oauth2/v2.0/token")
        values = urllib.parse.parse_qs(body.decode())
        self.assertEqual(values["refresh_token"], [ACCOUNT.refresh_token])
        self.assertTrue(connection.closed)

    def test_error_never_reflects_upstream_description_or_token(self) -> None:
        FakeConnection.response = FakeResponse(
            400,
            {"error": "invalid_grant", "error_description": f"leaked {ACCOUNT.refresh_token}"},
        )
        with self.assertRaises(OAuthError) as caught:
            OAuthClient(connection_factory=FakeConnection).refresh(ACCOUNT)
        message = str(caught.exception)
        self.assertIn("invalid_grant", message)
        self.assertNotIn(ACCOUNT.refresh_token, message)


if __name__ == "__main__":
    unittest.main()
