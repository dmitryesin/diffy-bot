package com.solver.numeric;

import java.util.function.BiFunction;

public final class NumericalMethods {

    private NumericalMethods() {
    }

    public static double[] dormandPrince(BiFunction<Double, double[], double[]> f, double x_0, double[] y_0, double h) {
        double[] y_next = new double[y_0.length];
    
        double[] k1 = ArrayOperations.multiply(h, f.apply(x_0, y_0));
        double[] temp = ArrayOperations.add(y_0, ArrayOperations.multiply(1.0 / 5.0, k1));
        double[] k2 = ArrayOperations.multiply(h, f.apply(x_0 + h / 5.0, temp));
        temp = ArrayOperations.add(y_0, ArrayOperations.add(
                ArrayOperations.multiply(3.0 / 40.0, k1),
                ArrayOperations.multiply(9.0 / 40.0, k2)));
        double[] k3 = ArrayOperations.multiply(h, f.apply(x_0 + h * 3.0 / 10.0, temp));
        temp = ArrayOperations.add(y_0, ArrayOperations.add(
                ArrayOperations.add(ArrayOperations.multiply(44.0 / 45.0, k1),
                        ArrayOperations.multiply(-56.0 / 15.0, k2)),
                ArrayOperations.multiply(32.0 / 9.0, k3)));
        double[] k4 = ArrayOperations.multiply(h, f.apply(x_0 + h * 4.0 / 5.0, temp));
        temp = ArrayOperations.add(y_0, ArrayOperations.add(
                ArrayOperations.add(ArrayOperations.multiply(19372.0 / 6561.0, k1),
                        ArrayOperations.add(ArrayOperations.multiply(-25360.0 / 2187.0, k2),
                                ArrayOperations.multiply(64448.0 / 6561.0, k3))),
                ArrayOperations.multiply(-212.0 / 729.0, k4)));
        double[] k5 = ArrayOperations.multiply(h, f.apply(x_0 + h * 8.0 / 9.0, temp));
        temp = ArrayOperations.add(y_0, ArrayOperations.add(
                ArrayOperations.add(ArrayOperations.multiply(9017.0 / 3168.0, k1),
                        ArrayOperations.add(ArrayOperations.multiply(-355.0 / 33.0, k2),
                                ArrayOperations.add(ArrayOperations.multiply(46732.0 / 5247.0, k3),
                                        ArrayOperations.multiply(49.0 / 176.0, k4)))),
                ArrayOperations.multiply(-5103.0 / 18656.0, k5)));
        double[] k6 = ArrayOperations.multiply(h, f.apply(x_0 + h, temp));
    
        for (int i = 0; i < y_0.length; i++) {
            y_next[i] = y_0[i] + (35.0 / 384.0 * k1[i] + 500.0 / 1113.0 * k3[i]
                        + 125.0 / 192.0 * k4[i] - 2187.0 / 6784.0 * k5[i]
                        + 11.0 / 84.0 * k6[i]);
        }
    
        double[] result = new double[y_0.length + 1];
        result[0] = x_0 + h;
        System.arraycopy(y_next, 0, result, 1, y_0.length);
    
        return result;
    }    

    public static double[] rungeKutta(BiFunction<Double, double[], double[]> f, double x_0, double[] y_0, double h) {
        double[] y_next = new double[y_0.length];

        double[] k1 = ArrayOperations.multiply(h, f.apply(x_0, y_0));
        double[] temp = ArrayOperations.add(y_0, ArrayOperations.multiply(0.5, k1));
        double[] k2 = ArrayOperations.multiply(h, f.apply(x_0 + h / 2, temp));
        temp = ArrayOperations.add(y_0, ArrayOperations.multiply(0.5, k2));
        double[] k3 = ArrayOperations.multiply(h, f.apply(x_0 + h / 2, temp));
        temp = ArrayOperations.add(y_0, k3);
        double[] k4 = ArrayOperations.multiply(h, f.apply(x_0 + h, temp));

        for (int i = 0; i < y_0.length; i++) {
            y_next[i] = y_0[i] + (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / 6;
        }

        double[] result = new double[y_0.length + 1];
        result[0] = x_0 + h;
        System.arraycopy(y_next, 0, result, 1, y_0.length);

        return result;
    }

    public static double[] heun(BiFunction<Double, double[], double[]> f, double x_0, double[] y_0, double h) {
        double[] y_next = new double[y_0.length];

        double[] k1 = f.apply(x_0, y_0);
        double[] temp = new double[y_0.length];

        for (int i = 0; i < y_0.length; i++) {
            temp[i] = y_0[i] + h * k1[i];
        }

        double[] k2 = f.apply(x_0 + h, temp);

        for (int i = 0; i < y_0.length; i++) {
            y_next[i] = y_0[i] + (h / 2) * (k1[i] + k2[i]);
        }

        double[] result = new double[y_0.length + 1];
        result[0] = x_0 + h;
        System.arraycopy(y_next, 0, result, 1, y_0.length);

        return result;
    }

    public static double[] midpoint(BiFunction<Double, double[], double[]> f, double x_0, double[] y_0, double h) {
        double[] y_next = new double[y_0.length];

        double[] k1 = f.apply(x_0, y_0);
        double[] temp = new double[y_0.length];

        for (int i = 0; i < y_0.length; i++) {
            temp[i] = y_0[i] + (h / 2) * k1[i];
        }

        double[] k2 = f.apply(x_0 + h / 2, temp);

        for (int i = 0; i < y_0.length; i++) {
            y_next[i] = y_0[i] + h * k2[i];
        }

        double[] result = new double[y_0.length + 1];
        result[0] = x_0 + h;
        System.arraycopy(y_next, 0, result, 1, y_0.length);

        return result;
    }

    public static double[] euler(BiFunction<Double, double[], double[]> f, double x_0, double[] y_0, double h) {
        double[] y_next = new double[y_0.length];

        double[] k1 = f.apply(x_0, y_0);
        for (int i = 0; i < y_0.length; i++) {
            y_next[i] = y_0[i] + h * k1[i];
        }

        double[] result = new double[y_0.length + 1];
        result[0] = x_0 + h;
        System.arraycopy(y_next, 0, result, 1, y_0.length);

        return result;
    }
}