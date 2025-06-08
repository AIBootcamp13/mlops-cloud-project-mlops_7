import os
from pathlib import Path

import requests
import tqdm
import wandb
import pandas as pd
import joblib

from src.libs.storage import Storage
from src.libs.weather.asosstation import AsosStation

from src.data.imputer import WeatherDataImputer
from src.data.labeler import WeatherLabeler
from src.data.handler import WeatherDataOutlierHandler
from src.data.transformer import WeatherDataTransformer

def load_model() -> object:
     # 모델 로딩
    run = wandb.init(project="ml-ops-practice2")
    artifact = run.use_artifact('jandar-tech/ml-ops-practice2/xgboost:v0', type='model')
    artifact_dir = artifact.download()
    run.finish()
    
    model_path = Path(artifact_dir) / "model-xgboost.joblib"
    return joblib.load(model_path)


MODEL = load_model()

#asosstation.py 수정 요함
def load_specific_data(stn_id: int, date: str ):
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    base_url = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"

    this_year = date[:4]
    this_date = date[4:]

    all_data = []
    
    params = {
        "serviceKey": WEATHER_API_KEY,
        "pageNo": "1",
        "numOfRows": "999",
        "dataType": "JSON",
        "dataCd": "ASOS",
        "dateCd": "DAY",
        "startDt": f"{this_year}{this_date}",
        "endDt": f"{this_year}{this_date}",
        "stnIds": stn_id,
    }

    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        json_data = response.json()
        items = json_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        all_data.extend(items)
    else:
        print(f"[{this_year}] 요청 실패: {response.status_code}")


    df = pd.DataFrame(all_data)
    return df

def preprocess(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    "입력날짜로 tm 변경 및 전처리 진행"
    df['tm'] = target_date #예측 날짜고 tm 변경
    df = WeatherDataImputer().fit_transform(df)
    df = WeatherLabeler().fit_transform(df)
    df = WeatherDataOutlierHandler().fit_transform(df)
    df= WeatherDataTransformer().fit_transform(df)
    
    #추론 시 타겟 제거
    if "weather" in df.columns:
            df = df.drop(columns=["weather"])
    
    return df

#ex) region : 서울, date : 2010-01-01
def predict_df(region: str, date: str) -> str:

    