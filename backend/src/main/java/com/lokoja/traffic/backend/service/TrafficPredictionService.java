package com.lokoja.traffic.backend.service;

import com.lokoja.traffic.backend.dto.InsightsResponse;
import com.lokoja.traffic.backend.dto.PredictTrafficRequest;
import com.lokoja.traffic.backend.dto.PredictTrafficResponse;
import com.lokoja.traffic.backend.dto.TrainModelRequest;
import com.lokoja.traffic.backend.dto.TrainModelResponse;
import org.springframework.stereotype.Service;

@Service
public class TrafficPredictionService {

    private final MlServiceClient mlServiceClient;

    public TrafficPredictionService(MlServiceClient mlServiceClient) {
        this.mlServiceClient = mlServiceClient;
    }

    public PredictTrafficResponse predict(PredictTrafficRequest request) {
        return mlServiceClient.predict(request);
    }

    public TrainModelResponse train(TrainModelRequest request) {
        return mlServiceClient.train(request);
    }

    public InsightsResponse insights() {
        return mlServiceClient.insights();
    }
}
