package com.lokoja.traffic.backend.dto;

public record BackendHealthResponse(
        String status,
        String service,
        String mlServiceBaseUrl
) {
}
