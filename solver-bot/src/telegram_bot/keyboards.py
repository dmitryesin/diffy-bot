from __future__ import annotations

from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def solution_markup(language: str, lang_texts: dict[str, Any]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    lang_texts[language]["solve_over"], callback_data="solve"
                )
            ],
            [InlineKeyboardButton(lang_texts[language]["menu"], callback_data="menu")],
        ]
    )
