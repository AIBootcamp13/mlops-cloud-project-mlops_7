from datetime import datetime

from config.default_args import KEY_FEATURE_DATASET_STORAGE_KEY, get_dynamic_default_args

from airflow.decorators import dag, task
from airflow.models import Variable
from src.libs.storage import Storage
from src.utils.log import get_logger


FIRST_COLLECTING_DURATION = 5  # 연단위

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
    storage = Storage.create()

    @task
    def train():
        """모델 학습"""
        # 데이터 준비
        feature_storage_key = Variable.get(KEY_FEATURE_DATASET_STORAGE_KEY)
        features = storage.read_as_dataframe(feature_storage_key)
        _logger.info(f"Train Features; shape: {features.shape}")
        # TODO 모델 학습하고 반환하는 로직을 작성합니다.

    @task
    def test():
        """모델 검증"""
        _logger.info("Evaluate Trained ML Model")
        # TODO 학습된 모델을 test dataset 으로 평가하는 로직을 작성합니다.

    @task
    def evaluate():
        """모델 평가"""
        _logger.info("Test Trained ML Model with Validation Dataset")
        # TODO 학습된 모델을 validation dataset 으로 평가하는 로직을 작성합니다.

    @task
    def save_model():
        """ML Model 을 Model Registry 에 저장"""
        _logger.info("Save Trained ML Model")
        # TODO 학습된 모델을 Model Registry 인 wandb 에 저장하는 로직을 작성합니다.

    train()
    test()
    evaluate()
    save_model()


automated_pipeline_dag()
