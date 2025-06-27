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

    private final ApplicationProcessingService applicationProcessingService;
    private final DBService dbService;

    public SolverController(ApplicationProcessingService applicationProcessingService, DBService dbService) {
        this.applicationProcessingService = applicationProcessingService;
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
        
        return dbService.createApplication(request.toJson(), "new", userId)
            .thenCompose(applicationId -> {
                logger.debug("Created application with id: {} for userId: {}", applicationId, userId);
                
                processEquationSolvingAsync(applicationId, request);
                
                return CompletableFuture.completedFuture(ResponseEntity.ok(applicationId));
            })
            .exceptionally(e -> {
                logger.error("Error creating application for userId: {}", userId, e);
                throw new SolverException("Error creating application", e);
            });
    }

    private void processEquationSolvingAsync(int applicationId, SolverRequest request) {
        applicationProcessingService.processApplication(applicationId, request);
    }

    @GetMapping("/users/{userId}/settings")
    public CompletableFuture<ResponseEntity<String>> getUserSettings(@PathVariable("userId") Long userId) {
        logger.debug("Getting user settings for userId: {}", userId);
        return dbService.getUserSettings(userId)
                .thenApply(optionalSettings -> optionalSettings
                    .map(ResponseEntity::ok)
                    .orElseThrow(() -> new NotFoundException("User settings not found for userId: " + userId)));
    }

    @GetMapping("/users/{userId}/applications")
    public CompletableFuture<ResponseEntity<List<Map<String, Object>>>> getApplications(@PathVariable("userId") Long userId) {
        logger.debug("Getting applications list for userId: {}", userId);
        return dbService.getApplications(userId)
                .thenApply(applications -> {
                    if (applications.isEmpty()) {
                        throw new NotFoundException("Applications not found for userId: " + userId);
                    }
                    return ResponseEntity.ok(applications);
                });
    }

    @GetMapping("/applications/{applicationId}/status")
    public CompletableFuture<ResponseEntity<String>> getApplicationStatus(@PathVariable("applicationId") int applicationId) {
        logger.debug("Getting application status for id: {}", applicationId);
        
        if (applicationId <= 0) {
            throw new NotFoundException("Invalid applicationId: " + applicationId);
        }
        
        return dbService.getApplicationStatus(applicationId)
                .thenApply(optionalStatus -> optionalStatus
                    .map(ResponseEntity::ok)
                    .orElseThrow(() -> new NotFoundException("Application not found for applicationId: " + applicationId)));
    }

    @GetMapping("/applications/{applicationId}/results")
    public CompletableFuture<ResponseEntity<List<Map<String, Object>>>> getResults(@PathVariable("applicationId") int applicationId) {
        logger.debug("Getting results for applicationId: {}", applicationId);
        
        if (applicationId <= 0) {
            throw new NotFoundException("Invalid applicationId: " + applicationId);
        }
        
        return dbService.getResults(applicationId)
                .thenApply(results -> {
                    if (results.isEmpty()) {
                        throw new NotFoundException("Results not found for applicationId: " + applicationId);
                    }
                    return ResponseEntity.ok(results);
                });
    }
}