import os
from pathlib import Path

import requests
import tqdm
import wandb
import pandas as pd
import joblib

from src.libs.storage import Storage
from src.libs.weather.asosstation import AsosStation

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
    years = range(str(int(this_year) - 5), this_year)

    all_data = []

    for year in tqdm(years):
        params = {
            "serviceKey": WEATHER_API_KEY,
            "pageNo": "1",
            "numOfRows": "999",
            "dataType": "JSON",
            "dataCd": "ASOS",
            "dateCd": "DAY",
            "startDt": f"{year}{this_date}",
            "endDt": f"{year}{this_date}",
            "stnIds": stn_id,
        }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        json_data = response.json()
        items = json_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        all_data.extend(items)
    else:
        print(f"[{year}] 요청 실패: {response.status_code}")


    df = pd.DataFrame(all_data)

#ex) region : 서울, date : 2010-01-01
def create_feature_df(region: str, date: str) -> pd.DataFrame:
    """
     지점, 날짜를 기반으로 기상청 api로 불러와서 사용
    """ 

    station = AsosStation.changed_name(region) #changed_name 은 한글로 재맵핑하는 코드 작성 필요
    stn_id = station.id
    
