package com.lokoja.traffic.backend.dto;

import java.util.List;
import java.util.Map;

public record InsightsResponse(
        Map<String, Object> datasetProfile,
        Map<String, Object> modelMetrics,
        List<Map<String, Object>> featureImportance,
        Map<String, Object> interpretation,
        Map<String, Double> congestionThresholds,
        List<Integer> peakHours,
        List<Map<String, Object>> hourlyTrends,
        List<Map<String, Object>> locationPatterns
) {
}
