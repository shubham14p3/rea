import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from jarvis import rea


class NodeVersionTests(unittest.TestCase):
    def test_supported_versions(self):
        for version in ["v22.19.0", "v22.22.0", "v24.11.0", "v24.15.2", "v26.0.0", "v27.1.0"]:
            with self.subTest(version=version):
                self.assertTrue(rea.node_supported(version))

    def test_unsupported_versions(self):
        for version in ["v22.18.0", "v20.11.1", "v24.10.0", "v25.0.0", "not-a-version", ""]:
            with self.subTest(version=version):
                self.assertFalse(rea.node_supported(version))


class ArgvTests(unittest.TestCase):
    def test_argv_is_a_list_with_no_shell(self):
        argv = rea.build_argv(["--help"])
        self.assertEqual(argv[:2], ["npx", "-y"])
        self.assertEqual(argv[-1], "--help")

    def test_js_analysis_argv_keeps_path_as_one_argument(self):
        path = "/tmp/my app; rm -rf ~"  # shell metacharacters stay inside one argv entry
        argv = rea.analyze_js_argv(path)
        self.assertIn(path, argv)
        self.assertEqual(argv[-1], "--json")

    def test_empty_target_rejected(self):
        with self.assertRaises(ValueError):
            rea.analyze_js_argv("   ")


class TeardownTests(unittest.TestCase):
    def test_save_writes_markdown_with_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = rea.save_teardown(
                Path(tmp), "JS teardown: Notes App", "body", datetime(2026, 10, 19, 9, 0)
            )
            self.assertEqual(path.name, "2026-10-19-js-teardown-notes-app.md")
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# JS teardown: Notes App"))
            self.assertIn("body", text)

    def test_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = datetime(2026, 10, 19, 9, 0)
            first = rea.save_teardown(Path(tmp), "same", "one", now)
            second = rea.save_teardown(Path(tmp), "same", "two", now)
            self.assertNotEqual(first, second)
            self.assertIn("one", first.read_text(encoding="utf-8"))
            self.assertIn("two", second.read_text(encoding="utf-8"))

    def test_slugify_handles_empty_title(self):
        self.assertEqual(rea.slugify("!!!"), "teardown")


if __name__ == "__main__":
    unittest.main()
