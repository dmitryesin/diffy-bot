package com.solver.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

@ConfigurationProperties(prefix = "solver")
public record SolverProperties(
        @DefaultValue("100000") long maxIntegrationSteps,
        @DefaultValue("4") int maxConcurrentSolves,
        @DefaultValue("32") int maxQueuedSolves,
        @DefaultValue("5") int maxStoredApplicationsPerUser,
        @DefaultValue("14") int applicationRetentionDays,
        String internalApiKey
) {
}
