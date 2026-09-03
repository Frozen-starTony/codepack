from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from codepack.scanner import scan_directory, is_binary_file, compile_path_matcher


class TestScannerModule(unittest.TestCase):
    def test_path_matcher(self):
        matcher = compile_path_matcher(["*.tmp", "ignore_dir/"])
        self.assertTrue(matcher("test.tmp", False))
        self.assertTrue(matcher("ignore_dir/file.py", False))
        self.assertTrue(matcher("ignore_dir", True))
        self.assertFalse(matcher("main.py", False))

    def test_scan_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            # Create files
            (root / "main.py").write_text("print('test')", encoding="utf-8")
            (root / "data.json").write_text("{}", encoding="utf-8")

            # Create ignored dir
            (root / "node_modules").mkdir()
            (root / "node_modules" / "junk.js").write_text("alert(1)", encoding="utf-8")

            # Create custom gitignore
            (root / ".gitignore").write_text("*.json\n", encoding="utf-8")

            files = scan_directory(str(root), respect_gitignore=True)
            rel_paths = [f.rel_path for f in files]

            self.assertIn("main.py", rel_paths)
            self.assertNotIn("data.json", rel_paths)
            self.assertNotIn("node_modules/junk.js", rel_paths)

    def test_binary_detection(self):
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            temp_path = Path(f.name)

        try:
            self.assertTrue(is_binary_file(temp_path))
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
