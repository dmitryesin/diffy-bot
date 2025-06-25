package com.solver;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.ArrayList;
import java.util.concurrent.CompletableFuture;
import java.util.function.BiFunction;

@Service
public class SolverService {
    private static final Logger logger = LoggerFactory.getLogger(SolverService.class);

    @Async("taskExecutor")
    public CompletableFuture<SolutionResponse> solveEquation(SolverRequest request) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                logger.debug("Starting equation solving with method: {}, order: {}", 
                    request.getMethod(), request.getOrder());

                BiFunction<Double, double[], double[]> equationFunction = 
                    CreateEquationFunction.create(request.getFormattedEquation(), request.getOrder());

                List<Double> xValues = new ArrayList<>();
                List<double[]> yValues = new ArrayList<>();

                double x = request.getInitialX();
                double[] y = request.getInitialY().clone();

                while (x < request.getReachPoint() - 1e-10) {
                    double[] result = switch (request.getMethod()) {
                        case "euler" -> NumericalMethods.euler(equationFunction, x, y, request.getStepSize());
                        case "midpoint" -> NumericalMethods.midpoint(equationFunction, x, y, request.getStepSize());
                        case "heun" -> NumericalMethods.heun(equationFunction, x, y, request.getStepSize());
                        case "rungeKutta" -> NumericalMethods.rungeKutta(equationFunction, x, y, request.getStepSize());
                        case "dormandPrince" -> NumericalMethods.dormandPrince(equationFunction, x, y, request.getStepSize());
                        default -> throw new IllegalArgumentException("Invalid method value: " + request.getMethod());
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

                logger.debug("Successfully completed equation solving with {} steps", xValues.size());
                return new SolutionResponse(finalSolution, xValues, yValues);

            } catch (Exception e) {
                logger.error("Error solving equation: {}", e.getMessage(), e);
                throw new SolverException("Error solving equation: " + e.getMessage(), e);
            }
        });
    }
}
