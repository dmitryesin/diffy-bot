from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SolveParameters:
    user_id: int
    method: str
    order: int
    user_equation: str
    formatted_equation: str
    initial_x: str
    initial_y: list[str]
    reach_point: str
    step_size: str


@dataclass(slots=True)
class UserSettings:
    method: str
    rounding: str
    language: str
    hints: str
