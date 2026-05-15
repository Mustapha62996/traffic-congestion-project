from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "traffic_pred_dataset_updated.csv"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "traffic_congestion_model.joblib"
METADATA_PATH = ARTIFACTS_DIR / "training_metadata.json"
INTERPRETATION_DIR = ARTIFACTS_DIR / "interpretation"

FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "is_weekend",
    "location",
    "road_type",
    "weather",
    "road_condition",
    "vehicle_mix",
    "near_commercial_hub",
]
REGRESSION_TARGET_COLUMN = "traffic_volume"
LEGACY_CLASS_COLUMN = "congestion_level"

USER_INPUT_COLUMNS = [
    "hour",
    "day_of_week",
    "location",
    "weather",
    "road_condition",
    "road_type",
    "vehicle_mix",
    "near_commercial_hub",
    "is_weekend",
]
