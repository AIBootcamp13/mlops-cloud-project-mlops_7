import datetime
from pathlib import Path

import joblib
import pandas as pd

from src.data.handler import WeatherDataOutlierHandler
from src.data.imputer import WeatherDataImputer
from src.data.transformer import WeatherDataTransformer
from src.libs.weather.asosstation import AsosStation
from src.libs.weather.fetcher import AsosDataFetcher
from src.tracker.wandb import WandbTracker
from src.utils.log import get_logger


def load_model_from_wandb(model_name: str = "best_model", version: str = "latest"):
    """
    W&B에서 모델 artifact 직접 불러와 joblib으로 로드하는 함수
    """
    experiment_name = "load_best_model"

    tracker = WandbTracker.create()
    tracker.start_experiment(
        experiment_name=experiment_name,
        params={},
        job_type="inference",
    )

    artifact_ref = f"{tracker.project_name}/{model_name}:{version}"
    artifact = tracker.run.use_artifact(artifact_ref, type="model")

    model_dir = Path(artifact.download())
    model_files = list(model_dir.glob("*.joblib"))

    if not model_files:
        raise FileNotFoundError(f"모델 파일(.joblib)을 찾을 수 없습니다: {model_dir}")

    model_path = model_files[0]
    model = joblib.load(model_path)

    tracker.end_experiment()
    return model


def fetch_features_from_weather_api(region: str, date: str) -> pd.DataFrame:
    """
    사용자가 입력한 날짜 기준으로 1년 전 날씨 데이터를 ASOS API에서 가져옴
    """
    target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    one_year_ago = target_date.replace(year=target_date.year - 1)

    try:
        station_id = AsosStation[region.upper()]
    except KeyError as e:
        raise ValueError(f"지원되지 않는 지역명입니다: {region}", e)  # noqa: B904

    fetcher = AsosDataFetcher.create()
    response = fetcher.fetch_all(
        asos_station=station_id,
        start_date=one_year_ago,
        end_date=one_year_ago,
    )

    if not response.is_success or not response.items:
        raise RuntimeError(f"{region} 지역의 {one_year_ago.date()} 날씨 데이터를 가져올 수 없습니다.")

    return pd.DataFrame(response.items)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    DAG 전처리 파이프라인과 동일한 추론용 전처리 함수
    학습된 변환기를 사용하여 transform() 수행
    """
    logger = get_logger("inference")
    result = df.copy()
    logger.info(f"current dataset: {result.shape}")
    logger.info(result)

    # 1. 결측치 보간
    result = WeatherDataImputer().transform(result)
    logger.info("After WeatherDataImputer")
    logger.info(result.shape)

    # 2. 이상치 처리
    result = WeatherDataOutlierHandler().transform(result)
    logger.info("After WeatherDataOutlierHandler")
    logger.info(result.shape)

    # 3. 피처 변환 (인코딩, 스케일링 등)
    result = WeatherDataTransformer().transform(result)
    logger.info("After WeatherDataTransformer")
    logger.info(result.shape)

    return result


def predict_weather(region: str, date: str) -> str:
    """
    지역과 날짜를 입력받아 날씨 예측값을 반환
    """
    input_df = preprocess(fetch_features_from_weather_api(region, date))

    model_wrapper = load_model_from_wandb()

    # 내부 모델 추출 및 예측
    if isinstance(model_wrapper, dict) and "model" in model_wrapper:
        model = model_wrapper["model"]
    elif hasattr(model_wrapper, "predict"):
        model = model_wrapper
    else:
        raise TypeError("predict() 가능한 모델 객체가 아닙니다.")

    prediction = model.predict(input_df)

    if prediction is None:
        raise ValueError("모델 예측 결과가 None입니다.")

    return prediction[0]
