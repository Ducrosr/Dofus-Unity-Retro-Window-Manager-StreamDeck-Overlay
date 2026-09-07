from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


def search_words(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.casefold().replace("œ", "oe"))
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.findall(r"[^\W_]+", normalized)


@dataclass(frozen=True)
class SettingSearchEntry:
    label: str
    context: str
    tab: str
    target: object


def find_settings(entries: list[SettingSearchEntry], query: str) -> list[SettingSearchEntry]:
    words = search_words(query)
    if not words:
        return []
    matches = []
    for entry in entries:
        label = " ".join(search_words(entry.label))
        text = " ".join(search_words(entry.context)) + " " + label
        if all(word in text for word in words):
            matches.append((sum(word in label for word in words), entry))
    return [entry for _score, entry in sorted(matches, key=lambda item: -item[0])]
