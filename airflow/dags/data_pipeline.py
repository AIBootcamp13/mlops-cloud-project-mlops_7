from datetime import datetime, timedelta

import pandas as pd

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from src.data.collector import Collector
from src.data.handler import WeatherDataOutlierHandler
from src.data.imputer import WeatherDataImputer
from src.data.labeler import WeatherLabeler
from src.data.loader import AsosDataLoader
from src.data.transformer import WeatherDataTransformer
from src.libs.storage import Storage
from src.libs.weather.fetcher import AsosDataFetcher


# ------------------------
# 데이터 수집
# ------------------------


def get_last_loaded_date(**kwargs):
    """Variable에서 마지막 수집 날짜 조회 / 없으면 5년 전으로 초기화"""
    last = Variable.get("weather_last_loaded", default_var=None)
    if last is None:
        last = (datetime.today() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
    kwargs["ti"].xcom_push(key="last_loaded_date", value=last)


def collector_weather_data(**kwargs):
    """ASOS API로 데이터 수집 후 S3 업로드"""
    last_loaded_date = kwargs["ti"].xcom_pull(key="last_loaded_date", task_ids="get_last_date")
    start_dt = datetime.strptime(last_loaded_date, "%Y-%m-%d")
    end_dt = datetime.today() - timedelta(days=1)  # API는 어제까지 데이터 제공

    fetcher = AsosDataFetcher.create()
    storage = Storage.create()

    collector = Collector(storage, fetcher)
    collector.collect_all_asos_data(start_date=start_dt, end_date=end_dt)
    uploaded_keys = collector.upload_all_asos_data()

    print(f"업로드 완료된 파일 수: {len(uploaded_keys)}")

    kwargs["ti"].xcom_push(key="new_last_date", value=end_dt.strftime("%Y-%m-%d"))


def update_last_loaded_date(**kwargs):
    """Variable에 새로운 수집 날짜 저장"""
    new_date = kwargs["ti"].xcom_pull(key="new_last_date", task_ids="collector_data")
    Variable.set("weather_last_loaded", new_date)


# ------------------------
# 데이터 적재
# ------------------------


def load_weather_data(**kwargs):
    """S3에서 CSV 불러와 DataFrame으로 합치기"""
    storage = Storage.create()
    loader = AsosDataLoader(storage)
    df_dict = loader.load()
    total_df = pd.concat(list(df_dict.values()))
    kwargs["ti"].xcom_push(key="total_df", value=total_df)


# ------------------------
# 전처리 단계
# ------------------------


def impute_missing_values(**kwargs):
    """결측치 보간"""
    total_df = kwargs["ti"].xcom_pull(key="total_df", task_ids="load_data")
    imputer = WeatherDataImputer()
    imputed_df = imputer.transform(total_df)
    kwargs["ti"].xcom_push(key="imputed_df", value=imputed_df)


def add_weather_labeler(**kwargs):
    """날씨 레이블 추가"""
    imputed_df = kwargs["ti"].xcom_pull(key="imputed_df", task_ids="imputer")

    labeler = WeatherLabeler()
    labeled_df = labeler.fit_transform(imputed_df)

    kwargs["ti"].xcom_push(key="labeled_df", value=labeled_df)


def handle_outliers(**kwargs):
    """수치형 변수에 대해 IQR 기반 이상치 처리"""
    labeled_df = kwargs["ti"].xcom_pull(key="labeled_df", task_ids="labeler")

    handler = WeatherDataOutlierHandler()
    handled_df = handler.fit_transform(labeled_df)

    kwargs["ti"].xcom_push(key="handled_df", value=handled_df)


def transform_features(**kwargs):
    """피처 인코딩 처리"""
    handled_df = kwargs["ti"].xcom_pull(key="handled_df", task_ids="handler")

    transformer = WeatherDataTransformer()
    final_df = transformer.fit_transform(handled_df)

    kwargs["ti"].xcom_push(key="final_df", value=final_df)


def save_preprocessed_data(**kwargs):
    """최종 전처리 결과를 S3에 저장"""

    final_df = kwargs["ti"].xcom_pull(key="final_df", task_ids="transformer")

    storage = Storage.create()
    today_str = datetime.today().strftime("%Y%m%d")
    file_key = f"preprocessed/preprocessed_weather_data_{today_str}.csv"

    # S3에 저장
    storage.save_df(final_df, file_key)
    print(f"[✔] S3 저장 완료 → {file_key}")


# ------------------------
# DAG 정의
# ------------------------

with DAG(
    dag_id="weather_pipeline",
    start_date=datetime(2025, 5, 30),
    schedule="@daily",
    catchup=False,
    tags=["weather", "variable"],
) as dag:
    get_last_date = PythonOperator(task_id="get_last_date", python_callable=get_last_loaded_date)

    collector_data = PythonOperator(task_id="collector_data", python_callable=collector_weather_data)

    update_variable = PythonOperator(task_id="update_last_date", python_callable=update_last_loaded_date)

    load_data = PythonOperator(task_id="load_data", python_callable=load_weather_data)

    imputer = PythonOperator(task_id="imputer", python_callable=impute_missing_values)

    labeler = PythonOperator(task_id="labeler", python_callable=add_weather_labeler)

    handler = PythonOperator(task_id="handler", python_callable=handle_outliers)

    transformer = PythonOperator(task_id="transformer", python_callable=transform_features)

    saver = PythonOperator(task_id="save_result", python_callable=save_preprocessed_data)

    # DAG 실행 순서
    (
        get_last_date
        >> collector_data
        >> update_variable
        >> load_data
        >> imputer
        >> labeler
        >> handler
        >> transformer
        >> saver
    )
    # load_data >> imputer >> labeler >> handler >> transformer
