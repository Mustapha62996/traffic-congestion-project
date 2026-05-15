package com.lokoja.traffic.backend.controller;

import com.lokoja.traffic.backend.config.MlServiceProperties;
import com.lokoja.traffic.backend.dto.BackendHealthResponse;
import com.lokoja.traffic.backend.dto.InsightsResponse;
import com.lokoja.traffic.backend.dto.PredictTrafficRequest;
import com.lokoja.traffic.backend.dto.PredictTrafficResponse;
import com.lokoja.traffic.backend.dto.TrainModelRequest;
import com.lokoja.traffic.backend.dto.TrainModelResponse;
import com.lokoja.traffic.backend.service.TrafficPredictionService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class TrafficController {

    private final TrafficPredictionService trafficPredictionService;
    private final MlServiceProperties mlServiceProperties;

    public TrafficController(TrafficPredictionService trafficPredictionService,
                             MlServiceProperties mlServiceProperties) {
        this.trafficPredictionService = trafficPredictionService;
        this.mlServiceProperties = mlServiceProperties;
    }

    @GetMapping("/health")
    public BackendHealthResponse health() {
        return new BackendHealthResponse("ok", "traffic-backend", mlServiceProperties.getBaseUrl());
    }

    @PostMapping("/predict")
    public PredictTrafficResponse predict(@Valid @RequestBody PredictTrafficRequest request) {
        return trafficPredictionService.predict(request);
    }

    @PostMapping("/train")
    public TrainModelResponse train(@Valid @RequestBody TrainModelRequest request) {
        return trafficPredictionService.train(request);
    }

    @GetMapping("/insights")
    public InsightsResponse insights() {
        return trafficPredictionService.insights();
    }
}
