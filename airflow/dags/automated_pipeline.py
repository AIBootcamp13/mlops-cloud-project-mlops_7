from datetime import datetime
from airflow.decorators import dag, task
from airflow.models import Variable
import wandb

from config.default_args import get_dynamic_default_args, KEY_FEATURE_DATASET_STORAGE_KEY
from src.utils.config import WANDB_ENTITY, WANDB_PROJECT

from src.utils.log import get_logger
from src.libs.storage import Storage
from src.models.prepared_data import PreparedData
from src.models.trainer import Trainer
from src.models.validator import Validator
from src.models.evaluator import Evaluator
from src.models.save_model import WeatherModelSaver

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
    storage = Storage.create()

    @task
    def run_pipeline():
        # WandB 초기화
        wandb.init(
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
            job_type="weather_ml_pipeline",
            config={"pipeline": "weather_prediction"}
        )

        # Step 1. Load Dataset
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

    run_pipeline()


automated_pipeline_dag()