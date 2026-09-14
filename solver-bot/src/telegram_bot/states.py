from __future__ import annotations

from enum import IntEnum


class ConversationState(IntEnum):
    MENU = 0
    EQUATION = 1
    INITIAL_X = 2
    INITIAL_Y = 3
    REACH_POINT = 4
    STEP_SIZE = 5


ACTIVE_SOLVE_STATES = frozenset(
    {
        ConversationState.EQUATION,
        ConversationState.INITIAL_X,
        ConversationState.INITIAL_Y,
        ConversationState.REACH_POINT,
        ConversationState.STEP_SIZE,
    }
)
