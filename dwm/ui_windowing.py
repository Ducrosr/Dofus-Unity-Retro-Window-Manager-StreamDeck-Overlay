from __future__ import annotations


def centered_position(
    parent_x: int,
    parent_y: int,
    parent_width: int,
    parent_height: int,
    child_width: int,
    child_height: int,
) -> tuple[int, int]:
    return (
        int(parent_x + (parent_width - child_width) / 2),
        int(parent_y + (parent_height - child_height) / 2),
    )


def _widget_is_visible(widget) -> bool:
    try:
        state = str(widget.state())
        if state in {"withdrawn", "iconic"}:
            return False
    except Exception:
        pass
    try:
        return bool(widget.winfo_viewable())
    except Exception:
        return False


def center_window_on_parent(window, parent=None) -> None:
    """Center a conventional dialog over its visible parent.

    If the parent is hidden, center on the current Tk screen instead. Overlay,
    popup and compact windows should not use this helper because their position
    is part of their functionality.
    """
    try:
        window.update_idletasks()
        child_width = max(int(window.winfo_width()), int(window.winfo_reqwidth()))
        child_height = max(int(window.winfo_height()), int(window.winfo_reqheight()))

        if parent is not None and _widget_is_visible(parent):
            parent.update_idletasks()
            x, y = centered_position(
                int(parent.winfo_rootx()),
                int(parent.winfo_rooty()),
                max(1, int(parent.winfo_width())),
                max(1, int(parent.winfo_height())),
                child_width,
                child_height,
            )
        else:
            x, y = centered_position(
                0,
                0,
                int(window.winfo_screenwidth()),
                int(window.winfo_screenheight()),
                child_width,
                child_height,
            )

        # Position-only geometry preserves a width/height already chosen by the
        # caller while letting Tk place the window on the same desktop as DWM.
        window.geometry(f"+{x}+{y}")
    except Exception:
        return


def schedule_center_window(window, parent=None) -> None:
    """Center after Tk has computed the dialog's requested dimensions."""
    try:
        window.after_idle(lambda: center_window_on_parent(window, parent))
    except Exception:
        center_window_on_parent(window, parent)


def install_combobox_wheel_guard(root) -> None:
    """Disable closed Combobox value changes caused by mouse-wheel scrolling.

    The replacement class binding deliberately returns None: the event may keep
    propagating to the containing window/canvas, so normal page scrolling still
    works. An opened Combobox drop-down uses its listbox and remains scrollable.
    """

    def ignore_selection_change(_event):
        return None

    try:
        root.bind_class("TCombobox", "<MouseWheel>", ignore_selection_change)
    except Exception:
        pass
    # Kept for completeness on Tk builds that report wheel events this way.
    for sequence in ("<Button-4>", "<Button-5>"):
        try:
            root.bind_class("TCombobox", sequence, ignore_selection_change)
        except Exception:
            pass
