import http.client
import os
import threading
import unittest
from unittest.mock import patch

from inbox_harbor.server import ServerConfig, build_config, create_server


class ServerBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        config = ServerConfig("127.0.0.1", 0, None, frozenset({"127.0.0.1", "localhost"}), True)
        self.server = create_server(config)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path: str, host: str = "127.0.0.1") -> tuple[int, bytes, dict[str, str]]:
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("GET", path, headers={"Host": host})
        response = connection.getresponse()
        body = response.read()
        headers = dict(response.getheaders())
        connection.close()
        return response.status, body, headers

    def test_health_has_privacy_headers(self) -> None:
        status, body, headers = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertIn(b'"privacy":"memory-only"', body)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])

    def test_rejects_dns_rebinding_host(self) -> None:
        status, _, _ = self.request("/api/health", "attacker.example")
        self.assertEqual(status, 400)


class ServerConfigTests(unittest.TestCase):
    def test_non_loopback_requires_key_and_host_allowlist(self) -> None:
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit):
            build_config("0.0.0.0", 4174)
        with (
            patch.dict(os.environ, {"INBOXHARBOR_ACCESS_TOKEN": "x" * 32}, clear=True),
            self.assertRaises(SystemExit),
        ):
            build_config("0.0.0.0", 4174)

    def test_ipv6_loopback_host_is_allowed(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = build_config("::1", 4174)
        self.assertIn("::1", config.allowed_hosts)


if __name__ == "__main__":
    unittest.main()
