from config.keys import KEY_FEATURE_DATASET_STORAGE_KEY

from airflow.decorators import task
from airflow.models import Variable


@task
def generate_unique_subdirectory(prefix: str) -> str:
    """고유한 서브디렉토리 이름 생성"""
    import uuid

    return f"{prefix}-{uuid.uuid4()!s}"


@task
def impute_missing_values(raw_dataset_directory: str, subdirectory: str) -> str:
    """원본 데이터의 결측치가 보간 후 Cloud Storage 에 저장. 그 Key 반환"""
    from src.data.imputer import WeatherDataImputer
    from src.data.loader import AsosDataLoader
    from src.libs.storage import Storage

    storage = Storage.create()

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
    from src.data.labeler import WeatherLabeler
    from src.libs.storage import Storage

    storage = Storage.create()

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
    from src.data.handler import WeatherDataOutlierHandler
    from src.libs.storage import Storage

    storage = Storage.create()

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
    from src.data.transformer import WeatherDataTransformer
    from src.libs.storage import Storage

    storage = Storage.create()

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
