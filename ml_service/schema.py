from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class PredictionInput(BaseModel):
    hour: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)
    location: str
    weather: str
    road_condition: int = Field(ge=1, le=3)
    road_type: str | None = None
    vehicle_mix: str | None = None
    near_commercial_hub: int | None = Field(default=None, ge=0, le=1)
    is_weekend: int | None = Field(default=None, ge=0, le=1)

    @field_validator("location", "weather", "road_type", "vehicle_mix")
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()

    @model_validator(mode="after")
    def derive_is_weekend(self) -> "PredictionInput":
        if self.is_weekend is None:
            self.is_weekend = 1 if self.day_of_week in {5, 6} else 0
        return self


class TrainRequest(BaseModel):
    test_size: float = Field(default=0.2, gt=0.05, lt=0.5)
    random_state: int = 42
    n_estimators: int = Field(default=300, ge=100, le=1000)


class PredictionResponse(BaseModel):
    predicted_traffic_volume: float
    congestion_level: str
    thresholds: dict[str, float]
    explanation: list[str]
    normalized_input: dict[str, Any]


class InsightsResponse(BaseModel):
    dataset_profile: dict[str, Any]
    model_metrics: dict[str, Any] | None = None
    feature_importance: list[dict[str, Any]]
    interpretation: dict[str, Any] | None = None
    congestion_thresholds: dict[str, float]
    peak_hours: list[int]
    hourly_trends: list[dict[str, Any]]
    location_patterns: list[dict[str, Any]]
