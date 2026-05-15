package com.lokoja.traffic.backend.service;

import com.lokoja.traffic.backend.dto.InsightsResponse;
import com.lokoja.traffic.backend.dto.PredictTrafficRequest;
import com.lokoja.traffic.backend.dto.PredictTrafficResponse;
import com.lokoja.traffic.backend.dto.TrainModelRequest;
import com.lokoja.traffic.backend.dto.TrainModelResponse;
import com.lokoja.traffic.backend.exception.MlServiceException;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Component
public class MlServiceClient {

    private final RestClient restClient;

    public MlServiceClient(RestClient mlRestClient) {
        this.restClient = mlRestClient;
    }

    public PredictTrafficResponse predict(PredictTrafficRequest request) {
        try {
            Map<String, Object> response = restClient.post()
                    .uri("/predict")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(toPythonPredictPayload(request))
                    .retrieve()
                    .body(new ParameterizedTypeReference<>() {});
            return toPredictResponse(response);
        } catch (HttpStatusCodeException ex) {
            throw new MlServiceException(HttpStatus.valueOf(ex.getStatusCode().value()), extractMessage(ex.getResponseBodyAsString()));
        } catch (RestClientException ex) {
            throw new MlServiceException(HttpStatus.BAD_GATEWAY, "Failed to reach ML service: " + ex.getMessage());
        }
    }

    public TrainModelResponse train(TrainModelRequest request) {
        try {
            return restClient.post()
                    .uri("/train")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(toPythonTrainPayload(request))
                    .retrieve()
                    .body(TrainModelResponse.class);
        } catch (HttpStatusCodeException ex) {
            throw new MlServiceException(HttpStatus.valueOf(ex.getStatusCode().value()), extractMessage(ex.getResponseBodyAsString()));
        } catch (RestClientException ex) {
            throw new MlServiceException(HttpStatus.BAD_GATEWAY, "Failed to reach ML service: " + ex.getMessage());
        }
    }

    public InsightsResponse insights() {
        try {
            Map<String, Object> response = restClient.get()
                    .uri("/insights")
                    .retrieve()
                    .body(new ParameterizedTypeReference<>() {});
            return toInsightsResponse(response);
        } catch (HttpStatusCodeException ex) {
            throw new MlServiceException(HttpStatus.valueOf(ex.getStatusCode().value()), extractMessage(ex.getResponseBodyAsString()));
        } catch (RestClientException ex) {
            throw new MlServiceException(HttpStatus.BAD_GATEWAY, "Failed to reach ML service: " + ex.getMessage());
        }
    }

    private Map<String, Object> toPythonPredictPayload(PredictTrafficRequest request) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("hour", request.hour());
        payload.put("day_of_week", request.dayOfWeek());
        payload.put("location", request.location());
        payload.put("weather", request.weather());
        payload.put("road_condition", request.roadCondition());
        payload.put("road_type", request.roadType());
        payload.put("vehicle_mix", request.vehicleMix());
        payload.put("near_commercial_hub", request.nearCommercialHub());
        payload.put("is_weekend", request.isWeekend());
        return payload;
    }

    private Map<String, Object> toPythonTrainPayload(TrainModelRequest request) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("test_size", request.resolvedTestSize());
        payload.put("random_state", request.resolvedRandomState());
        payload.put("n_estimators", request.resolvedNEstimators());
        return payload;
    }

    private String extractMessage(String responseBody) {
        if (responseBody == null || responseBody.isBlank()) {
            return "ML service request failed.";
        }
        return responseBody;
    }

    private PredictTrafficResponse toPredictResponse(Map<String, Object> response) {
        if (response == null) {
            throw new MlServiceException(HttpStatus.BAD_GATEWAY, "ML service returned an empty prediction response.");
        }

        return new PredictTrafficResponse(
                toDouble(response.get("predicted_traffic_volume")),
                toStringValue(response.get("congestion_level")),
                toDoubleMap(response.get("thresholds")),
                toStringList(response.get("explanation")),
                toObjectMap(response.get("normalized_input"))
        );
    }

    private InsightsResponse toInsightsResponse(Map<String, Object> response) {
        if (response == null) {
            throw new MlServiceException(HttpStatus.BAD_GATEWAY, "ML service returned empty insights.");
        }

        return new InsightsResponse(
                toObjectMap(response.get("dataset_profile")),
                extractModelMetrics(response),
                toListOfMaps(response.get("feature_importance")),
                toObjectMap(response.get("interpretation")),
                toDoubleMap(response.get("congestion_thresholds")),
                toIntegerList(response.get("peak_hours")),
                toListOfMaps(response.get("hourly_trends")),
                toListOfMaps(response.get("location_patterns"))
        );
    }

    private Double toDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        return null;
    }

    private String toStringValue(Object value) {
        return value == null ? null : value.toString();
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> toObjectMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            Map<String, Object> converted = new LinkedHashMap<>();
            map.forEach((key, entryValue) -> converted.put(String.valueOf(key), entryValue));
            return converted;
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Double> toDoubleMap(Object value) {
        if (!(value instanceof Map<?, ?> map)) {
            return null;
        }
        Map<String, Double> converted = new LinkedHashMap<>();
        map.forEach((key, entryValue) -> converted.put(String.valueOf(key), toDouble(entryValue)));
        return converted;
    }

    @SuppressWarnings("unchecked")
    private List<String> toStringList(Object value) {
        if (!(value instanceof List<?> list)) {
            return null;
        }
        List<String> converted = new ArrayList<>(list.size());
        list.forEach(item -> converted.add(item == null ? null : item.toString()));
        return converted;
    }

    @SuppressWarnings("unchecked")
    private List<Integer> toIntegerList(Object value) {
        if (!(value instanceof List<?> list)) {
            return null;
        }
        List<Integer> converted = new ArrayList<>(list.size());
        for (Object item : list) {
            if (item instanceof Number number) {
                converted.add(number.intValue());
            }
        }
        return converted;
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> toListOfMaps(Object value) {
        if (!(value instanceof List<?> list)) {
            return null;
        }
        List<Map<String, Object>> converted = new ArrayList<>(list.size());
        for (Object item : list) {
            Map<String, Object> mapped = toObjectMap(item);
            if (mapped != null) {
                converted.add(mapped);
            }
        }
        return converted;
    }

    private Map<String, Object> extractModelMetrics(Map<String, Object> response) {
        Map<String, Object> metrics = new LinkedHashMap<>();
        copyIfPresent(metrics, "mae", response.get("mae"));
        copyIfPresent(metrics, "rmse", response.get("rmse"));
        copyIfPresent(metrics, "r2", response.get("r2"));
        copyIfPresent(metrics, "baselineMae", response.get("baseline_mae"));
        copyIfPresent(metrics, "baselineRmse", response.get("baseline_rmse"));
        copyIfPresent(metrics, "baselineR2", response.get("baseline_r2"));
        copyIfPresent(metrics, "selectedModel", response.get("selected_model"));
        copyIfPresent(metrics, "modelName", response.get("model_name"));
        return metrics.isEmpty() ? null : metrics;
    }

    private void copyIfPresent(Map<String, Object> target, String key, Object value) {
        if (value != null) {
            target.put(key, value);
        }
    }
}
