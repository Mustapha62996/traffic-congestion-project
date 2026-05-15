package com.lokoja.traffic.backend.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

public record TrainModelRequest(
        @DecimalMin("0.05") @DecimalMax("0.5") Double testSize,
        Integer randomState,
        @Min(100) @Max(1000) Integer nEstimators
) {
    public Double resolvedTestSize() {
        return testSize == null ? 0.2 : testSize;
    }

    public Integer resolvedRandomState() {
        return randomState == null ? 42 : randomState;
    }

    public Integer resolvedNEstimators() {
        return nEstimators == null ? 300 : nEstimators;
    }
}
