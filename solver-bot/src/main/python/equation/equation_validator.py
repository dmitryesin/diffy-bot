import re
import json

from pathlib import Path

PY_DIR = Path(__file__).parent
functions_path = PY_DIR / "functions.json"

with open(functions_path, "r", encoding="utf-8") as f:
    MATH_FUNCTIONS = json.load(f)


def validate_symbols(equation):
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


def validate_parentheses(equation):
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

    if stack:
        return False
    return True
