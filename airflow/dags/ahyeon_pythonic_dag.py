from airflow.decorators import dag, task
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

from src.data.loader import AsosDataLoader
from src.libs.storage import Storage
from src.data.imputer import WeatherDataImputer
from src.data.labeler import WeatherLabeler

# DAG 정의
@dag(
    default_args={
    'owner': 'ahyeon',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    },
    dag_id='data_pipeline_pythonic_ahyeon',
    start_date=datetime(2025, 5, 29),
    schedule_interval=relativedelta(months=3),
    catchup=False,
    tags=['weather Predictor'],
)
def data_pipeline():

    @task()
    def load_and_merge_data():
        storage = Storage.create()
        loader = AsosDataLoader(storage)
        df_per_station = loader.load()
        total_df = pd.concat(list(df_per_station.values()))
        total_df.to_csv('/opt/project/src/data/raw_dataset.csv', index=False)

    @task()
    def preprocess_null_data():
        total_df = pd.read_csv('/opt/project/src/data/raw_dataset.csv')
        imputer = WeatherDataImputer()
        transformed_df = imputer.transform(total_df)
        transformed_df.to_csv('/opt/project/src/data/imputed_dataset.csv', index=False)

    @task()
    def labeling_data():
        transformed_df = pd.read_csv('/opt/project/src/data/imputed_dataset.csv')
        transformed_df["weather"] = transformed_df.apply(
            lambda row: WeatherLabeler(row).determine_weather_label().value, axis=1
        )
        transformed_df.to_csv('/opt/project/src/data/plus_label_dataset.csv', index=False)

    # Task 연결
    task1 = load_and_merge_data()
    task2 = preprocess_null_data()
    task3 = labeling_data()

    task1 >> task2 >> task3

# DAG 객체 인스턴스화
data_pipeline()