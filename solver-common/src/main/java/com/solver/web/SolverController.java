package com.solver.web;

import com.solver.dto.ApplicationSummary;
import com.solver.dto.ResultEntry;
import com.solver.dto.SolverRequest;
import com.solver.dto.UserSettings;
import com.solver.exception.NotFoundException;
import com.solver.exception.SolverException;
import com.solver.persistence.ApplicationRepository;
import com.solver.persistence.ResultRepository;
import com.solver.persistence.UserSettingsRepository;
import com.solver.service.ApplicationProcessingService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/api/solver")
public class SolverController {
    private static final Logger logger = LoggerFactory.getLogger(SolverController.class);

    private final ApplicationProcessingService applicationProcessingService;
    private final ApplicationRepository applicationRepository;
    private final ResultRepository resultRepository;
    private final UserSettingsRepository userSettingsRepository;

    public SolverController(
            ApplicationProcessingService applicationProcessingService,
            ApplicationRepository applicationRepository,
            ResultRepository resultRepository,
            UserSettingsRepository userSettingsRepository) {
        this.applicationProcessingService = applicationProcessingService;
        this.applicationRepository = applicationRepository;
        this.resultRepository = resultRepository;
        this.userSettingsRepository = userSettingsRepository;
    }

    @PostMapping("/users/{userId}/settings")
    public CompletableFuture<ResponseEntity<UserSettings>> setUserSettings(
            @PathVariable("userId") Long userId,
            @RequestParam("method") String method,
            @RequestParam("rounding") String rounding,
            @RequestParam("language") String language,
            @RequestParam("hints") String hints) {
        logger.debug("Setting user settings for userId: {}", userId);
        UserSettings settings = new UserSettings(method, rounding, language, hints);
        return userSettingsRepository.setUserSettings(userId, settings)
                .thenApply(saved -> {
                    if (!saved) {
                        throw new SolverException("Failed to update settings for userId: " + userId);
                    }
                    return ResponseEntity.ok(settings);
                });
    }

    @GetMapping("/users/{userId}/settings")
    public CompletableFuture<ResponseEntity<UserSettings>> getUserSettings(@PathVariable("userId") Long userId) {
        logger.debug("Getting user settings for userId: {}", userId);
        return userSettingsRepository.getUserSettings(userId)
                .thenApply(optionalSettings -> optionalSettings
                    .map(ResponseEntity::ok)
                    .orElseThrow(() -> new NotFoundException("User settings not found for userId: " + userId)));
    }

    @PostMapping("/users/{userId}/solve")
    public CompletableFuture<ResponseEntity<Integer>> solve(
            @PathVariable("userId") Long userId,
            @Valid @RequestBody SolverRequest request) {
        logger.debug("Received solve request with userId: {}", userId);

        return applicationRepository.createApplication(request.toJson(), "new", userId)
            .thenApply(applicationId -> {
                logger.debug("Created application with id: {} for userId: {}", applicationId, userId);

                applicationProcessingService.processApplication(applicationId, request);

                return ResponseEntity.ok(applicationId);
            })
            .exceptionally(e -> {
                logger.error("Error creating application for userId: {}", userId, e);
                throw new SolverException("Error creating application", e);
            });
    }

    @GetMapping("/users/{userId}/applications")
    public CompletableFuture<ResponseEntity<List<ApplicationSummary>>> getApplications(@PathVariable("userId") Long userId) {
        logger.debug("Getting applications list for userId: {}", userId);
        return applicationRepository.getApplications(userId)
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

        return applicationRepository.getApplicationStatus(applicationId)
                .thenApply(optionalStatus -> optionalStatus
                    .map(ResponseEntity::ok)
                    .orElseThrow(() -> new NotFoundException("Application not found for applicationId: " + applicationId)));
    }

    @GetMapping("/applications/{applicationId}/results")
    public CompletableFuture<ResponseEntity<List<ResultEntry>>> getResults(@PathVariable("applicationId") int applicationId) {
        logger.debug("Getting results for applicationId: {}", applicationId);

        if (applicationId <= 0) {
            throw new NotFoundException("Invalid applicationId: " + applicationId);
        }

        return resultRepository.getResults(applicationId)
                .thenApply(results -> {
                    if (results.isEmpty()) {
                        throw new NotFoundException("Results not found for applicationId: " + applicationId);
                    }
                    return ResponseEntity.ok(results);
                });
    }
}
