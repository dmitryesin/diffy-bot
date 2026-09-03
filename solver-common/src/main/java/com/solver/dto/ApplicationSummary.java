package com.solver.dto;

public record ApplicationSummary(
        int id,
        String parameters,
        String status,
        String createdAt,
        String lastUpdatedAt
) {
}
