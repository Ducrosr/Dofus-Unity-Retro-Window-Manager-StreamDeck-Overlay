from __future__ import annotations

import unittest

from dwm.services.shell_attention_hook import (
    HSHELL_FLASH,
    HSHELL_RUDEAPPACTIVATED,
    HSHELL_WINDOWACTIVATED,
    classify_shell_event,
)


class ShellAttentionHookTests(unittest.TestCase):
    def test_shell_events_are_classified_without_windows_dependencies(self) -> None:
        self.assertEqual(classify_shell_event(HSHELL_FLASH), "attention")
        self.assertEqual(classify_shell_event(HSHELL_WINDOWACTIVATED), "foreground")
        self.assertEqual(classify_shell_event(HSHELL_RUDEAPPACTIVATED), "foreground")
        self.assertIsNone(classify_shell_event(12345))


if __name__ == "__main__":
    unittest.main()
