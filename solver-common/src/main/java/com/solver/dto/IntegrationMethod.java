package com.solver.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public enum IntegrationMethod {
    @JsonProperty("euler") EULER,
    @JsonProperty("midpoint") MIDPOINT,
    @JsonProperty("heun") HEUN,
    @JsonProperty("rungeKutta") RUNGE_KUTTA,
    @JsonProperty("dormandPrince") DORMAND_PRINCE
}
