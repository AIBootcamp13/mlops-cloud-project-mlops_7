from datetime import datetime

import pandas as pd
from config.default_args import KEY_FEATURE_DATASET_STORAGE_KEY, KEY_LAST_FETCHING_DATE, get_dynamic_default_args
from dateutil.relativedelta import relativedelta

from airflow.decorators import dag, task, task_group
from airflow.models import Variable
from src.data.handler import WeatherDataOutlierHandler
from src.data.imputer import WeatherDataImputer
from src.data.labeler import WeatherLabeler
from src.data.loader import AsosDataLoader
from src.data.transformer import WeatherDataTransformer
from src.libs.storage import Storage
from src.utils.config import DEFAULT_DATE_FORMAT
from src.utils.log import get_logger


FIRST_COLLECTING_DURATION = 5  # 연단위

default_args = get_dynamic_default_args()
_logger = get_logger("weather_data_pipeline")


@dag(
    dag_id="weather_data_pipeline",
    start_date=datetime(2025, 6, 1),
    schedule=relativedelta(months=3),
    catchup=False,
    tags=["weather", "data-engineering"],
    default_args=default_args,
)
def data_pipeline_dag():
    storage = Storage.create()

    @task_group(group_id="data_collection")
    def collect_asos_data() -> tuple[datetime, pd.DataFrame]:
        """데이터 수집 작업 그룹"""

        @task
        def get_last_fetching_date() -> datetime:
            """Variable에서 마지막 수집 날짜 조회. 없으면 5년 전으로 초기화"""
            fetching_date_str = Variable.get(KEY_LAST_FETCHING_DATE, default_var=None)
            if fetching_date_str is None:
                return datetime.now() - relativedelta(years=FIRST_COLLECTING_DURATION)
            return datetime.strptime(fetching_date_str, DEFAULT_DATE_FORMAT)

        @task
        def fetch_and_upload_asos_data(_: datetime) -> datetime:
            """기상청 API 로 데이터 수집 후 S3 업로드"""
            # TODO 나중에 배포시에 변경될 예정입니다.
            # end_date = datetime(2025, 5, 31)
            # end_date = datetime.now() - timedelta(days=1)
            # collector = Collector(storage=storage, fetcher=AsosDataFetcher.create())
            # collector.collect_all_asos_data(start_date=start_date, end_date=end_date)
            # collector.upload_all_asos_data(with_index=False)
            return datetime(2025, 5, 31)

        @task
        def update_last_fetching_date(new_end_date: datetime) -> None:
            """Variable 에 새로운 수집 날짜 저장"""
            Variable.set(KEY_LAST_FETCHING_DATE, new_end_date.strftime(DEFAULT_DATE_FORMAT))

        @task
        def load_dataset(fetching_date: datetime) -> pd.DataFrame:
            """S3 에서 CSV 불러와 DataFrame 으로 변환"""
            datasets_per_station = AsosDataLoader(storage=storage).load_at(fetching_date=fetching_date)
            return pd.concat(list(datasets_per_station.values()))

        # 데이터 수집
        new_last_fetching_date = fetch_and_upload_asos_data(get_last_fetching_date())

        # 데이터 적재
        update_last_fetching_date(new_last_fetching_date)
        datasets_per_asos_station = load_dataset(new_last_fetching_date)
        return new_last_fetching_date, datasets_per_asos_station

    @task_group(group_id="data_preprocessing")
    def preprocess_data(raw_dataset: pd.DataFrame, load_date: datetime) -> None:
        """데이터 전처리 작업 그룹"""

        @task
        def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
            """결측치 보간"""
            return WeatherDataImputer().fit_transform(df)

        @task
        def label_dataset(df: pd.DataFrame) -> pd.DataFrame:
            """날씨 레이블 추가"""
            return WeatherLabeler().fit_transform(df)

        @task
        def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
            """수치형 변수에 대해 IQR 기반 이상치 처리"""
            return WeatherDataOutlierHandler().fit_transform(df)

        @task
        def transform_features(df: pd.DataFrame) -> pd.DataFrame:
            """feature 인코딩 처리"""
            return WeatherDataTransformer().fit_transform(df)

        @task
        def save_features(feature_df: pd.DataFrame, dataset_date: datetime) -> str:
            """최종 전처리 결과를 S3 에 저장 및 그 key 를 Variable 에 저장"""
            filename = "weather_features.csv"
            sub_directory = dataset_date.strftime(DEFAULT_DATE_FORMAT)
            storage_key = storage.make_csv_key_in_features(filename, sub_directory=sub_directory)
            if not storage.upload_dataframe(feature_df, key=storage_key):
                raise RuntimeError("features 업로드 실패")

            Variable.set(KEY_FEATURE_DATASET_STORAGE_KEY, storage_key)
            return storage_key

        # 전처리 단계
        imputed_df = impute_missing_values(raw_dataset)
        labeled_df = label_dataset(imputed_df)
        handled_df = handle_outliers(labeled_df)
        features = transform_features(handled_df)
        # 전처리된 데이터 저장
        feature_key = save_features(features, dataset_date=load_date)
        _logger.info(f"Uploaded features;{feature_key}")

    last_fetching_date, dataset = collect_asos_data()
    preprocess_data(dataset, load_date=last_fetching_date)


data_pipeline_dag()
