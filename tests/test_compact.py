from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from codepack.compact import compact_python_code, compact_generic_code, compact_content


class TestCompactModule(unittest.TestCase):
    def test_compact_python(self):
        source = '''"""Module docstring."""
import os
import sys

TIMEOUT = 60

class Worker:
    """Worker class docstring."""
    status: str

    def run(self, task_id: int) -> bool:
        """Runs the task."""
        print("Starting task", task_id)
        result = True
        return result

def helper():
    """Helper doc."""
    pass
'''
        compacted = compact_python_code(source)
        self.assertIn("class Worker:", compacted)
        self.assertIn("def run(", compacted)
        self.assertIn("def helper():", compacted)
        self.assertIn("...", compacted)
        self.assertNotIn('print("Starting task", task_id)', compacted)

    def test_compact_generic_js(self):
        js_code = """
export function calculateTax(amount, rate) {
    const tax = amount * rate;
    return tax;
}

export class OrderService {
    constructor() {
        this.items = [];
    }
}
"""
        compacted = compact_generic_code(js_code)
        self.assertIn("export function calculateTax", compacted)
        self.assertIn("export class OrderService", compacted)
        self.assertNotIn("const tax = amount * rate", compacted)


if __name__ == "__main__":
    unittest.main()
