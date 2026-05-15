package com.lokoja.traffic.backend.dto;

import java.util.Map;

public record TrainModelResponse(
        String status,
        Map<String, Object> metrics
) {
}
