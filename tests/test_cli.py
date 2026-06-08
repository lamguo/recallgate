import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from recallgate.cli import main


class RecallGateCliTests(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(list(args))
        return code, buf.getvalue()

    def test_root_and_json_output_for_add_list_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, out = self.run_cli("init", "--root", str(root), "--json")
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(out)["ok"])

            code, out = self.run_cli(
                "add",
                "Keep zero core dependencies.",
                "--root",
                str(root),
                "--type",
                "rule",
                "--role",
                "coder",
                "--json",
            )
            self.assertEqual(code, 0)
            memory = json.loads(out)
            self.assertEqual(memory["id"], "mem_0001")

            code, out = self.run_cli("list", "--root", str(root), "--json")
            self.assertEqual(code, 0)
            self.assertEqual(len(json.loads(out)), 1)

            code, out = self.run_cli("info", "mem_0001", "--root", str(root), "--json")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["content"], "Keep zero core dependencies.")

    def test_update_and_review_apply_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_cli("init", "--root", str(root))
            self.run_cli("add", "Temporary low value note.", "--root", str(root), "--importance", "1")

            code, out = self.run_cli(
                "update",
                "mem_0001",
                "--root",
                str(root),
                "--short",
                "Low value note.",
                "--priority",
                "low",
                "--json",
            )
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["short"], "Low value note.")

            code, out = self.run_cli("review", "--root", str(root), "--apply")
            self.assertEqual(code, 0)
            self.assertIn("Applied actions", out)

            code, out = self.run_cli("info", "mem_0001", "--root", str(root), "--json")
            self.assertEqual(json.loads(out)["status"], "archived")


if __name__ == "__main__":
    unittest.main()
