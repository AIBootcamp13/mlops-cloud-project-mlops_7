from datetime import datetime

from config.default_args import get_dynamic_default_args
from tasks.data import prepare_data
from tasks.eval import evaluate
from tasks.save_best_model import save_best_model
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
        from src.utils.config import DEFAULT_DATE_FORMAT

        current = datetime.now()
        date_str = current.strftime(DEFAULT_DATE_FORMAT)
        return f"{date_str}-{current.microsecond}-{model}"

    # 각 모델의 test task를 저장할 리스트
    test_tasks = []

    for model_name in MODEL_NAMES:
        with TaskGroup(group_id=f"model_{model_name}"):
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

            test_result = test(
                test_x_key=dataset_keys["test_x"],
                test_y_key=dataset_keys["test_y"],
                experiment_name=experiment_name,
                model_artifact_ref=eval_result,
            )

            test_tasks.append(test_result)

    @task
    def get_combined_experiment_name() -> str:
        from src.utils.config import DEFAULT_DATE_FORMAT

        current = datetime.now()
        date_str = current.strftime(DEFAULT_DATE_FORMAT)
        return f"{date_str}-{current.microsecond}-model_selection"

    # save_best_model이 모든 test_tasks가 끝난 후 실행되도록 의존성 설정
    best_model = save_best_model(
        experiment_name=get_combined_experiment_name(),
        model_names=MODEL_NAMES,
    )
    for t in test_tasks:
        t >> best_model


automated_pipeline_dag()
