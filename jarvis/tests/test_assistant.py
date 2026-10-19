import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from jarvis import llm
from jarvis.assistant import Assistant
from jarvis.config import Settings
from jarvis.rea import RunResult


def make_settings(brain: Path, api_key: str | None = "key") -> Settings:
    return Settings(api_key=api_key, model="m", user_name="Shubham", brain_dir=brain)


class FakeRunner:
    def __init__(self, result: RunResult):
        self.result = result
        self.calls: list[list[str]] = []

    def __call__(self, argv):
        self.calls.append(argv)
        return self.result


class CommandTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.brain = Path(self._tmp.name)
        self.clock = lambda: datetime(2026, 10, 19, 9, 30, 0)

    def tearDown(self):
        self._tmp.cleanup()

    def assistant(self, runner=None, api_key="key", sender=None):
        return Assistant(
            make_settings(self.brain, api_key),
            sender=sender,
            runner=runner or FakeRunner(RunResult(0, "", "")),
            clock=self.clock,
        )

    def test_unknown_command(self):
        reply = self.assistant().handle("/nope")
        self.assertIn("Unknown command", reply.text)

    def test_quit_sets_flag(self):
        self.assertTrue(self.assistant().handle("/quit").quit)

    def test_time_uses_clock(self):
        self.assertEqual(self.assistant().handle("/time").text, "Monday 19 October 2026, 09:30:00")

    def test_empty_input_is_noop(self):
        reply = self.assistant().handle("   ")
        self.assertEqual(reply.text, "")
        self.assertFalse(reply.quit)

    def test_rea_passthrough_builds_argv(self):
        runner = FakeRunner(RunResult(0, "help text", ""))
        reply = self.assistant(runner=runner).handle("/rea --help")
        self.assertEqual(runner.calls[0][-1], "--help")
        self.assertEqual(reply.text, "help text")

    def test_rea_usage_without_args(self):
        self.assertIn("Usage", self.assistant().handle("/rea").text)

    def test_rea_setup_runs_setup(self):
        runner = FakeRunner(RunResult(0, "ok", ""))
        self.assistant(runner=runner).handle("/rea-setup")
        self.assertEqual(runner.calls[0][-1], "setup")

    def test_rea_failure_reports_exit_code(self):
        runner = FakeRunner(RunResult(2, "", "boom"))
        reply = self.assistant(runner=runner).handle("/rea analyze")
        self.assertIn("code 2", reply.text)
        self.assertIn("boom", reply.text)

    def test_node_check_uses_injected_version(self):
        a = self.assistant()
        a.node_version = lambda: "v18.0.0"
        self.assertIn("too old", a.handle("/node").text)
        a.node_version = lambda: "v22.22.0"
        self.assertIn("supported", a.handle("/node").text)

    def test_teardown_saves_report_to_brain(self):
        runner = FakeRunner(RunResult(0, '{"modules": 3}', ""))
        reply = self.assistant(runner=runner).handle("/teardown /apps/Notes")
        self.assertIn("Teardown saved", reply.text)
        saved = list(self.brain.glob("*.md"))
        self.assertEqual(len(saved), 1)
        self.assertIn('{"modules": 3}', saved[0].read_text(encoding="utf-8"))

    def test_teardown_failure_does_not_save(self):
        runner = FakeRunner(RunResult(1, "", "bad path"))
        reply = self.assistant(runner=runner).handle("/teardown /missing")
        self.assertIn("code 1", reply.text)
        self.assertEqual(list(self.brain.glob("*.md")), [])

    def test_teardown_requires_path(self):
        self.assertIn("Usage", self.assistant().handle("/teardown").text)

    def test_voice_toggle(self):
        a = self.assistant()
        self.assertIn("on", a.handle("/voice on").text)
        self.assertTrue(a.voice_out)
        self.assertIn("Usage", a.handle("/voice maybe").text)


class ChatTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.brain = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_chat_without_key_explains(self):
        a = Assistant(make_settings(self.brain, api_key=None))
        self.assertIn("ANTHROPIC_API_KEY", a.handle("hello").text)

    def test_chat_keeps_history_across_turns(self):
        seen = []

        def sender(payload):
            seen.append(list(payload["messages"]))
            return f"reply {len(seen)}"

        a = Assistant(make_settings(self.brain), sender=sender)
        self.assertEqual(a.handle("first").text, "reply 1")
        self.assertEqual(a.handle("second").text, "reply 2")
        self.assertEqual([m["content"] for m in seen[1]], ["first", "reply 1", "second"])

    def test_failed_chat_rolls_back_user_turn(self):
        def sender(payload):
            raise llm.LLMError("down")

        a = Assistant(make_settings(self.brain), sender=sender)
        self.assertIn("API error", a.handle("hi").text)
        self.assertEqual(a.history, [])

    def test_reset_clears_history(self):
        a = Assistant(make_settings(self.brain), sender=lambda p: "ok")
        a.handle("hi")
        a.handle("/reset")
        self.assertEqual(a.history, [])

    def test_voice_speaks_replies_when_enabled(self):
        spoken = []
        a = Assistant(make_settings(self.brain), sender=lambda p: "hello sir", speaker=lambda t: spoken.append(t) or True)
        a.handle("/voice on")
        a.handle("hi")
        self.assertEqual(spoken, ["hello sir"])


if __name__ == "__main__":
    unittest.main()
