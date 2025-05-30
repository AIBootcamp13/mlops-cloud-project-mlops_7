from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

from src.data.loader import AsosDataLoader
from src.libs.storage import Storage
from src.data.imputer import WeatherDataImputer
from src.data.labeler import WeatherLabeler

with DAG(
    default_args = {
    'owner': 'ahyeon',
    'depends_on_past': False,                    # 현재 Task 실행이 이전 실행의 성공 여부에 의존하느냐
    'retries': 1,                                # 해당 Task가 실패했을 때 재시도할 최대 횟수
    'retry_delay': timedelta(minutes=5),
    },
    dag_id='data_pipeline_ahyeon',
    start_date=datetime(2025, 5, 29),            # DAG 실행 주기의 기준 시작 날짜
    schedule_interval=relativedelta(months=3),  
    catchup=False,                               # 과거 누락된 주기를 실행할 것인지 결정
    tags=['weather Predictor'],
) as dag:

    # 지점별 데이터를 불러오고 병합하여 csv 파일 저장
    def load_and_merge_data(**context):
        storage = Storage.create()
        loader = AsosDataLoader(storage)
        df_per_station = loader.load()
        total_df = pd.concat(list(df_per_station.values()))
        total_df.to_csv('/opt/project/src/data/raw_dataset.csv', index=False)

    # 병합된 데이터의 결측치 처리 후 csv 파일 저장
    def preprocess_null_data(**context):
        total_df = pd.read_csv('/opt/project/src/data/raw_dataset.csv')
        imputer = WeatherDataImputer()
        transformed_df = imputer.transform(total_df)
        transformed_df.to_csv('/opt/project/src/data/imputed_dataset.csv', index=False)

    # 결측치 처리 된 병합 데이터에 날씨 label 추가한 csv 파일 저장
    def labeling_data(**context):
        transformed_df = pd.read_csv('/opt/project/src/data/imputed_dataset.csv')
        transformed_df["weather"] = transformed_df.apply(
            lambda row: WeatherLabeler(row).determine_weather_label().value, axis=1
        )
        transformed_df.to_csv('/opt/project/src/data/plus_label_dataset.csv', index=False)
        
    data_load_task = PythonOperator(
        task_id='data_load_task',
        python_callable=load_and_merge_data,
    )

    preprocess_null_task = PythonOperator(
        task_id='preprocess_null_task',
        python_callable=preprocess_null_data,
    )

    labeling_task = PythonOperator(
        task_id='labeling_task',
        python_callable=labeling_data,
    )

    data_load_task >> preprocess_null_task >> labeling_task
