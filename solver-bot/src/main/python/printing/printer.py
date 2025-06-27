def get_variable_name(i):
    superscripts = "⁰¹²³⁴⁵⁶⁷⁸⁹"

    if i == 0:
        return "y"
    if i < 4:
        return f"y{chr(39) * i}"
    else:
        return "y⁽" + "".join(superscripts[int(d)] for d in str(i)) + "⁾"


def print_solution(result, order, rounding):
    def format_value(value):
        formatted_value = f"{value:.{rounding}f}"
        if "." in formatted_value:
            formatted_value = formatted_value.rstrip("0")
            if formatted_value.endswith("."):
                formatted_value += "0"
        return formatted_value

    variable_names = [get_variable_name(i) for i in range(order)]
    values = [
        format_value(result[i]) if i < len(result) else "NaN"
        for i in range(1, order + 1)
    ]

    formatted_x = format_value(result[0])
    variables_str = ", ".join(
        f"{name}: {val}" for name, val in zip(variable_names, values)
    )

    return f"x: {formatted_x}, {variables_str}"
