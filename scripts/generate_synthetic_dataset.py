from __future__ import annotations

import argparse
import csv
import random
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "traffic_pred_dataset_updated.csv"
FIELDNAMES = [
    "hour",
    "day_of_week",
    "is_weekend",
    "location",
    "road_type",
    "weather",
    "road_condition",
    "traffic_volume",
    "vehicle_mix",
    "near_commercial_hub",
    "congestion_level",
]


def weighted_choice(rng: random.Random, mapping: dict[object, float]):
    options = list(mapping.keys())
    weights = list(mapping.values())
    return rng.choices(options, weights=weights, k=1)[0]


def location_profiles() -> dict[str, dict[str, object]]:
    return {
        "Lokoja_Central_OldMarket": {
            "weight": 1.5,
            "base_offset": 34,
            "road_type": {"Urban": 0.9, "Highway": 0.05, "Residential": 0.05},
            "vehicle_mix": {"Mixed": 0.55, "Commercial": 0.35, "Private": 0.10},
            "near_hub": {1: 0.95, 0: 0.05},
        },
        "Kabba_Junction": {
            "weight": 1.35,
            "base_offset": 30,
            "road_type": {"Urban": 0.75, "Highway": 0.25, "Residential": 0.0},
            "vehicle_mix": {"Mixed": 0.50, "Commercial": 0.35, "Private": 0.15},
            "near_hub": {1: 0.85, 0: 0.15},
        },
        "Nataco": {
            "weight": 1.2,
            "base_offset": 24,
            "road_type": {"Urban": 0.70, "Highway": 0.20, "Residential": 0.10},
            "vehicle_mix": {"Mixed": 0.50, "Commercial": 0.25, "Private": 0.25},
            "near_hub": {1: 0.80, 0: 0.20},
        },
        "Ganaja": {
            "weight": 1.1,
            "base_offset": 18,
            "road_type": {"Urban": 0.45, "Highway": 0.45, "Residential": 0.10},
            "vehicle_mix": {"Mixed": 0.45, "Commercial": 0.20, "Private": 0.35},
            "near_hub": {1: 0.65, 0: 0.35},
        },
        "Felele": {
            "weight": 1.0,
            "base_offset": 14,
            "road_type": {"Urban": 0.35, "Highway": 0.55, "Residential": 0.10},
            "vehicle_mix": {"Mixed": 0.40, "Commercial": 0.20, "Private": 0.40},
            "near_hub": {1: 0.60, 0: 0.40},
        },
        "Adankolo": {
            "weight": 0.95,
            "base_offset": 10,
            "road_type": {"Urban": 0.55, "Highway": 0.10, "Residential": 0.35},
            "vehicle_mix": {"Mixed": 0.45, "Commercial": 0.15, "Private": 0.40},
            "near_hub": {1: 0.45, 0: 0.55},
        },
        "Phase_I": {
            "weight": 0.8,
            "base_offset": 2,
            "road_type": {"Urban": 0.20, "Highway": 0.05, "Residential": 0.75},
            "vehicle_mix": {"Mixed": 0.25, "Commercial": 0.05, "Private": 0.70},
            "near_hub": {1: 0.10, 0: 0.90},
        },
        "Zango": {
            "weight": 0.75,
            "base_offset": 0,
            "road_type": {"Urban": 0.25, "Highway": 0.10, "Residential": 0.65},
            "vehicle_mix": {"Mixed": 0.30, "Commercial": 0.10, "Private": 0.60},
            "near_hub": {1: 0.20, 0: 0.80},
        },
    }


def hour_effect(hour: int) -> float:
    if hour in {6, 7, 8, 9}:
        return 34 + (9 - abs(8 - hour)) * 2
    if hour in {16, 17, 18, 19, 20}:
        return 48 + (10 - abs(18 - hour)) * 3
    if hour in {12, 13, 14, 15}:
        return 20
    if hour in {10, 11, 21}:
        return 10
    if hour in {0, 1, 2, 3, 4, 5, 22, 23}:
        return -8
    return 0


def day_effect(day_of_week: int, near_hub: int) -> float:
    if day_of_week in {0, 1, 2, 3, 4}:
        return 8 if near_hub else 4
    if day_of_week == 5:
        return 1 if near_hub else -6
    return -3 if near_hub else -10


def weather_effect(weather: str) -> float:
    return 18 if weather == "Rain" else 0


def road_type_effect(road_type: str) -> float:
    return {"Urban": 16, "Highway": 10, "Residential": -4}[road_type]


def vehicle_mix_effect(vehicle_mix: str) -> float:
    return {"Commercial": 16, "Mixed": 9, "Private": 0}[vehicle_mix]


def road_condition_effect(road_condition: int) -> float:
    return {1: 0, 2: 8, 3: 18}[road_condition]


def derive_congestion_label(volume: float, low_max: float, medium_max: float) -> str:
    if volume <= low_max:
        return "Low"
    if volume <= medium_max:
        return "Medium"
    return "High"


def generate_records(count: int, seed: int) -> list[dict[str, object]]:
    rng = random.Random(seed)
    profiles = location_profiles()
    locations = {name: data["weight"] for name, data in profiles.items()}
    weather_weights = {"Clear": 0.72, "Rain": 0.28}
    road_condition_weights = {1: 0.52, 2: 0.36, 3: 0.12}

    records: list[dict[str, object]] = []
    for _ in range(count):
        hour = rng.choices(
            population=list(range(24)),
            weights=[
                0.4, 0.35, 0.3, 0.25, 0.25, 0.35, 0.8, 1.25, 1.2, 0.9, 0.7, 0.7,
                0.85, 0.9, 0.95, 1.0, 1.3, 1.45, 1.55, 1.45, 1.1, 0.7, 0.5, 0.4,
            ],
            k=1,
        )[0]
        day_of_week = rng.randint(0, 6)
        is_weekend = int(day_of_week in {5, 6})

        location = weighted_choice(rng, locations)
        profile = profiles[location]
        road_type = weighted_choice(rng, profile["road_type"])
        vehicle_mix = weighted_choice(rng, profile["vehicle_mix"])
        near_commercial_hub = weighted_choice(rng, profile["near_hub"])
        weather = weighted_choice(rng, weather_weights)
        road_condition = weighted_choice(rng, road_condition_weights)

        if weather == "Rain" and rng.random() < 0.35:
            road_condition = min(3, road_condition + 1)

        volume = (
            22
            + profile["base_offset"]
            + hour_effect(hour)
            + day_effect(day_of_week, near_commercial_hub)
            + weather_effect(weather)
            + road_type_effect(road_type)
            + vehicle_mix_effect(vehicle_mix)
            + road_condition_effect(road_condition)
            + (16 if near_commercial_hub else 0)
            + rng.gauss(0, 9.5)
        )

        if is_weekend and road_type == "Residential":
            volume -= 8
        if weather == "Rain" and hour in {16, 17, 18, 19}:
            volume += 10

        volume = round(max(8.0, min(225.0, volume)), 2)
        records.append(
            {
                "hour": hour,
                "day_of_week": day_of_week,
                "is_weekend": is_weekend,
                "location": location,
                "road_type": road_type,
                "weather": weather,
                "road_condition": road_condition,
                "traffic_volume": volume,
                "vehicle_mix": vehicle_mix,
                "near_commercial_hub": near_commercial_hub,
                "congestion_level": "",
            }
        )

    volumes = sorted(record["traffic_volume"] for record in records)
    low_index = max(0, min(len(volumes) - 1, int(len(volumes) * 0.33)))
    medium_index = max(0, min(len(volumes) - 1, int(len(volumes) * 0.66)))
    low_max = volumes[low_index]
    medium_max = volumes[medium_index]

    for record in records:
        record["congestion_level"] = derive_congestion_label(
            record["traffic_volume"],
            low_max,
            medium_max,
        )

    return records


def write_dataset(records: list[dict[str, object]], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


def summarize(records: list[dict[str, object]]) -> str:
    counts = Counter(record["congestion_level"] for record in records)
    return (
        f"Generated {len(records)} records "
        f"(High={counts.get('High', 0)}, Medium={counts.get('Medium', 0)}, Low={counts.get('Low', 0)})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the synthetic Lokoja traffic dataset.")
    parser.add_argument("--count", type=int, default=2000, help="Number of records to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=Path, default=DATASET_PATH, help="CSV output path.")
    args = parser.parse_args()

    records = generate_records(count=args.count, seed=args.seed)
    write_dataset(records, args.output)
    print(summarize(records))


if __name__ == "__main__":
    main()
