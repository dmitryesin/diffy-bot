from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_I18N_DIR = Path(__file__).parent
_LANGUAGES_PATH = _I18N_DIR / "languages.json"
_TEXTS_DIR = _I18N_DIR / "texts"

SUPPORTED_LANGUAGES = ("en", "ru", "zh")


def load_language_texts() -> dict[str, Any]:
    with open(_LANGUAGES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_start_texts() -> dict[str, str]:
    texts = {}
    for lang_code in SUPPORTED_LANGUAGES:
        file_path = _TEXTS_DIR / f"START_{lang_code.upper()}.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            texts[lang_code] = file.read()
    return texts
