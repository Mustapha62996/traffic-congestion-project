from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import FEATURE_COLUMNS


def _group_encoded_feature_name(encoded_name: str) -> str:
    clean = encoded_name.split("__", 1)[-1]
    for feature in FEATURE_COLUMNS:
        if clean == feature or clean.startswith(f"{feature}_"):
            return feature
    return clean


def _prediction_fn_from_pipeline(model, columns: list[str]):
    def predict_fn(values: np.ndarray) -> np.ndarray:
        frame = pd.DataFrame(values, columns=columns)
        return model.predict(frame)

    return predict_fn


def _build_lime_encoded_frames(X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[int, str]]]:
    encoded_train = X_train.copy()
    encoded_test = X_test.copy()
    categorical_lookup: dict[str, dict[int, str]] = {}

    for column in ["location", "road_type", "weather", "vehicle_mix"]:
        categories = sorted(X_train[column].astype(str).unique().tolist())
        forward = {value: index for index, value in enumerate(categories)}
        reverse = {index: value for value, index in forward.items()}
        encoded_train[column] = X_train[column].astype(str).map(forward).astype(float)
        encoded_test[column] = X_test[column].astype(str).map(forward).astype(float)
        categorical_lookup[column] = reverse

    return encoded_train, encoded_test, categorical_lookup


def _save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def generate_interpretation_artifacts(
    model,
    model_name: str,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    feature_importance: list[dict[str, float]],
    output_dir: Path,
    random_state: int = 42,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle: dict[str, Any] = {
        "feature_importance": {
            "top_features": feature_importance[:5],
        },
        "pdp": {"status": "not_generated", "plots": [], "summary": []},
        "lime": {"status": "not_generated", "plot": None, "summary": []},
        "shap": {"status": "not_generated", "plot": None, "summary": []},
    }

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
        from sklearn.inspection import PartialDependenceDisplay
    except Exception as exc:
        bundle["feature_importance"]["plot"] = None
        bundle["feature_importance"]["status"] = f"plotting_unavailable: {type(exc).__name__}"
        return bundle

    sns.set_theme(style="whitegrid")
    fi_frame = pd.DataFrame(feature_importance[:8])
    fi_plot = output_dir / "feature_importance.png"
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.barplot(data=fi_frame, x="importance", y="feature", ax=ax, palette="Blues_r")
    ax.set_title("Permutation Feature Importance")
    ax.set_xlabel("Importance Score")
    ax.set_ylabel("Feature")
    fig.tight_layout()
    fig.savefig(fi_plot, dpi=200, bbox_inches="tight")
    plt.close(fig)
    bundle["feature_importance"]["plot"] = str(fi_plot)
    bundle["feature_importance"]["status"] = "generated"

    pdp_features = [item["feature"] for item in feature_importance if item["feature"] in {"hour", "day_of_week", "road_condition", "near_commercial_hub"}][:2]
    if not pdp_features:
        pdp_features = ["hour", "day_of_week"]
    try:
        fig, ax = plt.subplots(figsize=(8, 4.8))
        PartialDependenceDisplay.from_estimator(model, X_test, pdp_features, ax=ax)
        fig.suptitle("Partial Dependence Plots", y=1.02)
        fig.tight_layout()
        pdp_plot = output_dir / "partial_dependence.png"
        fig.savefig(pdp_plot, dpi=200, bbox_inches="tight")
        plt.close(fig)
        bundle["pdp"]["status"] = "generated"
        bundle["pdp"]["plots"] = [str(pdp_plot)]
        bundle["pdp"]["summary"] = [
            f"Partial dependence was generated for {feature} to show its average marginal effect on predicted traffic volume."
            for feature in pdp_features
        ]
    except Exception as exc:
        bundle["pdp"]["status"] = f"failed: {type(exc).__name__}"

    try:
        from lime.lime_tabular import LimeTabularExplainer

        encoded_train, encoded_test, categorical_lookup = _build_lime_encoded_frames(X_train[FEATURE_COLUMNS], X_test[FEATURE_COLUMNS])
        categorical_features = [FEATURE_COLUMNS.index(name) for name in ["location", "road_type", "weather", "vehicle_mix"]]
        categorical_names = {
            FEATURE_COLUMNS.index(column): [label for _, label in sorted(categorical_lookup[column].items())]
            for column in ["location", "road_type", "weather", "vehicle_mix"]
        }

        def lime_prediction_fn(values: np.ndarray) -> np.ndarray:
            frame = pd.DataFrame(values, columns=FEATURE_COLUMNS)
            for column in ["location", "road_type", "weather", "vehicle_mix"]:
                reverse = categorical_lookup[column]
                frame[column] = frame[column].round().astype(int).map(reverse)
            return model.predict(frame)

        explainer = LimeTabularExplainer(
            training_data=encoded_train.to_numpy(),
            feature_names=FEATURE_COLUMNS,
            mode="regression",
            categorical_features=categorical_features,
            categorical_names=categorical_names,
            random_state=random_state,
        )
        sample_row = encoded_test.iloc[0][FEATURE_COLUMNS]
        explanation = explainer.explain_instance(
            sample_row.to_numpy(),
            lime_prediction_fn,
            num_features=6,
        )
        lime_items = explanation.as_list()
        bundle["lime"]["summary"] = [f"{feature}: {value:.3f}" for feature, value in lime_items]
        fig = explanation.as_pyplot_figure()
        fig.set_size_inches(8, 4.8)
        fig.tight_layout()
        lime_plot = output_dir / "lime_explanation.png"
        fig.savefig(lime_plot, dpi=200, bbox_inches="tight")
        plt.close(fig)
        bundle["lime"]["status"] = "generated"
        bundle["lime"]["plot"] = str(lime_plot)
        _save_json(output_dir / "lime_explanation.json", {"summary": bundle["lime"]["summary"]})
    except Exception as exc:
        bundle["lime"]["status"] = f"failed: {type(exc).__name__}"

    try:
        import shap

        preprocessor = model.named_steps["preprocessor"]
        regressor = model.named_steps["regressor"]
        transformed_train = preprocessor.transform(X_train)
        transformed_test = preprocessor.transform(X_test)
        feature_names = preprocessor.get_feature_names_out()
        sample_size = min(120, transformed_test.shape[0])

        if model_name == "RandomForestRegressor":
            explainer = shap.TreeExplainer(regressor)
            shap_values = explainer.shap_values(transformed_test[:sample_size])
        else:
            background = transformed_train[: min(100, transformed_train.shape[0])]
            explainer = shap.Explainer(regressor, background)
            shap_values = explainer(transformed_test[:sample_size]).values

        shap_array = np.asarray(shap_values)
        grouped_scores: dict[str, float] = {feature: 0.0 for feature in FEATURE_COLUMNS}
        for index, encoded_name in enumerate(feature_names):
            grouped_scores[_group_encoded_feature_name(str(encoded_name))] += float(np.mean(np.abs(shap_array[:, index])))

        ordered_scores = sorted(
            [{"feature": key, "importance": value} for key, value in grouped_scores.items()],
            key=lambda item: item["importance"],
            reverse=True,
        )
        bundle["shap"]["summary"] = [
            f"{item['feature']}: {item['importance']:.3f}" for item in ordered_scores[:6]
        ]

        shap_frame = pd.DataFrame(ordered_scores[:8])
        fig, ax = plt.subplots(figsize=(8, 4.8))
        sns.barplot(data=shap_frame, x="importance", y="feature", ax=ax, palette="crest")
        ax.set_title("Mean Absolute SHAP Values")
        ax.set_xlabel("Mean |SHAP value|")
        ax.set_ylabel("Feature")
        fig.tight_layout()
        shap_plot = output_dir / "shap_summary.png"
        fig.savefig(shap_plot, dpi=200, bbox_inches="tight")
        plt.close(fig)

        bundle["shap"]["status"] = "generated"
        bundle["shap"]["plot"] = str(shap_plot)
        _save_json(output_dir / "shap_summary.json", {"summary": bundle["shap"]["summary"]})
    except Exception as exc:
        bundle["shap"]["status"] = f"failed: {type(exc).__name__}"

    _save_json(output_dir / "interpretation_summary.json", bundle)
    return bundle
