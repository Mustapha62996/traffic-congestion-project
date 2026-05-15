from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .config import DATASET_PATH, FEATURE_COLUMNS, LEGACY_CLASS_COLUMN, REGRESSION_TARGET_COLUMN


@dataclass
class DatasetProfile:
    row_count: int
    categorical_options: dict[str, list[Any]]
    numeric_ranges: dict[str, dict[str, float]]
    defaults: dict[str, Any]
    congestion_thresholds: dict[str, float]


def load_dataset() -> pd.DataFrame:
    dataset = pd.read_csv(DATASET_PATH)
    missing = set(FEATURE_COLUMNS + [REGRESSION_TARGET_COLUMN, LEGACY_CLASS_COLUMN]) - set(dataset.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Dataset is missing required columns: {missing_text}")
    return dataset


def derive_congestion_thresholds(dataset: pd.DataFrame) -> dict[str, float]:
    low_upper = float(dataset[REGRESSION_TARGET_COLUMN].quantile(0.33))
    medium_upper = float(dataset[REGRESSION_TARGET_COLUMN].quantile(0.66))
    return {
        "low_max": round(low_upper, 2),
        "medium_max": round(medium_upper, 2),
    }


def volume_to_congestion_level(volume: float, thresholds: dict[str, float]) -> str:
    if volume <= thresholds["low_max"]:
        return "Low"
    if volume <= thresholds["medium_max"]:
        return "Medium"
    return "High"


def build_dataset_profile(dataset: pd.DataFrame) -> DatasetProfile:
    categorical_columns = ["location", "road_type", "weather", "vehicle_mix"]
    numeric_columns = [
        "hour",
        "day_of_week",
        "is_weekend",
        "road_condition",
        "traffic_volume",
        "near_commercial_hub",
    ]

    categorical_options = {
        column: sorted(dataset[column].dropna().astype(str).unique().tolist())
        for column in categorical_columns
    }
    numeric_ranges = {
        column: {
            "min": float(dataset[column].min()),
            "max": float(dataset[column].max()),
        }
        for column in numeric_columns
    }
    defaults = {
        "road_type": str(dataset["road_type"].mode().iloc[0]),
        "vehicle_mix": str(dataset["vehicle_mix"].mode().iloc[0]),
        "near_commercial_hub": int(dataset["near_commercial_hub"].mode().iloc[0]),
        "is_weekend": int(dataset["is_weekend"].mode().iloc[0]),
    }

    return DatasetProfile(
        row_count=len(dataset),
        categorical_options=categorical_options,
        numeric_ranges=numeric_ranges,
        defaults=defaults,
        congestion_thresholds=derive_congestion_thresholds(dataset),
    )


def build_hourly_trends(dataset: pd.DataFrame) -> list[dict[str, Any]]:
    thresholds = derive_congestion_thresholds(dataset)
    labeled = dataset.assign(
        derived_congestion_level=dataset[REGRESSION_TARGET_COLUMN].apply(
            lambda value: volume_to_congestion_level(float(value), thresholds)
        )
    )
    grouped = (
        labeled.groupby(["hour", "derived_congestion_level"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("hour")
    )
    return grouped.to_dict(orient="records")


def build_location_patterns(dataset: pd.DataFrame) -> list[dict[str, Any]]:
    thresholds = derive_congestion_thresholds(dataset)
    labeled = dataset.assign(
        derived_congestion_level=dataset[REGRESSION_TARGET_COLUMN].apply(
            lambda value: volume_to_congestion_level(float(value), thresholds)
        )
    )
    grouped = (
        labeled.groupby(["location", "derived_congestion_level"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("location")
    )
    return grouped.to_dict(orient="records")


def build_peak_hour_summary(dataset: pd.DataFrame) -> list[int]:
    hourly_volume = (
        dataset.groupby("hour")[REGRESSION_TARGET_COLUMN]
        .mean()
        .sort_values(ascending=False)
    )
    return [int(hour) for hour in hourly_volume.head(5).index.tolist()]
