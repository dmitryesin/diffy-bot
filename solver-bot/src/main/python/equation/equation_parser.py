import re
import sympy as sp

from equation.function_replacer import replace_math_functions


def get_equation_order(eq):
    derivatives = list(eq.lhs.atoms(sp.Derivative))
    if not derivatives:
        return 0

    return max(d.derivative_count for d in derivatives)


def convert_to_first_order(eq, y, x):
    order = get_equation_order(eq)
    if order == 0:
        return eq, order

    y_vars = [sp.Symbol(f"y[{i}]") for i in range(order)]
    subs_dict = {y.diff(x, i): y_vars[i] for i in range(order)}
    subs_dict[y] = y_vars[0]

    last_derivative = y.diff(x, order)
    last_eq = sp.solve(eq, last_derivative)[0].subs(subs_dict)
    last_equation = sp.Eq(sp.Symbol(f"y[{order - 1}]").diff(x), last_eq)

    return last_equation, order


def parse_equation(eq):
    x = sp.Symbol("x")
    y = sp.Function("y")(x)

    eq = eq.replace(" ", "").replace("`", "'").replace("’", "'")
    eq = re.sub(r"y\^\((\d+)\)", lambda m: "y" + "'" * int(m.group(1)), eq)
    eq = re.sub(r"y'{3,}", lambda m: f"Derivative(y, x, {len(m.group(0)) - 1})", eq)
    eq = re.sub(r"y''", "Derivative(y, x, 2)", eq)
    eq = re.sub(r"y'", "Derivative(y, x)", eq)

    if "=" in eq:
        lhs_str, rhs_str = eq.split("=")
    else:
        lhs_str, rhs_str = eq, "0"

    lhs_expr = sp.sympify(lhs_str, locals={"y": y, "x": x, "Derivative": sp.Derivative})
    rhs_expr = sp.sympify(rhs_str, locals={"y": y, "x": x})

    return sp.Eq(lhs_expr, rhs_expr), y, x


def format_equation(eq):
    try:
        equation, y, x = parse_equation(eq.lower())
        last_equation, order = convert_to_first_order(equation, y, x)
        rhs_str = str(last_equation.rhs).replace("**", "^")
        rhs_str = replace_math_functions(rhs_str)
        return rhs_str, order
    except (sp.SympifyError, TypeError, AttributeError, ValueError):
        return None, None
