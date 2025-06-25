package com.solver;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
public class ApplicationProcessingService {
    private static final Logger logger = LoggerFactory.getLogger(ApplicationProcessingService.class);

    private final SolverService solverService;
    private final DBService dbService;

    public ApplicationProcessingService(SolverService solverService, DBService dbService) {
        this.solverService = solverService;
        this.dbService = dbService;
    }

    public CompletableFuture<Void> processApplication(int applicationId, SolverRequest request) {
        logger.debug("Starting processing for applicationId: {}", applicationId);
        
        return dbService.updateApplicationStatus(applicationId, "in_progress")
            .thenCompose(v -> {
                logger.debug("Application {} status updated to in_progress, starting solver", applicationId);
                return solverService.solveEquation(request);
            })
            .thenCompose(solutionResponse -> {
                logger.debug("Solution computed for applicationId: {}, saving results", applicationId);
                return dbService.saveResults(applicationId, solutionResponse.toJson());
            })
            .thenCompose(v -> {
                logger.debug("Results saved for applicationId: {}, updating status to completed", applicationId);
                return dbService.updateApplicationStatus(applicationId, "completed");
            })
            .whenComplete((result, throwable) -> {
                if (throwable != null) {
                    logger.error("Error processing application {}: {}", applicationId, throwable.getMessage(), throwable);
                    dbService.updateApplicationStatus(applicationId, "error")
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
