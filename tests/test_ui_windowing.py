from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from dwm.services.monitor_layout import Monitor

from dwm.ui_windowing import (
    _clamp_geometry_to_work_area,
    center_window_on_parent,
    centered_position,
    install_combobox_wheel_guard,
)


class _FakeWidget:
    def __init__(
        self,
        *,
        x=0,
        y=0,
        width=100,
        height=100,
        req_width=None,
        req_height=None,
        visible=True,
        screen_width=1920,
        screen_height=1080,
    ):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._req_width = req_width if req_width is not None else width
        self._req_height = req_height if req_height is not None else height
        self._visible = visible
        self._screen_width = screen_width
        self._screen_height = screen_height
        self.geometry_calls: list[str] = []

    def update_idletasks(self):
        return None

    def state(self):
        return "normal" if self._visible else "withdrawn"

    def winfo_viewable(self):
        return int(self._visible)

    def winfo_rootx(self):
        return self._x

    def winfo_rooty(self):
        return self._y

    def winfo_width(self):
        return self._width

    def winfo_height(self):
        return self._height

    def winfo_reqwidth(self):
        return self._req_width

    def winfo_reqheight(self):
        return self._req_height

    def winfo_screenwidth(self):
        return self._screen_width

    def winfo_screenheight(self):
        return self._screen_height

    def geometry(self, value):
        self.geometry_calls.append(value)


class WindowPlacementTests(unittest.TestCase):
    def test_centered_position_uses_parent_rectangle(self):
        self.assertEqual(
            centered_position(100, 200, 1000, 700, 400, 300),
            (400, 400),
        )

    def test_dialog_centers_over_visible_parent(self):
        parent = _FakeWidget(x=200, y=120, width=1000, height=700)
        child = _FakeWidget(width=400, height=300)

        center_window_on_parent(child, parent)

        self.assertEqual(child.geometry_calls, ["400x300+500+320"])

    def test_hidden_parent_falls_back_to_screen_center(self):
        parent = _FakeWidget(visible=False)
        child = _FakeWidget(
            width=400,
            height=300,
            screen_width=1920,
            screen_height=1080,
        )

        with patch(
            "dwm.ui_windowing.list_monitors",
            return_value=(Monitor("primary", (0, 0, 1920, 1080), True),),
        ):
            center_window_on_parent(child, parent)

        self.assertEqual(child.geometry_calls, ["400x300+760+390"])


    def test_large_dialog_is_clamped_inside_work_area(self):
        self.assertEqual(
            _clamp_geometry_to_work_area(
                1800,
                900,
                900,
                800,
                (0, 0, 1920, 1040),
                margin=24,
            ),
            (996, 216, 900, 800),
        )

    def test_oversized_dialog_is_reduced_to_work_area(self):
        self.assertEqual(
            _clamp_geometry_to_work_area(
                -500,
                -500,
                2500,
                1500,
                (0, 0, 1920, 1040),
                margin=24,
            ),
            (24, 24, 1872, 992),
        )


class ComboboxWheelGuardTests(unittest.TestCase):
    def test_guard_replaces_combobox_and_spinbox_wheel_bindings_without_break(self):
        root = Mock()

        install_combobox_wheel_guard(root)

        bindings = [
            (call.args[0], call.args[1])
            for call in root.bind_class.call_args_list
        ]
        for widget_class in ("TCombobox", "TSpinbox"):
            self.assertIn((widget_class, "<MouseWheel>"), bindings)
            self.assertIn((widget_class, "<Button-4>"), bindings)
            self.assertIn((widget_class, "<Button-5>"), bindings)

        mousewheel_call = next(
            call
            for call in root.bind_class.call_args_list
            if call.args[0] == "TSpinbox" and call.args[1] == "<MouseWheel>"
        )
        callback = mousewheel_call.args[2]
        self.assertIsNone(callback(Mock()))


if __name__ == "__main__":
    unittest.main()
