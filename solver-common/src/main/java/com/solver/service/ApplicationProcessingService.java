package com.solver.service;

import com.solver.dto.SolverRequest;
import com.solver.persistence.ApplicationRepository;
import com.solver.persistence.ResultRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
public class ApplicationProcessingService {
    private static final Logger logger = LoggerFactory.getLogger(ApplicationProcessingService.class);

    private static final String STATUS_IN_PROGRESS = "in_progress";
    private static final String STATUS_COMPLETED = "completed";
    private static final String STATUS_ERROR = "error";

    private final SolverService solverService;
    private final ApplicationRepository applicationRepository;
    private final ResultRepository resultRepository;

    public ApplicationProcessingService(
            SolverService solverService,
            ApplicationRepository applicationRepository,
            ResultRepository resultRepository) {
        this.solverService = solverService;
        this.applicationRepository = applicationRepository;
        this.resultRepository = resultRepository;
    }

    public CompletableFuture<Void> processApplication(int applicationId, SolverRequest request) {
        logger.debug("Starting processing for applicationId: {}", applicationId);

        return applicationRepository.updateApplicationStatus(applicationId, STATUS_IN_PROGRESS)
            .thenCompose(v -> {
                logger.debug("Application {} status updated to in_progress, starting solver", applicationId);
                return solverService.solveEquation(request);
            })
            .thenCompose(solutionResponse -> {
                logger.debug("Solution computed for applicationId: {}, saving results", applicationId);
                return resultRepository.saveResults(applicationId, solutionResponse.toJson());
            })
            .thenCompose(v -> {
                logger.debug("Results saved for applicationId: {}, updating status to completed", applicationId);
                return applicationRepository.updateApplicationStatus(applicationId, STATUS_COMPLETED);
            })
            .whenComplete((result, throwable) -> {
                if (throwable != null) {
                    logger.error("Error processing application {}: {}", applicationId, throwable.getMessage(), throwable);
                    applicationRepository.updateApplicationStatus(applicationId, STATUS_ERROR)
                        .exceptionally(sqlException -> {
                            logger.error("Failed to update application status to error for applicationId: {}",
                                applicationId, sqlException);
                            return null;
                        });
                } else {
                    logger.info("Successfully completed processing for applicationId: {}", applicationId);
                }
            });
    }
}
