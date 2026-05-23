import re

from backend.utils.helpers import normalize_text

MALAY_MARKERS = {
    "saya",
    "ingin",
    "pinjaman",
    "syarikat",
    "pendaftaran",
    "perniagaan",
    "cari",
    "semak",
    "pilih",
    "untuk",
}

ENGLISH_MARKERS = {
    "i want",
    "business",
    "search",
    "check",
    "find",
    "continue",
}


def _contains_marker(text, marker):
    return bool(re.search(rf"(?<!\\w){re.escape(marker)}(?!\\w)", text))


def detect_language(message):
    text = normalize_text(message or "")
    if not text:
        return "en"

    if any(_contains_marker(text, marker) for marker in MALAY_MARKERS):
        return "ms"

    if any(_contains_marker(text, marker) for marker in ENGLISH_MARKERS):
        return "en"

    return "en"
