import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from jarvis import desktop, voice, wake
from jarvis.assistant import Assistant
from jarvis.config import Settings


class WakeWordTests(unittest.TestCase):
    def test_command_after_wake_word(self):
        self.assertEqual(wake.extract_command("Jarvis, what time is it"), "what time is it")

    def test_lead_in_words_allowed(self):
        self.assertEqual(wake.extract_command("Hey Jarvis open notepad"), "open notepad")
        self.assertEqual(wake.extract_command("ok jarvis"), "")

    def test_bare_wake_word_means_listening(self):
        self.assertEqual(wake.extract_command("Jarvis"), "")

    def test_not_addressed_returns_none(self):
        self.assertIsNone(wake.extract_command("what time is it"))
        self.assertIsNone(wake.extract_command("tell the jarvis team hello"))
        self.assertIsNone(wake.extract_command(""))

    def test_stop_requests(self):
        self.assertTrue(wake.is_stop_request("stop listening"))
        self.assertTrue(wake.is_stop_request("Goodbye."))
        self.assertFalse(wake.is_stop_request("open notes"))


class DesktopTests(unittest.TestCase):
    def test_resolve_known_app(self):
        self.assertEqual(desktop.resolve("Notepad", "Windows"), ["notepad.exe"])
        self.assertEqual(desktop.resolve("notes", "Darwin"), ["open", "-a", "Notes"])

    def test_unknown_app_refused(self):
        self.assertIsNone(desktop.resolve("rm -rf /", "Linux"))
        launched = []
        msg = desktop.open_app("rm -rf /", "Linux", launcher=lambda argv: launched.append(argv))
        self.assertIn("can't open", msg)
        self.assertEqual(launched, [])

    def test_open_launches_fixed_argv_without_shell(self):
        launched = []
        msg = desktop.open_app("calculator", "Windows", launcher=lambda argv: launched.append(argv))
        self.assertEqual(launched, [["calc.exe"]])
        self.assertIn("Opening calculator", msg)

    def test_launch_failure_reported(self):
        def broken(argv):
            raise OSError("not installed")

        self.assertIn("Could not open", desktop.open_app("notepad", "Windows", launcher=broken))


class VoiceFallbackTests(unittest.TestCase):
    def test_speak_empty_text_is_false(self):
        self.assertFalse(voice.speak("   "))

    def test_missing_packages_reported_as_pip_names(self):
        missing = voice.missing_packages()
        for name in missing:
            self.assertIn(name, {"pyttsx3", "SpeechRecognition"})


class AssistantVoiceCommandTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(api_key=None, model="m", user_name="Shubham", brain_dir=Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_listen_handles_heard_command(self):
        a = Assistant(self.settings, listener=lambda: "/time", clock=lambda: datetime(2026, 10, 19, 9, 0))
        reply = a.handle("/listen")
        self.assertIn('Heard: "/time"', reply.text)
        self.assertIn("Monday 19 October 2026", reply.text)

    def test_listen_sends_plain_speech_to_chat(self):
        a = Assistant(self.settings, listener=lambda: "what time is it")
        reply = a.handle("/listen")
        self.assertIn('Heard: "what time is it"', reply.text)
        self.assertIn("ANTHROPIC_API_KEY", reply.text)  # no key set, so chat explains

    def test_listen_nothing_heard(self):
        a = Assistant(self.settings, listener=lambda: None)
        self.assertEqual(a.handle("/listen").text, "I didn't catch that.")

    def test_listen_can_quit(self):
        a = Assistant(self.settings, listener=lambda: "/quit")
        self.assertTrue(a.handle("/listen").quit)

    def test_open_command_uses_opener(self):
        seen = []
        a = Assistant(self.settings, opener=lambda name: seen.append(name) or "ok")
        a.handle("/open notes")
        self.assertEqual(seen, ["notes"])

    def test_open_requires_app(self):
        a = Assistant(self.settings)
        self.assertIn("Usage", a.handle("/open").text)

    def test_apps_lists_allowlist(self):
        a = Assistant(self.settings)
        self.assertIn("Allowed apps", a.handle("/apps").text)


if __name__ == "__main__":
    unittest.main()
