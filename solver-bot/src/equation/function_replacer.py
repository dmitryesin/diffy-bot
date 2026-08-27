import json
import re
from pathlib import Path

_FUNCTIONS_PATH = Path(__file__).parent / "functions.json"

with open(_FUNCTIONS_PATH, "r", encoding="utf-8") as f:
    MATH_FUNCTIONS = json.load(f)


def replace_math_functions(equation: str) -> str:
    for func, replacement in MATH_FUNCTIONS.items():
        if func in ["coth", "cth"]:
            equation = re.sub(rf"\b{func}\((.*?)\)", r"(cosh(\1) / sinh(\1))", equation)
        elif func in ["acot", "actg", "arccot", "arcctg"]:
            equation = re.sub(rf"\b{func}\((.*?)\)", r"(atan(1 / \1))", equation)
        else:
            equation = re.sub(rf"\b{func}\b", f"{replacement}", equation)

    return equation
