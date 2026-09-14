package com.solver.numeric;

import com.solver.exception.SolverException;
import net.objecthunter.exp4j.Expression;
import net.objecthunter.exp4j.ExpressionBuilder;

import java.util.function.BiFunction;
import java.util.regex.Pattern;

public final class OdeFunctionFactory {

    private static final Pattern INDEXED_VARIABLE = Pattern.compile("y\\[(\\d+)]");

    private OdeFunctionFactory() {
    }

    public static BiFunction<Double, double[], double[]> create(String equation, int order) {
        if (order < 1) {
            throw new IllegalArgumentException("Order must be at least 1");
        }

        Expression compiled = compile(equation, order);

        return (x, y) -> {
            double[] dydt = new double[order];
            System.arraycopy(y, 1, dydt, 0, order - 1);
            dydt[order - 1] = evaluate(compiled, equation, x, y);
            return dydt;
        };
    }

    private static Expression compile(String equation, int order) {
        String normalized = INDEXED_VARIABLE.matcher(equation).replaceAll("y$1");
        ExpressionBuilder builder = new ExpressionBuilder(normalized).variable("x");
        for (int i = 0; i < order; i++) {
            builder.variable("y" + i);
        }
        return builder.build();
    }

    private static double evaluate(Expression expression, String equation, double x, double[] y) {
        try {
            expression.setVariable("x", x);
            for (int i = 0; i < y.length; i++) {
                expression.setVariable("y" + i, y[i]);
            }

            double result = expression.evaluate();

            if (Double.isNaN(result)) {
                throw new SolverException("Result is NaN at x = " + x);
            }
            if (Double.isInfinite(result)) {
                throw new SolverException("Result is infinite (likely division by zero) at x = " + x);
            }
            return result;
        } catch (SolverException e) {
            throw e;
        } catch (ArithmeticException e) {
            String message = e.getMessage();
            if (message != null && message.contains("Division by zero")) {
                throw new SolverException("Division by zero occurred at x = " + x);
            }
            throw new SolverException("Arithmetic error in equation: " + equation, e);
        } catch (Exception e) {
            throw new SolverException("Error evaluating equation: " + equation, e);
        }
    }
}
