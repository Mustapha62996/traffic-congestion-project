from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .config import METADATA_PATH
from .predictor import predictor_service
from .schema import InsightsResponse, PredictionInput, PredictionResponse, TrainRequest
from .training import train_and_save_model


app = FastAPI(
    title="Lokoja Traffic Congestion ML Service",
    description="Prediction and decision-support service for traffic congestion in Lokoja.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionInput) -> dict:
    try:
        return predictor_service.predict(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/train")
def train(request: TrainRequest) -> dict:
    result = train_and_save_model(
        test_size=request.test_size,
        random_state=request.random_state,
        n_estimators=request.n_estimators,
    )
    predictor_service._model = None
    predictor_service._metadata = None
    return {"status": "trained", "metrics": result.__dict__}


@app.get("/insights", response_model=InsightsResponse)
def insights() -> dict:
    if not Path(METADATA_PATH).exists():
        raise HTTPException(status_code=503, detail="No training metadata found. Run /train first.")
    return json.loads(Path(METADATA_PATH).read_text(encoding="utf-8"))
