import unittest

from inbox_harbor.models import AccountRecord, FetchSettings, ValidationError, mask_email

VALID_ACCOUNT = {
    "email": "lina@example.com",
    "client_id": "12345678-1234-4234-9234-1234567890ab",
    "refresh_token": "synthetic-refresh-token-value",
    "tenant": "consumers",
}


class AccountRecordTests(unittest.TestCase):
    def test_accepts_valid_modern_auth_record(self) -> None:
        account = AccountRecord.from_payload(VALID_ACCOUNT)
        self.assertEqual(account.email, "lina@example.com")
        self.assertEqual(account.masked_email, "l***@example.com")

    def test_rejects_non_uuid_client_id(self) -> None:
        payload = {**VALID_ACCOUNT, "client_id": "not-a-client-id"}
        with self.assertRaises(ValidationError):
            AccountRecord.from_payload(payload)

    def test_rejects_path_like_tenant(self) -> None:
        payload = {**VALID_ACCOUNT, "tenant": "../consumers"}
        with self.assertRaises(ValidationError):
            AccountRecord.from_payload(payload)

    def test_masks_short_and_long_addresses(self) -> None:
        self.assertEqual(mask_email("a@example.com"), "a***@example.com")
        self.assertEqual(mask_email("longusername@example.com"), "l********@example.com")


class FetchSettingsTests(unittest.TestCase):
    def test_bounds_sensitive_work_limits(self) -> None:
        with self.assertRaises(ValidationError):
            FetchSettings.from_payload({"limit": 100})
        with self.assertRaises(ValidationError):
            FetchSettings.from_payload({"concurrency": 12})


if __name__ == "__main__":
    unittest.main()
