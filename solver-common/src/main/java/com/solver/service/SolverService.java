package com.solver.service;

import com.solver.config.SolverProperties;
import com.solver.dto.IntegrationMethod;
import com.solver.dto.SolutionResponse;
import com.solver.dto.SolverRequest;
import com.solver.exception.SolverException;
import com.solver.numeric.NumericalMethods;
import com.solver.numeric.OdeFunctionFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.function.BiFunction;

@Service
public class SolverService {
    private static final Logger logger = LoggerFactory.getLogger(SolverService.class);
    private static final double CONVERGENCE_EPSILON = 1e-10;

    private final SolverProperties properties;

    public SolverService(SolverProperties properties) {
        this.properties = properties;
    }

    @Async("taskExecutor")
    public CompletableFuture<SolutionResponse> solveEquation(SolverRequest request) {
        logger.debug("Starting equation solving with method: {}, order: {}",
                request.method(), request.order());

        validate(request);

        BiFunction<Double, double[], double[]> equationFunction =
                OdeFunctionFactory.create(request.formattedEquation(), request.order());

        List<Double> xValues = new ArrayList<>();
        List<double[]> yValues = new ArrayList<>();

        double x = request.initialX();
        double[] y = request.initialY().clone();

        try {
            while (x < request.reachPoint() - CONVERGENCE_EPSILON) {
                double[] result = step(equationFunction, request.method(), x, y, request.stepSize());

                x = result[0];
                y = new double[result.length - 1];
                System.arraycopy(result, 1, y, 0, result.length - 1);

                xValues.add(x);
                yValues.add(y.clone());
            }
        } catch (SolverException e) {
            throw e;
        } catch (Exception e) {
            logger.error("Error solving equation: {}", e.getMessage(), e);
            throw new SolverException("Error solving equation: " + e.getMessage(), e);
        }

        double[] finalSolution = new double[1 + y.length];
        finalSolution[0] = x;
        System.arraycopy(y, 0, finalSolution, 1, y.length);

        logger.debug("Successfully completed equation solving with {} steps", xValues.size());
        return CompletableFuture.completedFuture(new SolutionResponse(finalSolution, xValues, yValues));
    }

    private static double[] step(
            BiFunction<Double, double[], double[]> f,
            IntegrationMethod method,
            double x, double[] y, double h) {
        return switch (method) {
            case EULER -> NumericalMethods.euler(f, x, y, h);
            case MIDPOINT -> NumericalMethods.midpoint(f, x, y, h);
            case HEUN -> NumericalMethods.heun(f, x, y, h);
            case RUNGE_KUTTA -> NumericalMethods.rungeKutta(f, x, y, h);
            case DORMAND_PRINCE -> NumericalMethods.dormandPrince(f, x, y, h);
        };
    }

    private void validate(SolverRequest request) {
        if (request.initialY().length != request.order()) {
            throw new IllegalArgumentException(
                    "initialY length must match the equation order (" + request.order() + ")");
        }
        if (request.reachPoint() <= request.initialX()) {
            throw new IllegalArgumentException("reachPoint must be greater than initialX");
        }

        long steps = (long) Math.ceil((request.reachPoint() - request.initialX()) / request.stepSize()) + 1;
        if (steps > properties.maxIntegrationSteps()) {
            throw new IllegalArgumentException(
                    "Requested range/stepSize would require too many steps (" + steps + ")");
        }
    }
}
