package com.solver.dto;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record SolverRequest(
        @NotNull IntegrationMethod method,
        @Positive int order,
        @NotBlank String userEquation,
        @NotBlank String formattedEquation,
        double initialX,
        @NotEmpty double[] initialY,
        double reachPoint,
        @Positive double stepSize
) {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    public String toJson() {
        try {
            return OBJECT_MAPPER.writeValueAsString(this);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Error converting SolverRequest to JSON", e);
        }
    }
}
