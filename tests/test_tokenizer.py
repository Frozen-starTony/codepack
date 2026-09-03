from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from codepack.tokenizer import estimate_tokens, format_token_count, format_size


class TestTokenizerModule(unittest.TestCase):
    def test_estimate_tokens_empty(self):
        self.assertEqual(estimate_tokens(""), 0)

    def test_estimate_tokens_text(self):
        sample = "def hello_world():\n    print('Hello, world!')\n"
        tokens = estimate_tokens(sample)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, 50)

    def test_format_token_count(self):
        self.assertEqual(format_token_count(500), "500")
        self.assertEqual(format_token_count(1500), "1.5k")
        self.assertEqual(format_token_count(2_400_000), "2.4M")

    def test_format_size(self):
        self.assertEqual(format_size(500), "500 B")
        self.assertEqual(format_size(2048), "2.0 KB")
        self.assertEqual(format_size(5 * 1024 * 1024), "5.0 MB")


if __name__ == "__main__":
    unittest.main()
