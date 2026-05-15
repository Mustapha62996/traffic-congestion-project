from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from .config import FEATURE_COLUMNS, METADATA_PATH, MODEL_PATH
from .data import build_dataset_profile, load_dataset, volume_to_congestion_level
from .explain import build_prediction_explanation
from .schema import PredictionInput


class PredictorService:
    def __init__(self) -> None:
        self._model = None
        self._metadata: dict[str, Any] | None = None

    def _load_metadata(self) -> dict[str, Any]:
        if self._metadata is not None:
            return self._metadata
        if Path(METADATA_PATH).exists():
            self._metadata = json.loads(Path(METADATA_PATH).read_text(encoding="utf-8"))
        else:
            profile = build_dataset_profile(load_dataset())
            self._metadata = {
                "dataset_profile": {
                    "row_count": profile.row_count,
                    "categorical_options": profile.categorical_options,
                    "numeric_ranges": profile.numeric_ranges,
                    "defaults": profile.defaults,
                    "congestion_thresholds": profile.congestion_thresholds,
                },
                "feature_importance": [],
                "location_patterns": [],
                "congestion_thresholds": profile.congestion_thresholds,
                "interpretation": {},
            }
        return self._metadata

    def _load_model(self):
        if self._model is None:
            if not Path(MODEL_PATH).exists():
                raise FileNotFoundError("No trained model found. Run training first.")
            self._model = joblib.load(MODEL_PATH)
        return self._model

    def normalize_input(self, payload: PredictionInput) -> dict[str, Any]:
        metadata = self._load_metadata()
        defaults = metadata["dataset_profile"]["defaults"]
        normalized = payload.model_dump()
        normalized["road_type"] = normalized["road_type"] or defaults["road_type"]
        normalized["vehicle_mix"] = normalized["vehicle_mix"] or defaults["vehicle_mix"]
        if normalized["near_commercial_hub"] is None:
            normalized["near_commercial_hub"] = defaults["near_commercial_hub"]
        if normalized["is_weekend"] is None:
            normalized["is_weekend"] = defaults["is_weekend"]
        return normalized

    def validate_against_dataset(self, normalized_input: dict[str, Any]) -> None:
        metadata = self._load_metadata()
        profile = metadata["dataset_profile"]

        for field in ["location", "road_type", "weather", "vehicle_mix"]:
            options = profile["categorical_options"][field]
            if normalized_input[field] not in options:
                joined = ", ".join(options)
                raise ValueError(f"Invalid {field}. Expected one of: {joined}")

        numeric_ranges = profile["numeric_ranges"]
        for field in ["hour", "day_of_week", "is_weekend", "road_condition", "near_commercial_hub"]:
            value = float(normalized_input[field])
            min_value = numeric_ranges[field]["min"]
            max_value = numeric_ranges[field]["max"]
            if value < min_value or value > max_value:
                raise ValueError(f"Invalid {field}. Expected a value between {min_value} and {max_value}")

    def predict(self, payload: PredictionInput) -> dict[str, Any]:
        normalized_input = self.normalize_input(payload)
        self.validate_against_dataset(normalized_input)

        model = self._load_model()
        frame = pd.DataFrame([[normalized_input[column] for column in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
        predicted_volume = float(model.predict(frame)[0])

        metadata = self._load_metadata()
        thresholds = metadata["congestion_thresholds"]
        congestion_level = volume_to_congestion_level(predicted_volume, thresholds)
        explanation = build_prediction_explanation(
            normalized_input=normalized_input,
            predicted_volume=predicted_volume,
            thresholds=thresholds,
            feature_importance=metadata.get("feature_importance", []),
            location_patterns=metadata.get("location_patterns", []),
        )

        return {
            "predicted_traffic_volume": round(predicted_volume, 2),
            "congestion_level": congestion_level,
            "thresholds": thresholds,
            "explanation": explanation,
            "normalized_input": normalized_input,
        }


predictor_service = PredictorService()
