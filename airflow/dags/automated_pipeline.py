from datetime import datetime

from config.default_args import KEY_FEATURE_DATASET_STORAGE_KEY, get_dynamic_default_args

from airflow.decorators import dag, task
from airflow.models import Variable
from src.libs.storage import Storage
from src.utils.log import get_logger


TARGET_COLUMN = "weather"

default_args = get_dynamic_default_args()
_logger = get_logger("weather_automated_pipeline")


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
    def prepare_data(random_state: int) -> dict[str, str]:
        """
        dataset 을 훈련(60%), 검증(20%), 테스트(20%)로 나눠서
        Cloud Storage 에 저장하고, 그 key 들을 반환
        """
        import uuid
        from pathlib import Path

        from sklearn.model_selection import train_test_split

        storage = Storage.create()
        feature_storage_key = Variable.get(KEY_FEATURE_DATASET_STORAGE_KEY)
        features = storage.read_as_dataframe(feature_storage_key)

        x = features.drop(TARGET_COLUMN, axis=1)
        y = features[TARGET_COLUMN]

        # 1단계: 데이터를 훈련 + 검증 세트와 테스트 세트로 분할 (80% 대 20%)
        train_val_x, test_x, train_val_y, test_y = train_test_split(x, y, test_size=0.2, random_state=random_state)

        # 2단계: 훈련 + 검증 세트를 훈련 세트와 검증 세트로 분할 (75% 대 25%)
        train_x, val_x, train_y, val_y = train_test_split(
            train_val_x, train_val_y, test_size=0.25, random_state=random_state
        )

        # 최종적으로, 원래 데이터의 60% 가 훈련 세트, 20% 가 검증 세트, 20% 가 테스트 세트
        dfs = {
            "train_x": train_x,
            "val_x": val_x,
            "test_x": test_x,
            "train_y": train_y,
            "val_y": val_y,
            "test_y": test_y,
        }
        result = {}
        sub_directory = f"{Path(feature_storage_key).parent.name}/split-{uuid.uuid4()}"
        for dataset_name, df in dfs.items():
            storage_key = storage.upload_feature_df(df, filename=dataset_name, sub_directory=sub_directory)
            result[dataset_name] = storage_key
        return result

    @task
    def train(train_x_key: str, train_y_key: str, experiment_name: str) -> dict:
        """모델 학습"""
        from src.models.random_forest import RandomForestModel
        from src.tracker.wandb import WandbTracker

        storage = Storage.create()
        train_x = storage.read_as_dataframe(train_x_key)
        train_y = storage.read_as_dataframe(train_y_key).to_numpy().ravel()

        tracker = WandbTracker.create()
        model_params = RandomForestModel.default_params()

        tracker.start_experiment(
            experiment_name=experiment_name,
            params=model_params,
            job_type="training",
        )
        experiment_id = tracker.get_run_id()

        model = RandomForestModel(model_params)
        _logger.info(f"Train ML Model: {model.name}; train_x: {train_x.shape}, train_y: {train_y.shape}")
        model.fit(train_x, train_y)

        model_artifact_ref = tracker.register_model(
            model,
            model_name="random-forest",
            metadata={
                "framework": "sklearn",
                "datasets": {
                    "storage": {
                        "name": "ncloud",
                        "bucket": storage.bucket,
                        "train_x": train_x_key,
                        "train_y": train_y_key,
                    }
                },
                "params": model_params,
            },
        )

        tracker.end_experiment()
        return {"experiment_id": experiment_id, "model_artifact_ref": model_artifact_ref}

    @task
    def evaluate(val_x_key: str, val_y_key: str, experiment_id: str, model_artifact_ref: str) -> dict:
        """모델 평가"""
        from src.evaluation.metrics import evaluate_model
        from src.tracker.wandb import WandbTracker

        _logger.info(f"Evaluate Trained ML Model; model_reference: {model_artifact_ref}")

        storage = Storage.create()
        val_x = storage.read_as_dataframe(val_x_key)
        val_y = storage.read_as_dataframe(val_y_key).to_numpy().ravel()

        tracker = WandbTracker.create()
        tracker.resume_experiment(experiment_id, job_type="evaluation")

        model = tracker.load_model(model_artifact_ref)
        pred_y = model.predict(val_x)
        metrics = evaluate_model(val_y, pred_y)

        tracker.log_metrics(metrics)

        tracker.end_experiment()

        return {"experiment_id": experiment_id, "model_artifact_ref": model_artifact_ref}

    @task
    def test(test_x_key: str, test_y_key: str, experiment_id: str, model_artifact_ref: str) -> dict:
        """모델 검증"""
        from src.evaluation.metrics import evaluate_model
        from src.tracker.wandb import WandbTracker

        _logger.info(f"Test Trained ML Model; model_reference: {model_artifact_ref}")

        storage = Storage.create()
        test_x = storage.read_as_dataframe(test_x_key)
        test_y = storage.read_as_dataframe(test_y_key).to_numpy().ravel()

        tracker = WandbTracker.create()
        tracker.resume_experiment(experiment_id, job_type="test")

        model = tracker.load_model(model_artifact_ref)

        pred_y = model.predict(test_x)
        metrics = evaluate_model(test_y, pred_y)
        tracker.log_metrics(metrics)

        tracker.end_experiment()
        return {"experiment_id": experiment_id, "model_artifact_ref": model_artifact_ref}

    @task
    def save_model(model_artifact_ref: str):
        """ML Model 을 Model Registry 에 저장"""
        _logger.info(f"Save Trained ML Model; {model_artifact_ref}")
        # TODO 학습된 모델을 inference server 에서 가져갈 수 있도록 저장합니다.

    dataset_keys = prepare_data(432)
    result = train(
        train_x_key=dataset_keys["train_x"],
        train_y_key=dataset_keys["train_y"],
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
    save_model(result["model_artifact_ref"])


automated_pipeline_dag()
