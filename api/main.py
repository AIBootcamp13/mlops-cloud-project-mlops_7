from fastapi import FastAPI
from pydantic import BaseModel

from api.inference import predict_weather


app = FastAPI()


# 입력 데이터 스키마 정의
class InputData(BaseModel):
    region: str
    date: str  # 예: "2024-06-01"


@app.get("/")
def read_root() -> dict:
    return {"status": "Healthy"}


@app.get("/load-model")
def load_model():
    pass


@app.post("/predict")
def predict_api(input_data_in: InputData):
    try:
        prediction = predict_weather(input_data_in.region, input_data_in.date)
        return {
            "region": input_data_in.region,
            "date": input_data_in.date,
            "prediction": prediction,
        }
    except Exception as e:
        return {"error": str(e), "region": input_data_in.region, "date": input_data_in.date}
