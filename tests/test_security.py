from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from codepack.security import redact_secrets


class TestSecurityModule(unittest.TestCase):
    def test_openai_key_redaction(self):
        sample = "openai_key = 'sk-1234567890abcdef1234567890abcdef'"
        redacted, report = redact_secrets(sample)
        self.assertTrue(report.has_secrets)
        self.assertNotIn("sk-1234567890", redacted)
        self.assertIn("[REDACTED_OPENAI_KEY]", redacted)

    def test_anthropic_key_redaction(self):
        sample = "anthropic_key = 'sk-ant-api03-abcdef1234567890abcdef1234567890'"
        redacted, report = redact_secrets(sample)
        self.assertTrue(report.has_secrets)
        self.assertNotIn("sk-ant-", redacted)
        self.assertIn("[REDACTED_ANTHROPIC_KEY]", redacted)

    def test_github_token_redaction(self):
        sample = "gh_token = 'ghp_123456789012345678901234567890123456'"
        redacted, report = redact_secrets(sample)
        self.assertTrue(report.has_secrets)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", redacted)

    def test_google_key_redaction(self):
        sample = "google_key = 'AIzaSyA1234567890123456789012345678901'"
        redacted, report = redact_secrets(sample)
        self.assertTrue(report.has_secrets)
        self.assertIn("[REDACTED_GOOGLE_API_KEY]", redacted)

    def test_clean_code_no_false_positives(self):
        sample = "def calculate_total(items):\n    return sum(items)"
        redacted, report = redact_secrets(sample)
        self.assertFalse(report.has_secrets)
        self.assertEqual(sample, redacted)


if __name__ == "__main__":
    unittest.main()
