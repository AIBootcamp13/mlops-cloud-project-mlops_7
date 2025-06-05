import uuid
from datetime import datetime

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
    def collect_asos_data() -> str:
        """데이터 수집 작업 그룹"""

        @task
        def get_last_fetching_date() -> str:
            """Variable 에서 마지막 수집 날짜 문자열(%Y%m%d)조회. 없으면 5년 전으로 초기화"""
            fetching_date_str = Variable.get(KEY_LAST_FETCHING_DATE, default_var=None)
            if fetching_date_str is None:
                fetching_date = datetime.now() - relativedelta(years=FIRST_COLLECTING_DURATION)
                return fetching_date.strftime(DEFAULT_DATE_FORMAT)
            return fetching_date_str

        @task
        def fetch_and_upload_asos_data(_: str) -> str:
            """기상청 API 로 데이터 수집 후 S3 업로드"""
            # TODO 나중에 배포시에 변경될 예정입니다.
            # end_date = datetime(2025, 5, 31)
            # end_date = datetime.now() - timedelta(days=1)
            # collector = Collector(storage=storage, fetcher=AsosDataFetcher.create())
            # collector.collect_all_asos_data(start_date=start_date, end_date=end_date)
            # collector.upload_all_asos_data(with_index=False)
            return datetime(2025, 5, 31).strftime(DEFAULT_DATE_FORMAT)

        @task
        def update_last_fetching_date(new_end_date_str: str) -> str:
            """Variable 에 새로운 수집 날짜 저장"""
            Variable.set(KEY_LAST_FETCHING_DATE, new_end_date_str)
            return new_end_date_str

        # 마지막 수집 날짜 조회
        last_fetching_date = get_last_fetching_date()

        # 데이터 수집
        new_last_fetching_date = fetch_and_upload_asos_data(last_fetching_date)

        # 데이터 수집 날짜 업데이트
        return update_last_fetching_date(new_last_fetching_date)

    @task_group(group_id="data_preprocessing")
    def preprocess_data(load_date_str: str) -> None:
        """데이터 전처리 작업 그룹"""

        @task
        def generate_unique_subdirectory(prefix: str) -> str:
            """고유한 서브디렉토리 이름 생성"""
            return f"{prefix}-{uuid.uuid4()!s}"

        @task
        def impute_missing_values(raw_dataset_directory: str, subdirectory: str) -> str:
            """원본 데이터의 결측치가 보간 후 Cloud Storage 에 저장. 그 Key 반환"""
            raw_weather_df = AsosDataLoader(storage).load_weather_dataset_at(raw_dataset_directory)
            result = WeatherDataImputer().fit_transform(raw_weather_df).dropna()
            return storage.upload_preprocessed_df(
                result,
                filename="imputed-features.csv",
                sub_directory=subdirectory,
                err_msg="결측치를 보간한 데이터셋을 Cloud Storage 에 업로드하지 못했습니다.",
            )

        @task
        def label_dataset(dataset_storage_key: str, subdirectory: str) -> str:
            """날씨 레이블 추가 후 Cloud Storage 에 저장. 그 Key 반환"""
            imputed_df = storage.read_as_dataframe(dataset_storage_key)
            result = WeatherLabeler().fit_transform(imputed_df)
            return storage.upload_preprocessed_df(
                result,
                filename="labeled-features.csv",
                sub_directory=subdirectory,
                err_msg="날씨 레이블을 추가한 데이터셋을 Cloud Storage 에 업로드하지 못했습니다.",
            )

        @task
        def handle_outliers(dataset_storage_key: str, subdirectory: str) -> str:
            """수치형 변수에 대해 IQR 기반 이상치 처리 후 Cloud Storage 에 저장. 그 Key 반환"""
            labeled_df = storage.read_as_dataframe(dataset_storage_key)
            result = WeatherDataOutlierHandler().fit_transform(labeled_df)
            return storage.upload_preprocessed_df(
                result,
                filename="handled-features.csv",
                sub_directory=subdirectory,
                err_msg="이상치를 처리한 데이터셋을 Cloud Storage 에 업로드하지 못했습니다.",
            )

        @task
        def transform_features(dataset_storage_key: str, subdirectory: str) -> str:
            """feature 인코딩 처리 후 Cloud Storage 에 저장. 그 Key 반환"""
            preprocessed_df = storage.read_as_dataframe(dataset_storage_key)
            result = WeatherDataTransformer().fit_transform(preprocessed_df)
            return storage.upload_feature_df(
                result,
                filename="weather-features.csv",
                sub_directory=subdirectory,
                err_msg="인코딩한 데이터셋을 Cloud Storage 에 업로드하지 못했습니다.",
            )

        @task
        def save_feature_storage_key(feature_storage_key: str):
            """최종 전처리 결과의 Storage key 를 Variable 에 저장"""
            Variable.set(KEY_FEATURE_DATASET_STORAGE_KEY, feature_storage_key)
            _logger.info(f"Uploaded features, storage key: {feature_dataset_key}")

        unique_subdirectory = generate_unique_subdirectory(load_date_str)
        imputed_dataset_key = impute_missing_values(
            raw_dataset_directory=load_date_str,
            subdirectory=unique_subdirectory,
        )
        labeled_dataset_key = label_dataset(imputed_dataset_key, unique_subdirectory)
        handled_dataset_key = handle_outliers(labeled_dataset_key, unique_subdirectory)
        feature_dataset_key = transform_features(handled_dataset_key, unique_subdirectory)
        save_feature_storage_key(feature_dataset_key)

    preprocess_data(load_date_str=collect_asos_data())


data_pipeline_dag()
