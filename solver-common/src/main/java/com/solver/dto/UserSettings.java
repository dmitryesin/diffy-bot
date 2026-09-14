package com.solver.dto;

public record UserSettings(
        String method,
        String rounding,
        String language,
        String hints
) {
}
