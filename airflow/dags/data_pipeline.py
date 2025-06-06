from datetime import datetime

from config.default_args import get_dynamic_default_args
from dateutil.relativedelta import relativedelta

from airflow.decorators import dag, task_group


default_args = get_dynamic_default_args()


@dag(
    dag_id="weather_data_pipeline",
    start_date=datetime(2025, 6, 1),
    schedule=relativedelta(months=3),
    catchup=False,
    tags=["weather", "data-engineering"],
    default_args=default_args,
)
def data_pipeline_dag():
    from src.utils.log import get_logger

    _logger = get_logger("weather_data_pipeline")

    @task_group(group_id="data_collection")
    def collect_asos_data() -> str:
        """데이터 수집 작업 그룹"""
        from tasks.collect import (
            fetch_and_upload_asos_data,
            get_last_fetching_date,
            update_last_fetching_date,
        )

        # 마지막 수집 날짜 조회
        last_fetching_date = get_last_fetching_date()

        # 데이터 수집
        new_last_fetching_date = fetch_and_upload_asos_data(last_fetching_date)
        _logger.info(f"Done fetching and uploading asos data; last_fetching_date: {last_fetching_date}")

        # 데이터 수집 날짜 업데이트
        return update_last_fetching_date(new_last_fetching_date)

    @task_group(group_id="data_preprocessing")
    def preprocess_data(load_date_str: str) -> None:
        """데이터 전처리 작업 그룹"""
        from tasks.preprocess import (
            generate_unique_subdirectory,
            handle_outliers,
            impute_missing_values,
            label_dataset,
            save_feature_storage_key,
            transform_features,
        )

        unique_subdirectory = generate_unique_subdirectory(load_date_str)
        imputed_dataset_key = impute_missing_values(
            raw_dataset_directory=load_date_str,
            subdirectory=unique_subdirectory,
        )
        _logger.info("Done imputing dataset.")

        labeled_dataset_key = label_dataset(imputed_dataset_key, unique_subdirectory)
        _logger.info("Done labeling dataset.")

        handled_dataset_key = handle_outliers(labeled_dataset_key, unique_subdirectory)
        _logger.info("Done handling outlier dataset.")

        feature_dataset_key = transform_features(handled_dataset_key, unique_subdirectory)
        _logger.info("Done transforming dataset.")

        save_feature_storage_key(feature_dataset_key)
        _logger.info("Done preprocessing!")

    preprocess_data(load_date_str=collect_asos_data())


data_pipeline_dag()
