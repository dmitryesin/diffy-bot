package com.solver.dto;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.List;

public record SolutionResponse(
        double[] solution,
        List<Double> xValues,
        List<double[]> yValues
) {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    public String toJson() {
        try {
            return OBJECT_MAPPER.writeValueAsString(this);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Error converting SolutionResponse to JSON", e);
        }
    }
}
