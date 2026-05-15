from __future__ import annotations

from typing import Any

from .data import volume_to_congestion_level


def build_prediction_explanation(
    normalized_input: dict[str, Any],
    predicted_volume: float,
    thresholds: dict[str, float],
    feature_importance: list[dict[str, Any]],
    location_patterns: list[dict[str, Any]],
) -> list[str]:
    reasons: list[str] = []
    important_features = {item["feature"] for item in feature_importance[:5]}

    hour = int(normalized_input["hour"])
    weather = str(normalized_input["weather"])
    location = str(normalized_input["location"])

    if hour in {7, 8, 9, 16, 17, 18, 19}:
        reasons.append("Peak-hour traffic is influencing this prediction.")
    if predicted_volume >= thresholds["medium_max"]:
        reasons.append("High traffic volume is a strong congestion signal.")
    elif predicted_volume <= thresholds["low_max"]:
        reasons.append("Lower traffic volume is reducing congestion pressure.")

    if weather.lower() != "clear":
        reasons.append("Weather conditions are increasing congestion risk.")

    if normalized_input.get("near_commercial_hub") == 1:
        reasons.append("Proximity to a commercial hub is associated with heavier traffic.")

    if "road_condition" in important_features and int(normalized_input["road_condition"]) >= 2:
        reasons.append("Road condition is contributing to slower traffic flow.")

    for pattern in location_patterns:
        if pattern["location"] == location and pattern.get("High", 0) >= pattern.get("Low", 0):
            reasons.append("Historical location patterns suggest this area often experiences heavier congestion.")
            break

    derived_level = volume_to_congestion_level(predicted_volume, thresholds)
    if derived_level == "High":
        reasons.append("The predicted traffic volume falls inside the high congestion range.")
    elif derived_level == "Medium":
        reasons.append("The predicted traffic volume falls inside the medium congestion range.")
    else:
        reasons.append("The predicted traffic volume falls inside the low congestion range.")

    if not reasons:
        reasons.append("This prediction is mostly driven by the combined baseline conditions for the selected time and location.")

    return reasons[:4]
