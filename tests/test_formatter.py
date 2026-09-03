from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from codepack.formatter import generate_ascii_tree, format_markdown, format_xml, format_json
from codepack.scanner import FileInfo


class TestFormatterModule(unittest.TestCase):
    def setUp(self):
        self.files = [
            FileInfo(
                rel_path="src/main.py",
                abs_path=Path("/test/src/main.py"),
                size_bytes=120,
                line_count=10,
                token_count=30,
                extension="py",
                is_binary=False,
                content="print('Hello from main')",
            ),
            FileInfo(
                rel_path="README.md",
                abs_path=Path("/test/README.md"),
                size_bytes=50,
                line_count=3,
                token_count=15,
                extension="md",
                is_binary=False,
                content="# Test Repo",
            ),
        ]

    def test_ascii_tree_generation(self):
        paths = ["src/main.py", "README.md"]
        tree = generate_ascii_tree(paths, root_name="my_app")
        self.assertIn("my_app/", tree)
        self.assertIn("src/", tree)
        self.assertIn("main.py", tree)
        self.assertIn("README.md", tree)

    def test_markdown_format(self):
        md = format_markdown(self.files, root_name="my_app")
        self.assertIn("# Codebase Context: my_app", md)
        self.assertIn("### `src/main.py`", md)
        self.assertIn("```python", md)
        self.assertIn("print('Hello from main')", md)

    def test_xml_format(self):
        xml = format_xml(self.files, root_name="my_app")
        self.assertIn("<context>", xml)
        self.assertIn("<source>src/main.py</source>", xml)
        self.assertIn("print('Hello from main')", xml)

    def test_json_format(self):
        json_str = format_json(self.files, root_name="my_app")
        self.assertIn('"project": "my_app"', json_str)
        self.assertIn('"total_files": 2', json_str)
        self.assertIn('"src/main.py"', json_str)


if __name__ == "__main__":
    unittest.main()
