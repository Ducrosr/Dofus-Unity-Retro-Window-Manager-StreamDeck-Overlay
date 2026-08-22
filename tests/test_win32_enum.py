from __future__ import annotations

import ctypes
import types
import unittest
from unittest.mock import patch

from dwm.services import win32_enum


class Win32EnumerationTests(unittest.TestCase):
    def test_callback_type_uses_ctypes_winfunctype(self) -> None:
        calls = []

        fake_ctypes = types.SimpleNamespace(
            WINFUNCTYPE=lambda *args: calls.append(args) or "callback-type",
        )
        fake_wintypes = types.SimpleNamespace(BOOL="BOOL", HWND="HWND", LPARAM="LPARAM")

        result = win32_enum._make_wndenumproc(fake_ctypes, fake_wintypes)

        self.assertEqual(result, "callback-type")
        self.assertEqual(calls, [("BOOL", "HWND", "LPARAM")])

    def test_enumeration_filters_class_and_visibility(self) -> None:
        classes = {101: "UnityWndClass", 102: "OtherClass", 103: "UnityWndClass"}
        titles = {101: "Korra - Dofus", 102: "Navigateur", 103: "Fenêtre cachée"}
        visible = {101: True, 102: True, 103: False}

        def callback_type(function):
            return function

        def enum_windows(callback, lparam):
            for hwnd in classes:
                callback(hwnd, lparam)
            return True

        def get_class_name(hwnd, buffer, size):
            buffer.value = classes[hwnd]
            return len(buffer.value)

        def get_title(hwnd, buffer, size):
            buffer.value = titles[hwnd]
            return len(buffer.value)

        backend = (
            ctypes,
            types.SimpleNamespace(),
            callback_type,
            enum_windows,
            get_class_name,
            lambda hwnd: len(titles[hwnd]),
            get_title,
            lambda hwnd: visible[hwnd],
            lambda hwnd: True,
        )

        with patch.object(win32_enum, "_load_win32", return_value=backend):
            result = win32_enum.enum_top_level_windows("UnityWndClass", visible_only=True)

        self.assertEqual(result, [(101, "Korra - Dofus")])
        self.assertEqual(win32_enum.get_last_enum_error(), "")

    def test_enumeration_error_is_exposed(self) -> None:
        with patch.object(win32_enum, "_load_win32", side_effect=AttributeError("callback absent")):
            result = win32_enum.enum_top_level_windows("UnityWndClass")

        self.assertEqual(result, [])
        self.assertIn("callback absent", win32_enum.get_last_enum_error())


if __name__ == "__main__":
    unittest.main()
