from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from dwm.services.backup_history import (
    create_backup_snapshot,
    list_backup_snapshots,
    load_backup_snapshot,
)


class BackupHistoryTests(unittest.TestCase):
    def test_snapshots_are_listed_newest_first_and_keep_their_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = datetime(2026, 8, 25, 12, 0, 0)
            first = create_backup_snapshot(
                tmp,
                {"format": "dofus-window-manager-backup", "profiles": []},
                reason="manuel",
                app_version="2.20.0",
                now=base,
            )
            second = create_backup_snapshot(
                tmp,
                {"format": "dofus-window-manager-backup", "profiles": [1]},
                reason="avant import",
                app_version="2.20.0",
                now=base + timedelta(seconds=1),
            )
            snapshots = list_backup_snapshots(tmp)

        self.assertEqual([entry.path for entry in snapshots], [second.path, first.path])
        self.assertIn("avant import", snapshots[0].label)

    def test_retention_removes_only_oldest_managed_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            unrelated = directory / "keep-me.json"
            unrelated.write_text("{}", encoding="utf-8")
            base = datetime(2026, 8, 25, 12, 0, 0)
            for offset in range(4):
                create_backup_snapshot(
                    directory,
                    {"format": "dofus-window-manager-backup", "value": offset},
                    reason=f"point {offset}",
                    app_version="2.20.0",
                    keep=2,
                    now=base + timedelta(seconds=offset),
                )

            snapshots = list_backup_snapshots(directory)
            latest = load_backup_snapshot(snapshots[0])
            unrelated_preserved = unrelated.exists()

        self.assertEqual(len(snapshots), 2)
        self.assertEqual(latest["value"], 3)
        self.assertTrue(unrelated_preserved)
