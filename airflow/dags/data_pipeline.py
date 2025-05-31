# dags/weather_pipeline_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd

from src.data.loader import AsosDataLoader
from src.libs.storage import Storage
from src.data.imputer import WeatherDataImputer
from src.data.labeler import WeatherLabeler


def load_weather_data(**kwargs):
    storage = Storage.create()
    loader = AsosDataLoader(storage)
    df_dict = loader.load()
    total_df = pd.concat(list(df_dict.values()))
    kwargs['ti'].xcom_push(key='total_df', value=total_df)


def impute_missing_values(**kwargs):
    total_df = kwargs['ti'].xcom_pull(key='total_df', task_ids='load_data')
    imputer = WeatherDataImputer()
    df = imputer.transform(total_df)
    kwargs['ti'].xcom_push(key='transformed_df', value=df)


def add_weather_label(**kwargs):
    df = kwargs['ti'].xcom_pull(key='transformed_df', task_ids='impute')
    df['weather'] = df.apply(
        lambda row: WeatherLabeler(row).determine_weather_label().value,
        axis=1
    )
    print(df.head())  # 실제 운영에서는 저장도 필요함


with DAG(
    dag_id='weather_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['weather', 'pipeline']
) as dag:

    load_data = PythonOperator(
        task_id='load_data',
        python_callable=load_weather_data
    )

    impute = PythonOperator(
        task_id='impute',
        python_callable=impute_missing_values
    )

    label = PythonOperator(
        task_id='add_label',
        python_callable=add_weather_label
    )

    load_data >> impute >> label
