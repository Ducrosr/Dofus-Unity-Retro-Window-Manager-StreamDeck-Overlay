"""Persist an unfinished session while holding an OS lock.

No process names, window titles, or user identifiers are recorded.
"""
from __future__ import annotations

import os
from pathlib import Path

from ..storage.atomic import atomic_write_text


class SessionRecovery:
    def __init__(self, directory: Path):
        self.marker = directory / "unfinished-session"
        self.lock_path = directory / "session.lock"
        self._lock = None
        self.previous_interruption = False

    def begin(self) -> bool:
        if self._lock is not None:
            raise RuntimeError("Session tracking already started")
        handle = self.lock_path.open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0, 2)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            # Another instance may own the marker. Never inspect or remove it.
            return False
        self._lock = handle
        try:
            self.previous_interruption = self.marker.exists()
            atomic_write_text(self.marker, "unfinished\n")
        except OSError:
            self.close()
            raise
        return True

    def complete(self) -> None:
        if self._lock is not None:
            self.marker.unlink(missing_ok=True)

    def close(self) -> None:
        if self._lock is not None:
            self._lock.close()
            self._lock = None
