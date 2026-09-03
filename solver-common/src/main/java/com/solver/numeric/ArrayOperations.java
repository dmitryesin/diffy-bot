package com.solver.numeric;

public final class ArrayOperations {

    private ArrayOperations() {
    }

    public static double[] multiply(double scalar, double[] array) {
        double[] result = new double[array.length];
        for (int i = 0; i < array.length; i++) {
            result[i] = scalar * array[i];
        }
        return result;
    }

    public static double[] add(double[] array1, double[] array2) {
        double[] result = new double[array1.length];
        for (int i = 0; i < array1.length; i++) {
            result[i] = array1[i] + array2[i];
        }
        return result;
    }
}