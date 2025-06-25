package com.solver;

import java.util.List;
import java.util.ArrayList;
import java.util.function.BiFunction;

public class Main {
    private int order;
    private BiFunction<Double, double[], double[]> equationFunction;
    private double initialX;
    private double[] initialY;
    private double reachPoint;
    private double stepSize;
    private String method;

    private List<Double> xValues;
    private List<double[]> yValues;

    public void setMethod(String method) {
        this.method = method;
    }

    public void setOrder(int order) {
        this.order = order;
    }

    public void setUserEquation(String userEquation) {}

    public void setEquation(String equation) {
        this.equationFunction = CreateEquationFunction.create(equation, this.order);
    }

    public void setInitialX(double initialX) {
        this.initialX = initialX;
    }

    public void setInitialY(double... initialY) {
        this.initialY = initialY;
    }

    public void setReachPoint(double reachPoint) {
        this.reachPoint = reachPoint;
    }

    public void setStepSize(double stepSize) {
        this.stepSize = stepSize;
    }

    public double[] getSolution() {
        xValues = new ArrayList<>();
        yValues = new ArrayList<>();

        double x = initialX;
        double[] y = initialY.clone();

        while (x < reachPoint - 1e-10) {
            double[] result = switch (method) {
                case "euler" -> NumericalMethods.euler(equationFunction, x, y, stepSize);
                case "midpoint" -> NumericalMethods.midpoint(equationFunction, x, y, stepSize);
                case "heun" -> NumericalMethods.heun(equationFunction, x, y, stepSize);
                case "rungeKutta" -> NumericalMethods.rungeKutta(equationFunction, x, y, stepSize);
                case "dormandPrince" -> NumericalMethods.dormandPrince(equationFunction, x, y, stepSize);
                default -> throw new IllegalArgumentException("Invalid method value: " + method);
            };
            x = result[0];
            y = new double[result.length - 1];
            System.arraycopy(result, 1, y, 0, result.length - 1);

            xValues.add(x);
            yValues.add(y.clone());
        }

        double[] finalSolution = new double[1 + y.length];
        finalSolution[0] = x;
        System.arraycopy(y, 0, finalSolution, 1, y.length);

        return finalSolution;
    }

    public List<Double> getXValues() { return xValues; }

    public List<double[]> getYValues() { return yValues; }
}