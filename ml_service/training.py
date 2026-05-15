from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import ARTIFACTS_DIR, FEATURE_COLUMNS, INTERPRETATION_DIR, METADATA_PATH, MODEL_PATH, REGRESSION_TARGET_COLUMN
from .data import (
    build_dataset_profile,
    build_hourly_trends,
    build_location_patterns,
    build_peak_hour_summary,
    derive_congestion_thresholds,
    load_dataset,
)
from .interpretation import generate_interpretation_artifacts


NUMERIC_FEATURES = [
    "hour",
    "day_of_week",
    "is_weekend",
    "road_condition",
    "near_commercial_hub",
]
CATEGORICAL_FEATURES = ["location", "road_type", "weather", "vehicle_mix"]


@dataclass
class TrainingResult:
    selected_model: str
    mae: float
    rmse: float
    r2: float
    baseline_mae: float
    baseline_rmse: float
    baseline_r2: float
    feature_importance: list[dict[str, float]]
    interpretation: dict[str, Any]
    dataset_profile: dict[str, Any]
    congestion_thresholds: dict[str, float]
    peak_hours: list[int]
    hourly_trends: list[dict[str, Any]]
    location_patterns: list[dict[str, Any]]


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def train_and_save_model(
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 300,
) -> TrainingResult:
    dataset = load_dataset()
    X = dataset[FEATURE_COLUMNS]
    y = dataset[REGRESSION_TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    preprocessor = build_preprocessor()
    baseline_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                LinearRegression(),
            ),
        ]
    )
    main_model = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=n_estimators,
                    random_state=random_state,
                ),
            ),
        ]
    )

    baseline_model.fit(X_train, y_train)
    main_model.fit(X_train, y_train)

    baseline_predictions = baseline_model.predict(X_test)
    predictions = main_model.predict(X_test)
    baseline_rmse = float(mean_squared_error(y_test, baseline_predictions) ** 0.5)
    random_forest_rmse = float(mean_squared_error(y_test, predictions) ** 0.5)

    selected_model_name = "RandomForestRegressor"
    selected_model = main_model
    selected_predictions = predictions
    if baseline_rmse < random_forest_rmse:
        selected_model_name = "LinearRegression"
        selected_model = baseline_model
        selected_predictions = baseline_predictions

    thresholds = derive_congestion_thresholds(dataset)
    metrics = TrainingResult(
        selected_model=selected_model_name,
        mae=float(mean_absolute_error(y_test, selected_predictions)),
        rmse=float(mean_squared_error(y_test, selected_predictions) ** 0.5),
        r2=float(r2_score(y_test, selected_predictions)),
        baseline_mae=float(mean_absolute_error(y_test, baseline_predictions)),
        baseline_rmse=baseline_rmse,
        baseline_r2=float(r2_score(y_test, baseline_predictions)),
        feature_importance=[],
        interpretation={},
        dataset_profile=asdict(build_dataset_profile(dataset)),
        congestion_thresholds=thresholds,
        peak_hours=build_peak_hour_summary(dataset),
        hourly_trends=build_hourly_trends(dataset),
        location_patterns=build_location_patterns(dataset),
    )

    importance = permutation_importance(
        selected_model,
        X_test,
        y_test,
        n_repeats=10,
        random_state=random_state,
        scoring="neg_root_mean_squared_error",
    )
    metrics.feature_importance = sorted(
        [
            {"feature": feature, "importance": float(score)}
            for feature, score in zip(FEATURE_COLUMNS, importance.importances_mean, strict=True)
        ],
        key=lambda item: item["importance"],
        reverse=True,
    )
    metrics.interpretation = generate_interpretation_artifacts(
        model=selected_model,
        model_name=selected_model_name,
        X_train=X_train,
        X_test=X_test,
        y_test=y_test,
        feature_importance=metrics.feature_importance,
        output_dir=INTERPRETATION_DIR,
        random_state=random_state,
    )

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected_model, MODEL_PATH)
    metadata = asdict(metrics)
    metadata["model_path"] = str(MODEL_PATH)
    metadata["target_column"] = REGRESSION_TARGET_COLUMN
    metadata["feature_columns"] = FEATURE_COLUMNS
    metadata["model_name"] = selected_model_name
    Path(METADATA_PATH).write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metrics
