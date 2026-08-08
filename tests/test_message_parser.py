import unittest

from inbox_harbor.message_parser import extract_codes, parse_message


class MessageParserTests(unittest.TestCase):
    def test_extracts_contextual_code(self) -> None:
        raw = (
            b"From: Northwind <hello@northwind.example>\r\n"
            b"Subject: Your verification code is 482731\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            b"Use 482731 to finish signing in. Invoice 20260809."
        )
        parsed = parse_message(raw, 120)
        self.assertEqual(parsed["codes"], ["482731"])
        self.assertIn("Northwind", parsed["sender"])

    def test_html_parser_ignores_script_and_style(self) -> None:
        raw = (
            b"Subject: Login code\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
            b"<style>.secret{color:red}</style><p>Your OTP is <b>913204</b>.</p>"
            b"<script>alert('hidden')</script>"
        )
        parsed = parse_message(raw, 100)
        self.assertIn("913204", parsed["preview"])
        self.assertNotIn("alert", parsed["preview"])

    def test_codes_require_context(self) -> None:
        self.assertEqual(extract_codes("Receipt", "Order 123456 is shipped"), [])


if __name__ == "__main__":
    unittest.main()
