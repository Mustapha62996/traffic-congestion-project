"""5-fold cross-validation and hyperparameter sensitivity grid for the Lokoja traffic model.

run from the project root:
    python scripts/cross_validate.py
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline

from ml_service.config import FEATURE_COLUMNS, REGRESSION_TARGET_COLUMN
from ml_service.data import load_dataset
from ml_service.training import build_preprocessor

RANDOM_STATE = 42
N_ESTIMATORS = [50, 100, 300, 500]
MAX_DEPTH = [None, 20, 12, 8]


def cv_r2(n_estimators: int, max_depth: int | None, X: pd.DataFrame, y: pd.Series):
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    folds = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    return cross_val_score(pipeline, X, y, cv=folds, scoring="r2", n_jobs=-1)


def main() -> None:
    dataset = load_dataset()
    X = dataset[FEATURE_COLUMNS]
    y = dataset[REGRESSION_TARGET_COLUMN]

    scores = cv_r2(300, None, X, y)
    print(f"Deployed configuration (300 trees, no depth limit): "
          f"mean R2 = {scores.mean():.3f}, std = {scores.std():.3f}")

    print("\nHyperparameter sensitivity (5-fold CV R2):")
    print(f"{'n_estimators':>12} {'max_depth':>10} {'mean R2':>9} {'std':>7}")
    for n, depth in itertools.product(N_ESTIMATORS, MAX_DEPTH):
        s = cv_r2(n, depth, X, y)
        print(f"{n:>12} {str(depth):>10} {s.mean():>9.4f} {s.std():>7.4f}")


if __name__ == "__main__":
    main()
