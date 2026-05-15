package com.lokoja.traffic.backend.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record PredictTrafficRequest(
        @NotNull @Min(0) @Max(23) Integer hour,
        @NotNull @Min(0) @Max(6) Integer dayOfWeek,
        @NotBlank String location,
        @NotBlank String weather,
        @NotNull @Min(1) @Max(3) Integer roadCondition,
        String roadType,
        String vehicleMix,
        @Min(0) @Max(1) Integer nearCommercialHub,
        @Min(0) @Max(1) Integer isWeekend
) {
}
