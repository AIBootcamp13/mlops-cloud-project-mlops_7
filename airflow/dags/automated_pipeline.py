from datetime import datetime

import wandb
from config.default_args import KEY_FEATURE_DATASET_STORAGE_KEY, get_dynamic_default_args
from tasks.data import prepare_data
from tasks.eval import evaluate
from tasks.test import test
from tasks.train import train

from airflow.decorators import dag, task
from airflow.models import Variable
from src.libs.storage import Storage
from src.models.evaluator import Evaluator
from src.models.prepared_data import PreparedData
from src.models.save_model import WeatherModelSaver
from src.models.trainer import Trainer
from src.models.validator import Validator
from src.utils.config import WANDB_ENTITY, WANDB_PROJECT
from src.utils.log import get_logger


TARGET_COLUMN = "weather"


_logger = get_logger("weather_automated_pipeline")

default_args = get_dynamic_default_args()


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
    def generate_experiment_name() -> str:
        from datetime import datetime

        from src.utils.config import DEFAULT_DATE_FORMAT

        date_str = datetime.now().strftime(DEFAULT_DATE_FORMAT)
        return f"{date_str}-weather-prediction-model"

    @task
    def choose_best_model(model_artifact_ref: str):
        """ML Model 을 Model Registry 에 저장"""
        _logger.info(f"Save Trained ML Model; {model_artifact_ref}")
        # TODO 학습된 모델을 inference server 에서 가져갈 수 있도록 저장합니다.

    @task
    def run_pipeline():
        # WandB 초기화
        wandb.init(
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
            job_type="weather_ml_pipeline",
            config={"pipeline": "weather_prediction"},
        )

        # Step 1. Load Dataset
        storage = Storage.create()
        feature_storage_key = Variable.get(KEY_FEATURE_DATASET_STORAGE_KEY)
        df = storage.read_as_dataframe(feature_storage_key)
        _logger.info(f"Feature data loaded from: {feature_storage_key}, shape={df.shape}")

        # Step 2. 데이터 분할
        splitter = PreparedData()
        train_df, val_df, test_df = splitter.split_dataset(df)  # 올바른 메서드명

        X_train, y_train = splitter.prepare_features_target(train_df)
        X_val, y_val = splitter.prepare_features_target(val_df)
        X_test, y_test = splitter.prepare_features_target(test_df)

        # Step 3. 모델 학습
        trainer = Trainer()
        trained_models = trainer.train_all_models(X_train, y_train)

        # Step 4. 모델 검증
        validator = Validator()
        validation_results = validator.validate_all_models(trained_models, X_val, y_val)

        # Step 5. 모델 평가
        evaluator = Evaluator()
        evaluation_results = evaluator.evaluate_all_models(trained_models, X_test, y_test)

        # Step 6. 모든 모델 저장
        saver = WeatherModelSaver()
        saved_artifacts = saver.save_all_models(evaluation_results)

        wandb.finish()
        _logger.info(f"Pipeline completed. Saved models: {list(saved_artifacts.keys())}")

    dataset_keys = prepare_data(432)
    result = train(
        train_x_storage_key=dataset_keys["train_x"],
        train_y_storage_key=dataset_keys["train_y"],
        experiment_name=generate_experiment_name(),
    )
    result = evaluate(
        val_x_key=dataset_keys["val_x"],
        val_y_key=dataset_keys["val_y"],
        experiment_id=result["experiment_id"],
        model_artifact_ref=result["model_artifact_ref"],
    )
    result = test(
        test_x_key=dataset_keys["test_x"],
        test_y_key=dataset_keys["test_y"],
        experiment_id=result["experiment_id"],
        model_artifact_ref=result["model_artifact_ref"],
    )
    choose_best_model(result["model_artifact_ref"])


automated_pipeline_dag()
