from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import Settings
from src.solver_client import SolverClient
from telegram.ext import ContextTypes

_DEPS_KEY = "deps"


@dataclass(slots=True)
class BotDeps:
    settings: Settings
    solver_client: SolverClient
    lang_texts: dict[str, Any]
    start_texts: dict[str, str]


def store_deps(bot_data: dict, deps: BotDeps) -> None:
    bot_data[_DEPS_KEY] = deps


def get_deps(context: ContextTypes.DEFAULT_TYPE) -> BotDeps:
    return context.bot_data[_DEPS_KEY]
