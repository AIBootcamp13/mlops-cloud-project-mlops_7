from fastapi import FastAPI
from pydantic import BaseModel
from predict import predict_df  # 예측 함수 import


app = FastAPI()


# 입력 데이터 스키마 정의
class InputData(BaseModel):
    region: str
    date: str  # 예: "2024-06-01"

@app.get("/")
def read_root() -> dict:
    return {"status": "Healthy"}

@app.post("/predict")
def predict_api(input: InputData):
    try:
        prediction = predict_df(input.region, input.date)
        return {
            "region": input.region,
            "date": input.date,
            "prediction": prediction
        }
    except Exception as e:
        return {
            "error": str(e),
            "region": input.region,
            "date": input.date
        }
