from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class AppLogger:
    log_file: Path
    actions_file: Path

    def _write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(text)

    def info(self, msg: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write(self.log_file, f"[{ts}] [INFO] {msg}\n")

    def warn(self, msg: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write(self.log_file, f"[{ts}] [WARN] {msg}\n")

    def error(self, msg: str, exc: Optional[BaseException] = None) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write(self.log_file, f"[{ts}] [ERROR] {msg}\n")
        if exc is not None:
            self._write(self.log_file, "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))

    def action(self, msg: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write(self.actions_file, f"[{ts}] {msg}\n")


def install_excepthook(logger: AppLogger) -> None:
    """Logs unhandled exceptions to the main log file."""

    def _hook(exc_type, exc_value, exc_tb):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger._write(logger.log_file, f"--- Crash {ts} ---\n")
        logger._write(logger.log_file, "".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        logger._write(logger.log_file, "\n")

    import sys

    sys.excepthook = _hook
