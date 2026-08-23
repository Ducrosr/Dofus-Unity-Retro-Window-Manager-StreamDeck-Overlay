from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError

from dwm.services.update_checker import (
    MAX_RESPONSE_BYTES,
    OFFICIAL_RELEASE_URL,
    RELEASES_API_URL,
    UpdateCheckError,
    check_for_update,
    is_automatic_check_due,
    parse_release_version,
    select_latest_release,
    utc_now_iso,
)


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.closed = False

    def read(self, _size: int) -> bytes:
        return self.payload

    def close(self) -> None:
        self.closed = True


class UpdateCheckerTests(unittest.TestCase):
    def test_version_order_handles_prerelease_stages(self) -> None:
        alpha = parse_release_version("v2.19.0-alpha.2")
        beta = parse_release_version("2.19.0-beta.1")
        candidate = parse_release_version("v2.19.0-rc.1")
        stable = parse_release_version("v2.19.0")

        self.assertIsNotNone(alpha)
        self.assertLess(alpha, beta)
        self.assertLess(beta, candidate)
        self.assertLess(candidate, stable)
        self.assertIsNone(parse_release_version("release-2.19"))

    def test_select_latest_filters_drafts_and_optional_betas(self) -> None:
        releases = [
            {"tag_name": "v2.20.0-beta.2", "prerelease": True, "draft": False},
            {"tag_name": "v2.19.1", "prerelease": False, "draft": False},
            {"tag_name": "v9.0.0", "prerelease": False, "draft": True},
            {"tag_name": "latest", "prerelease": False, "draft": False},
        ]

        stable_selection = select_latest_release(releases, include_prereleases=False)
        beta_selection = select_latest_release(releases, include_prereleases=True)

        self.assertEqual(stable_selection[0].tag, "v2.19.1")
        self.assertEqual(beta_selection[0].tag, "v2.20.0-beta.2")

    def test_release_url_is_rebuilt_for_the_official_repository(self) -> None:
        selected = select_latest_release(
            [
                {
                    "tag_name": "v2.19.1",
                    "html_url": "https://example.test/malicious",
                    "draft": False,
                    "prerelease": False,
                }
            ],
            include_prereleases=True,
        )

        self.assertEqual(selected[0].url, f"{OFFICIAL_RELEASE_URL}/v2.19.1")

    def test_check_uses_official_api_and_detects_new_release(self) -> None:
        response = FakeResponse(
            json.dumps(
                [
                    {
                        "tag_name": "v2.19.0",
                        "name": "Version stable",
                        "draft": False,
                        "prerelease": False,
                    }
                ]
            ).encode("utf-8")
        )
        captured = {}

        def opener(request, *, timeout):
            captured["url"] = request.full_url
            captured["accept"] = request.get_header("Accept")
            captured["api_version"] = request.get_header("X-github-api-version")
            captured["timeout"] = timeout
            return response

        result = check_for_update(
            "v2.19.0-beta.1",
            include_prereleases=True,
            opener=opener,
        )

        self.assertTrue(result.update_available)
        self.assertEqual(result.latest_release.tag, "v2.19.0")
        self.assertEqual(captured["url"], RELEASES_API_URL)
        self.assertEqual(captured["accept"], "application/vnd.github+json")
        self.assertEqual(captured["api_version"], "2022-11-28")
        self.assertEqual(captured["timeout"], 5.0)
        self.assertTrue(response.closed)

    def test_github_rate_limit_has_a_clear_error(self) -> None:
        def opener(_request, *, timeout):
            raise HTTPError(RELEASES_API_URL, 403, "rate limit", {}, None)

        with self.assertRaisesRegex(UpdateCheckError, "limite temporaire"):
            check_for_update(
                "v2.19.0-beta.1",
                include_prereleases=True,
                opener=opener,
            )

    def test_oversized_response_is_rejected(self) -> None:
        def opener(_request, *, timeout):
            return FakeResponse(b"[" + b" " * MAX_RESPONSE_BYTES + b"]")

        with self.assertRaisesRegex(UpdateCheckError, "volumineuse"):
            check_for_update(
                "v2.19.0-beta.1",
                include_prereleases=True,
                opener=opener,
            )

    def test_automatic_check_is_due_once_per_day(self) -> None:
        now = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
        recent = utc_now_iso(now - timedelta(hours=23))
        old = utc_now_iso(now - timedelta(hours=25))

        self.assertFalse(is_automatic_check_due(recent, now=now))
        self.assertTrue(is_automatic_check_due(old, now=now))
        self.assertTrue(is_automatic_check_due("invalid", now=now))


if __name__ == "__main__":
    unittest.main()
