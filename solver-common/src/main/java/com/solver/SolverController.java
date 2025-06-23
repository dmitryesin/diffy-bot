package com.solver;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;

import java.util.concurrent.CompletableFuture;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/solver")
public class SolverController {
    private static final Logger logger = LoggerFactory.getLogger(SolverController.class);

    private final Main main;
    private final DBService dbService;

    public SolverController(Main main, DBService dbService) {
        this.main = main;
        this.dbService = dbService;
    }

    @PostMapping("/users/{userId}/settings")
    public CompletableFuture<ResponseEntity<String>> setUserSettings(
            @PathVariable("userId") Long userId,
            @RequestParam("method") String method,
            @RequestParam("rounding") Integer rounding,
            @RequestParam("language") String language,
            @RequestParam("hints") Boolean hints) {
        logger.debug("Setting user settings for userId: {}", userId);
        return dbService.setUserSettings(userId, method, rounding, language, hints)
                .thenApply(optionalResult -> optionalResult
                    .map(ResponseEntity::ok)
                    .orElseThrow(() -> new SolverException("Failed to update settings for userId: " + userId)));
    }

    @PostMapping("/users/{userId}/solve")
    public CompletableFuture<ResponseEntity<Integer>> solve(
            @PathVariable("userId") Long userId,
            @RequestBody SolverRequest request) {
        logger.debug("Received solve request with userId: {}", userId);
        return CompletableFuture.supplyAsync(() -> {
            final int applicationId;
            try {
                applicationId = dbService.createApplication(
                    request.toJson(),
                    "new", 
                    userId
                ).join();

                logger.debug("Created application with id: {} for userId: {}", applicationId, userId);

                CompletableFuture.runAsync(() -> {
                    try {
                        dbService.updateApplicationStatus(applicationId, "in_progress").join();

                        main.setMethod(request.getMethod());
                        main.setOrder(request.getOrder());
                        main.setUserEquation(request.getUserEquation());
                        main.setEquation(request.getFormattedEquation());
                        main.setInitialX(request.getInitialX());
                        main.setInitialY(request.getInitialY());
                        main.setReachPoint(request.getReachPoint());
                        main.setStepSize(request.getStepSize());

                        double[] solution = main.getSolution();
                        List<Double> xValues = main.getXValues();
                        List<double[]> yValues = main.getYValues();

                        SolutionResponse response = new SolutionResponse(solution, xValues, yValues);
                        dbService.saveResults(applicationId, response.toJson()).join();
                        dbService.updateApplicationStatus(applicationId, "completed").join();

                        logger.debug("Successfully solved problem for applicationId: {}", applicationId);
                    } catch (Exception e) {
                        logger.error("Error solving problem for applicationId: {}", applicationId, e);
                        try {
                            dbService.updateApplicationStatus(applicationId, "error").join();
                        } catch (Exception sqlException) {
                            logger.error("Failed to update application status to error", sqlException);
                        }
                    }
                });

                return ResponseEntity.ok(applicationId);
            } catch (Exception e) {
                logger.error("Error creating application for userId: {}", userId, e);
                throw new SolverException("Error creating application", e);
            }
        });
    }

    @GetMapping("/users/{userId}/settings")
    public CompletableFuture<ResponseEntity<String>> getUserSettings(@PathVariable("userId") Long userId) {
        logger.debug("Getting user settings for userId: {}", userId);
        return dbService.getUserSettings(userId)
                .thenApply(optionalSettings -> optionalSettings
                    .map(ResponseEntity::ok)
                    .orElseThrow(() -> new SolverException("User settings not found for userId: " + userId)));
    }

    @GetMapping("/users/{userId}/applications")
    public CompletableFuture<ResponseEntity<List<Map<String, Object>>>> getApplications(@PathVariable("userId") Long userId) {
        logger.debug("Getting applications list for userId: {}", userId);
        return dbService.getApplications(userId)
                .thenApply(applications -> {
                    if (applications.isEmpty()) {
                        throw new SolverException("Applications not found for userId: " + userId);
                    }
                    return ResponseEntity.ok(applications);
                });
    }

    @GetMapping("/applications/{applicationId}/status")
    public CompletableFuture<ResponseEntity<String>> getApplicationStatus(@PathVariable("applicationId") int applicationId) {
        logger.debug("Getting application status for id: {}", applicationId);
        return dbService.getApplicationStatus(applicationId)
                .thenApply(optionalStatus -> optionalStatus
                    .map(ResponseEntity::ok)
                    .orElseThrow(() -> new SolverException("Application status not found for applicationId: " + applicationId)));
    }

    @GetMapping("/applications/{applicationId}/results")
    public CompletableFuture<ResponseEntity<List<Map<String, Object>>>> getResults(@PathVariable("applicationId") Integer applicationId) {
        logger.debug("Getting results for applicationId: {}", applicationId);
        return dbService.getResults(applicationId)
                .thenApply(results -> {
                    if (results.isEmpty()) {
                        throw new SolverException("Results not found for applicationId: " + applicationId);
                    }
                    return ResponseEntity.ok(results);
                });
    }
}