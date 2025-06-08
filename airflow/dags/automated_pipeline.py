from datetime import datetime
import os

from config.default_args import get_dynamic_default_args
from tasks.data import prepare_data
from tasks.eval import evaluate
from tasks.test import test
from tasks.train import train

from airflow.decorators import dag, task
from airflow.utils.task_group import TaskGroup


default_args = get_dynamic_default_args()

MODEL_NAMES = ["random_forest", "lightgbm", "xgboost"]


@dag(
    dag_id="weather_automated_pipeline",
    start_date=datetime(2025, 6, 1),
    schedule="@daily",
    catchup=False,
    tags=["weather", "ml-modeling"],
    default_args=default_args,
)
def automated_pipeline_dag():
    dataset_keys = prepare_data()

    @task
    def get_experiment_name(model: str) -> str:
        from datetime import datetime

        from src.utils.config import DEFAULT_DATE_FORMAT

        current = datetime.now()
        date_str = current.strftime(DEFAULT_DATE_FORMAT)
        return f"{date_str}-{current.microsecond}-{model}"

    for model_name in MODEL_NAMES:
        with TaskGroup(group_id=f"model_{model_name}") as _:
            experiment_name = get_experiment_name(model_name)

            train_result = train(
                train_x_storage_key=dataset_keys["train_x"],
                train_y_storage_key=dataset_keys["train_y"],
                experiment_name=experiment_name,
                model_name=model_name,
            )

            eval_result = evaluate(
                val_x_key=dataset_keys["val_x"],
                val_y_key=dataset_keys["val_y"],
                experiment_name=experiment_name,
                model_artifact_ref=train_result,
            )

            test(
                test_x_key=dataset_keys["test_x"],
                test_y_key=dataset_keys["test_y"],
                experiment_name=experiment_name,
                model_artifact_ref=eval_result,
            )

    @task
    def save_model() -> None:
        import wandb

        """모델들 WANDB에 저장"""
        run = wandb.init(
            project="ml-ops-practice2",
            name="Trained_XGBoost",
            job_type="save",
            config={}
        )
        artifact = wandb.Artifact("XGBoost", type="model")

        artifact.metadata = {
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_name": train_result.model_name
        }

        artifact.add_file(train_result.model)

        run.log_artifact(artifact)
        run.finish()



automated_pipeline_dag()
