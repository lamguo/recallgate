import tempfile
import unittest
from pathlib import Path

from recallgate.core import (
    Paths,
    add_memory,
    change_status,
    delete_memory,
    estimate_report,
    estimate_tokens,
    generate_brief,
    generate_correction,
    init_workspace,
    info_memory,
    list_memories,
    promote_memory,
    remove_old_file,
    review_memories,
    search_memories,
    update_memory,
    slugify,
    trim_lines_to_budget,
)


class RecallGateCoreTests(unittest.TestCase):
    def test_empty_memory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            with self.assertRaises(ValueError):
                add_memory("   ", root=root)

    def test_init_and_add_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            memory = add_memory(
                "Keep zero core dependencies.",
                root=root,
                scope="project",
                type_="rule",
                roles="coder",
                priority="high",
                importance=10,
            )
            self.assertEqual(memory["id"], "mem_0001")
            self.assertEqual(memory["status"], "active")
            self.assertTrue((root / ".recallgate" / "index.json").exists())
            self.assertEqual(len(list_memories(root=root, status="active")), 1)

    def test_trash_not_in_brief_then_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            m = add_memory("Tests must use temp fixtures, not fragile example files.", root=root, type_="pitfall", roles="tester")
            brief = generate_brief("fix tests", root=root, role="tester")
            self.assertIn("temp fixtures", brief)
            change_status(m["id"], "trash", root=root)
            brief = generate_brief("fix tests", root=root, role="tester")
            self.assertNotIn("temp fixtures", brief)
            change_status(m["id"], "active", root=root)
            brief = generate_brief("fix tests", root=root, role="tester")
            self.assertIn("temp fixtures", brief)

    def test_role_brief_filters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            add_memory("README must stay concise.", root=root, type_="rule", roles="writer")
            add_memory("Preserve public CLI behavior.", root=root, type_="rule", roles="coder")
            writer = generate_brief("update README", root=root, role="writer")
            self.assertIn("README", writer)
            self.assertIn("RecallGate Writer Brief", writer)

    def test_correction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            add_memory("This is a Python CLI project, not a WordPress project.", root=root, type_="correction", roles="all", priority="high")
            text = generate_correction("model thinks this is WordPress", root=root)
            self.assertIn("local active memory", text)
            self.assertIn("Python CLI", text)

    def test_estimator_and_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            add_memory("Temporary note.", root=root, importance=2)
            report = estimate_report(root=root, query="general")
            self.assertIn("Model/API calls used for this estimate: 0", report)
            self.assertGreater(estimate_tokens("hello world"), 0)
            review = review_memories(root=root)
            self.assertIn("RecallGate Review", review)

    def test_estimate_does_not_update_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            memory = add_memory("Keep zero core dependencies.", root=root, type_="rule", roles="coder")
            before = list_memories(root=root)[0]["use_count"]
            estimate_report(root=root, query="fix code", role="coder")
            after = list_memories(root=root)[0]["use_count"]
            self.assertEqual(before, after)
            generate_brief("fix code", root=root, role="coder")
            used = list_memories(root=root)[0]["use_count"]
            self.assertGreater(used, after)

    def test_promote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            m = add_memory("Current task focuses on CI.", root=root, scope="conversation", type_="task")
            promoted = promote_memory(m["id"], root=root, to_scope="project")
            self.assertEqual(promoted["scope"], "project")

    def test_role_brief_does_not_leak_other_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            add_memory("Reviewer only release risk.", root=root, type_="rule", roles="reviewer")
            add_memory("Writer only README style.", root=root, type_="rule", roles="writer")
            writer = generate_brief("update README", root=root, role="writer")
            self.assertIn("Writer only README style", writer)
            self.assertNotIn("Reviewer only release risk", writer)

    def test_delete_removes_memory_from_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            memory = add_memory("Remove me permanently.", root=root)
            delete_memory(memory["id"], root=root)
            self.assertEqual(list_memories(root=root), [])
            brief = generate_brief("general", root=root)
            self.assertNotIn("Remove me permanently", brief)

    def test_note_memories_can_appear_in_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            add_memory("Writer docs.", root=root, roles="writer")
            writer = generate_brief("update docs", root=root, role="writer")
            self.assertIn("Writer docs", writer)

    def test_markdown_front_matter_does_not_store_stale_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            memory = add_memory("Archive me.", root=root)
            path = root / ".recallgate" / memory["file"]
            self.assertNotIn("file:", path.read_text(encoding="utf-8"))
            changed = change_status(memory["id"], "trash", root=root)
            new_path = root / ".recallgate" / changed["file"]
            self.assertNotIn("file:", new_path.read_text(encoding="utf-8"))

    def test_remove_old_file_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            outside = root / "outside.md"
            outside.write_text("do not delete", encoding="utf-8")
            with self.assertRaises(ValueError):
                remove_old_file(Paths(root), "../outside.md")
            self.assertTrue(outside.exists())

    def test_status_dir_rejects_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            with self.assertRaises(ValueError):
                Paths(root).status_dir("deleted")

    def test_list_role_all_means_unfiltered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            add_memory("Writer memory.", root=root, roles="writer")
            add_memory("Coder memory.", root=root, roles="coder")
            self.assertEqual(len(list_memories(root=root, role="all")), 2)
            self.assertEqual(len(list_memories(root=root, role="writer")), 1)

    def test_brief_role_all_disables_role_guessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            add_memory("Coder only memory.", root=root, roles="coder")
            add_memory("Writer only memory.", root=root, roles="writer")
            brief = generate_brief("fix code", root=root, role="all")
            self.assertIn("RecallGate Brief", brief)
            self.assertNotIn("RecallGate Coder Brief", brief)
            self.assertIn("Coder only memory", brief)
            self.assertIn("Writer only memory", brief)

    def test_automatic_keywords_skip_common_stopwords(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            memory = add_memory("This is a Python CLI project", root=root)
            self.assertEqual(memory["keywords"], ["python", "cli", "project"])

    def test_slugify_preserves_cjk_text(self):
        self.assertEqual(slugify("这是一个测试"), "这是一个测试")
        self.assertEqual(slugify("!!!"), "memory")

    def test_default_budget_is_read_from_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            config = root / ".recallgate" / "config.toml"
            config.write_text('default_budget = 35\ndefault_roles = ["coder"]\n', encoding="utf-8")
            add_memory("Keep zero core dependencies and preserve public CLI behavior.", root=root, type_="rule", roles="coder")
            brief = generate_brief("fix code", root=root, role="coder", include_estimate=False)
            self.assertLessEqual(estimate_tokens(brief), 35)

    def test_trim_first_line_respects_tiny_budget(self):
        line = "x" * 400
        trimmed = trim_lines_to_budget([line], 10)
        self.assertEqual(len(trimmed), 1)
        self.assertLessEqual(estimate_tokens(trimmed[0]), 10)

    def test_search_memories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            add_memory("Tests must use temp fixtures, not fragile example files.", root=root, type_="pitfall", roles="tester")
            add_memory("README must stay concise.", root=root, type_="rule", roles="writer")
            results = search_memories("fixtures", root=root)
            self.assertEqual(len(results), 1)
            self.assertIn("fixtures", results[0]["short"])
            writer_results = search_memories("README", root=root, role="writer")
            self.assertEqual(len(writer_results), 1)
            self.assertIn("README", writer_results[0]["short"])

    def test_brief_does_not_emit_empty_relevant_memory_heading_when_budget_is_tight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            config = root / ".recallgate" / "config.toml"
            config.write_text('default_budget = 50\ndefault_roles = ["coder"]\n', encoding="utf-8")
            for i in range(4):
                add_memory(
                    f"Very long memory item {i} that should not fit inside the tiny brief budget after authority rules.",
                    root=root,
                    roles="coder",
                    type_="rule",
                    short=f"Very long memory item {i} that should not fit inside the tiny brief budget after authority rules.",
                )
            brief = generate_brief("fix code", root=root, role="coder", include_estimate=False)
            self.assertNotIn("Relevant Memory:", brief)

    def test_correction_uses_default_budget_from_config_when_not_provided(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            config = root / ".recallgate" / "config.toml"
            config.write_text('default_budget = 40\ndefault_roles = ["coder"]\n', encoding="utf-8")
            add_memory(
                "This is a Python CLI project, not a WordPress project. Keep zero core dependencies.",
                root=root,
                scope="project",
                type_="rule",
                roles="all",
                priority="critical",
                short="Python CLI repo; keep zero core dependencies.",
            )
            text = generate_correction("model thinks this is WordPress", root=root)
            body = text.split("Estimated tokens:")[0]
            self.assertLessEqual(estimate_tokens(body), 40)

    def test_update_and_info_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            memory = add_memory("Original memory.", root=root, roles="coder", priority="low")
            updated = update_memory(
                memory["id"],
                root=root,
                content="Updated Python CLI memory.",
                short="Updated short.",
                priority="critical",
                keywords="python,cli",
            )
            self.assertEqual(updated["priority"], "critical")
            self.assertEqual(updated["short"], "Updated short.")
            info = info_memory(memory["id"], root=root)
            self.assertEqual(info["content"], "Updated Python CLI memory.")
            self.assertEqual(info["keywords"], ["cli", "python"])

    def test_list_sort_by_use_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            first = add_memory("First memory.", root=root, roles="coder")
            second = add_memory("Second memory.", root=root, roles="coder")
            generate_brief("first", root=root, role="coder")
            generate_brief("first", root=root, role="coder")
            memories = list_memories(root=root, sort_by="use_count", reverse=True)
            self.assertGreaterEqual(memories[0].get("use_count", 0), memories[-1].get("use_count", 0))

    def test_review_apply_archives_low_importance_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            memory = add_memory("Temporary low value note.", root=root, importance=1)
            text = review_memories(root=root, apply=True)
            self.assertIn("Applied actions", text)
            info = info_memory(memory["id"], root=root)
            self.assertEqual(info["status"], "archived")



if __name__ == "__main__":
    unittest.main()
