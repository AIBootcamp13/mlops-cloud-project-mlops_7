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

def create_feature_df(region: str, date: str) -> pd.DataFrame:
    
    """
     지점, 날짜를 기반으로 storage에서 해당 날의 feature 파일을 찾아 로딩
    """ 

    station = AsosStation.changed_name(region) #changed_name 은 한글로 재맵핑하는 코드 작성 필요
    stn_id = station.id
    
