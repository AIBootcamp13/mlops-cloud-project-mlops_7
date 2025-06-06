from datetime import datetime

from config.default_args import get_dynamic_default_args
from tasks.data import prepare_data
from tasks.eval import evaluate
from tasks.test import test
from tasks.train import train

from airflow.decorators import dag, task
from src.utils.log import get_logger


TARGET_COLUMN = "weather"


_logger = get_logger("weather_automated_pipeline")

default_args = get_dynamic_default_args()

MODEL_NAMES = ["random_forest", "xgboost", "lightgbm"]


@dag(
    dag_id="weather_automated_pipeline",
    start_date=datetime(2025, 6, 1),
    schedule="@daily",
    catchup=False,
    tags=["weather", "ml-modeling"],
    default_args=default_args,
)
def automated_pipeline_dag():
    @task
    def get_experiment_name() -> str:
        from datetime import datetime

        from src.utils.config import DEFAULT_DATE_FORMAT

        date_str = datetime.now().strftime(DEFAULT_DATE_FORMAT)
        return f"{date_str}-weather-prediction-model"

    dataset_keys = prepare_data(432)
    experiment_name = get_experiment_name()

    train_results = train.partial(
        train_x_storage_key=dataset_keys["train_x"],
        train_y_storage_key=dataset_keys["train_y"],
        experiment_name=experiment_name,
    ).expand(model_name=MODEL_NAMES)

    eval_results = evaluate.partial(
        val_x_key=dataset_keys["val_x"],
        val_y_key=dataset_keys["val_y"],
        experiment_name=experiment_name,
    ).expand(model_artifact_ref=train_results)

    test.partial(
        test_x_key=dataset_keys["test_x"],
        test_y_key=dataset_keys["test_y"],
        experiment_name=experiment_name,
    ).expand(model_artifact_ref=eval_results)


automated_pipeline_dag()
