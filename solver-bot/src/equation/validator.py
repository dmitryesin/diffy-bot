import json
import re
from pathlib import Path

_FUNCTIONS_PATH = Path(__file__).parent / "functions.json"

with open(_FUNCTIONS_PATH, "r", encoding="utf-8") as f:
    MATH_FUNCTIONS = json.load(f)


def validate_symbols(equation: str) -> tuple[bool, str | None]:
    allowed_vars = {"x", "y", "X", "Y"}
    symbols = re.findall(r"[a-zA-Z]+|\d+|\S", equation)
    for symbol in symbols:
        if (
            symbol.isalpha()
            and symbol not in allowed_vars
            and symbol not in MATH_FUNCTIONS
        ):
            return False, symbol
    return True, None


def validate_parentheses(equation: str) -> bool:
    stack = []
    for i, char in enumerate(equation):
        if char == "(":
            stack.append(i)
        elif char == ")":
            if not stack:
                return False
            start_index = stack.pop()
            if start_index + 1 == i:
                return False

    return not stack
