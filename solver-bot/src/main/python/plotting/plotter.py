import io
import matplotlib.pyplot as plt

from printing.printer import get_variable_name


def plot_solution(x_values, y_values, order):
    plt.figure(figsize=(10, 6), dpi=200)
    plt.grid(True)

    variable_names = ["y"] + [get_variable_name(i) for i in range(1, order)]

    is_multivariable = isinstance(y_values[0], (list, tuple))

    if is_multivariable:
        for i, var_name in enumerate(variable_names):
            plt.plot(x_values, [y[i] for y in y_values], label=var_name)
    else:
        plt.plot(x_values, y_values, label=variable_names[0])

    plt.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close()
    buffer.seek(0)

    return buffer
