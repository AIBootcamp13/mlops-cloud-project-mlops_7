from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import wandb


app = FastAPI()


# 모델 로딩
run = wandb.init()
artifact = run.use_artifact('jandar-tech/ml-ops-practice2/xgboost:v0', type='model')
artifact_dir = artifact.download()


# 입력 데이터 스키마 정의
class InputData(BaseModel):
    weather: str
    "지역": str


@app.get("/")
def read_root() -> dict:
    return {"status": "Healthy"}
