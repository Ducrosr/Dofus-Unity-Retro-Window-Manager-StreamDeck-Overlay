from __future__ import annotations

import unittest

from dwm.services.focus import (
    FocusError,
    _focus_hwnd_with_api,
    _is_streamdeck_process_name,
    _is_streamdeck_window,
)


class FakeFocusApi:
    def __init__(
        self,
        *,
        foreground: int = 900,
        foreground_after_attempt: int = 2,
        foreground_process_name: str = "StreamDeck.exe",
        foreground_window_title: str = "Stream Deck",
        alt_unlocks: bool = True,
        prepare_succeeds: bool = True,
        minimize_release_method: str | None = "async",
    ) -> None:
        self.foreground = foreground
        self.foreground_after_attempt = foreground_after_attempt
        self.foreground_process_name = foreground_process_name
        self.foreground_window_title = foreground_window_title
        self.alt_unlocks = alt_unlocks
        self.prepare_succeeds = prepare_succeeds
        self.minimize_release_method = minimize_release_method
        self.foreground_attempts = 0
        self.attached: list[tuple[int, int, bool]] = []
        self.alt_tapped = False
        self.prepared_hwnd = 0
        self.minimized_hwnd = 0
        self.minimize_attempts: list[str] = []
        self.iconic_windows: set[int] = set()
        self.topmost_pulsed = 0
        self.iconic = False
        self.restore_to_maximized = False

    def is_window(self, hwnd: int) -> bool:
        return hwnd == 100

    def is_iconic(self, hwnd: int) -> bool:
        return hwnd in self.iconic_windows or (hwnd == 100 and self.iconic)

    def should_restore_to_maximized(self, _hwnd: int) -> bool:
        return self.restore_to_maximized

    def show_window(self, _hwnd: int, _command: int) -> None:
        return

    def get_foreground_window(self) -> int:
        return self.foreground

    def get_window_thread_id(self, hwnd: int) -> int:
        return {900: 9, 100: 10}.get(hwnd, 0)

    def get_current_thread_id(self) -> int:
        return 8

    def attach_thread_input(self, source_thread: int, target_thread: int, attach: bool) -> bool:
        self.attached.append((source_thread, target_thread, attach))
        return True

    def bring_window_to_top(self, _hwnd: int) -> None:
        return

    def set_foreground_window(self, hwnd: int) -> bool:
        self.foreground_attempts += 1
        if self.foreground_attempts >= self.foreground_after_attempt:
            self.foreground = hwnd
            return True
        return False

    def set_active_window(self, _hwnd: int) -> None:
        return

    def set_focus(self, _hwnd: int) -> None:
        return

    def switch_to_window(self, _hwnd: int) -> None:
        return

    def tap_alt(self) -> None:
        self.alt_tapped = True
        if self.alt_unlocks:
            self.foreground_after_attempt = self.foreground_attempts + 1

    def get_window_process_name(self, _hwnd: int) -> str:
        return self.foreground_process_name

    def get_window_title(self, _hwnd: int) -> str:
        return self.foreground_window_title

    def prepare_window_for_activation(self, hwnd: int) -> bool:
        self.prepared_hwnd = hwnd
        return self.prepare_succeeds

    def _minimize(self, hwnd: int, method: str) -> bool:
        self.minimize_attempts.append(method)
        self.minimized_hwnd = hwnd
        if self.minimize_release_method == method:
            self.iconic_windows.add(hwnd)
            if self.prepared_hwnd and self.prepare_succeeds:
                self.foreground = self.prepared_hwnd
            else:
                self.foreground = 0
        return True

    def minimize_window_async(self, hwnd: int) -> bool:
        return self._minimize(hwnd, "async")

    def post_minimize_command(self, hwnd: int) -> bool:
        return self._minimize(hwnd, "post")

    def force_minimize_window(self, hwnd: int) -> None:
        self._minimize(hwnd, "force")

    def pulse_topmost(self, hwnd: int) -> None:
        self.topmost_pulsed = hwnd
        self.foreground = hwnd


class FocusTests(unittest.TestCase):
    def test_direct_activation_does_not_attach_threads(self) -> None:
        api = FakeFocusApi(foreground_after_attempt=1)

        _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertEqual(api.foreground, 100)
        self.assertEqual(api.attached, [])

    def test_streamdeck_foreground_attaches_both_input_queues(self) -> None:
        api = FakeFocusApi(foreground_after_attempt=2)

        _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertEqual(
            api.attached,
            [(8, 9, True), (8, 10, True), (8, 10, False), (8, 9, False)],
        )
        self.assertEqual(api.foreground, 100)

    def test_alt_fallback_is_used_only_after_regular_methods_fail(self) -> None:
        api = FakeFocusApi(foreground_after_attempt=99)

        _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertTrue(api.alt_tapped)
        self.assertEqual(api.foreground, 100)

    def test_streamdeck_foreground_is_minimized_as_last_resort(self) -> None:
        api = FakeFocusApi(foreground_after_attempt=99, alt_unlocks=False)

        _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertEqual(api.prepared_hwnd, 100)
        self.assertEqual(api.minimized_hwnd, 900)
        self.assertEqual(api.foreground, 100)

    def test_failed_z_order_preparation_does_not_skip_minimization(self) -> None:
        api = FakeFocusApi(
            foreground_after_attempt=99,
            alt_unlocks=False,
            prepare_succeeds=False,
        )

        _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertEqual(api.minimize_attempts, ["async"])
        self.assertEqual(api.topmost_pulsed, 100)

    def test_minimization_falls_back_to_system_command(self) -> None:
        api = FakeFocusApi(
            foreground_after_attempt=99,
            alt_unlocks=False,
            minimize_release_method="post",
        )

        _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertEqual(api.minimize_attempts, ["async", "post"])

    def test_minimization_falls_back_to_synchronous_force(self) -> None:
        api = FakeFocusApi(
            foreground_after_attempt=99,
            alt_unlocks=False,
            minimize_release_method="force",
        )

        _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertEqual(api.minimize_attempts, ["async", "post", "force"])

    def test_unrelated_foreground_window_is_never_minimized(self) -> None:
        api = FakeFocusApi(
            foreground_after_attempt=99,
            foreground_process_name="notepad.exe",
            foreground_window_title="Bloc-notes",
            alt_unlocks=False,
        )

        with self.assertRaises(FocusError):
            _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertEqual(api.minimized_hwnd, 0)

    def test_streamdeck_title_is_used_when_process_name_is_unavailable(self) -> None:
        api = FakeFocusApi(
            foreground_after_attempt=99,
            foreground_process_name="",
            foreground_window_title="Stream Deck",
            alt_unlocks=False,
        )

        _focus_hwnd_with_api(100, api, verify_timeout=0)

        self.assertEqual(api.minimized_hwnd, 900)

    def test_streamdeck_executable_name_matching_is_strict(self) -> None:
        self.assertTrue(_is_streamdeck_process_name(r"C:\\Program Files\\Elgato\\StreamDeck.exe"))
        self.assertTrue(_is_streamdeck_process_name("Stream Deck.exe"))
        self.assertTrue(_is_streamdeck_process_name("Elgato Stream Deck.exe"))
        self.assertFalse(_is_streamdeck_process_name("my-streamdeck-helper.exe"))

    def test_streamdeck_window_title_matching_is_limited(self) -> None:
        self.assertTrue(_is_streamdeck_window("", "Stream Deck"))
        self.assertTrue(_is_streamdeck_window("", "Stream Deck Settings"))
        self.assertFalse(_is_streamdeck_window("notepad.exe", "Notes Stream Deck"))

    def test_invalid_window_is_rejected(self) -> None:
        with self.assertRaises(FocusError):
            _focus_hwnd_with_api(999, FakeFocusApi(), verify_timeout=0)


if __name__ == "__main__":
    unittest.main()
