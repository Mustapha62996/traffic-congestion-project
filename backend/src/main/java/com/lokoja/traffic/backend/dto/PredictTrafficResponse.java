package com.lokoja.traffic.backend.dto;

import java.util.List;
import java.util.Map;

public record PredictTrafficResponse(
        Double predictedTrafficVolume,
        String congestionLevel,
        Map<String, Double> thresholds,
        List<String> explanation,
        Map<String, Object> normalizedInput
) {
}
