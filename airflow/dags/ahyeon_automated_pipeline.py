from datetime import datetime
import joblib
import pandas as pd
import wandb
import os

from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression

from config.default_args import KEY_FEATURE_DATASET_STORAGE_KEY, get_dynamic_default_args, X_TRAIN_KEY, Y_TRAIN_KEY, X_VAL_KEY, Y_VAL_KEY, X_TEST_KEY, Y_TEST_KEY

from airflow.decorators import dag, task
from airflow.models import Variable
from src.libs.storage import Storage
from src.utils.log import get_logger
from src.utils.config import DEFAULT_DATE_FORMAT


FIRST_COLLECTING_DURATION = 5  # 연단위

default_args = get_dynamic_default_args()

_logger = get_logger("ahyeon_weather_automated_pipeline")

MODEL_SAVE_DIR = "/opt/airflow/models"

@dag(
    dag_id="ahyeon_weather_automated_pipeline",
    start_date=datetime(2025, 6, 1),
    schedule="@daily",
    catchup=False,
    tags=["weather", "ml-modeling"],
    default_args=default_args,
)
def automated_pipeline_dag():
    storage = Storage.create()

    @task
    def load_features_and_split() -> None:
        """데이터 준비 및 분할"""
        feature_storage_key = Variable.get(KEY_FEATURE_DATASET_STORAGE_KEY)
        features = storage.read_as_dataframe(feature_storage_key)
        _logger.info(f"Train Features; shape: {features.shape}")

        x = features.drop(columns=["weather"])
        y = features["weather"]

        x_train, x_temp, y_train, y_temp = train_test_split(x, y, test_size=0.2, stratify=y, random_state=42)
        x_val, x_test, y_val, y_test = train_test_split(x_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)

        sub_directory = datetime(2025, 5, 31).strftime(DEFAULT_DATE_FORMAT)

        data_map = {
            X_TRAIN_KEY: ("x_train.csv", x_train),
            Y_TRAIN_KEY: ("y_train.csv", y_train),
            X_VAL_KEY: ("x_val.csv", x_val),
            Y_VAL_KEY: ("y_val.csv", y_val),
            X_TEST_KEY: ("x_test.csv", x_test),
            Y_TEST_KEY: ("y_test.csv", y_test),
        }

        for var_key, (filename, df) in data_map.items():
            storage_key = storage.make_csv_key_in_features(filename, sub_directory)
            if not storage.upload_dataframe(df, key=storage_key):
                raise RuntimeError(f"{filename} 업로드 실패")
            
            Variable.set(var_key, storage_key)

    @task
    def train_and_save_models() -> list[str]:
        """모델 학습 및 저장"""
        x_key = Variable.get(X_TRAIN_KEY)
        y_key = Variable.get(Y_TRAIN_KEY)

        x_train = storage.read_as_dataframe(x_key)
        y_train = storage.read_as_dataframe(y_key)

        _logger.info(f"Loaded x_train, y_train Datasets")

        models = {
            "rf": RandomForestClassifier(),
            "xgb": XGBClassifier(),
            "lgbm": LGBMClassifier(),
            "lr": LogisticRegression()
        }

        os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
        model_paths = []

        for name, model in models.items():
            run = wandb.init(
                project = "weather-prediction",
                name = f"{name}_train",
                job_type = "train",
                config = model.get_params(),
                reinit = True
            )
            model.fit(x_train, y_train)
            model_path = f"{MODEL_SAVE_DIR}/{name}_model.pkl"
            joblib.dump(model, model_path)
            model_paths.append(model_path)

            run.finish()

        _logger.info(f"Saved Trained Models")

        return model_paths

    @task
    def evaluate(paths: list[str]) -> None:
        """모델 검증 및 성능 기록"""
        x_key = Variable.get(X_VAL_KEY)
        y_key = Variable.get(Y_VAL_KEY)

        x_val = storage.read_as_dataframe(x_key)
        y_val = storage.read_as_dataframe(y_key)

        _logger.info(f"Loaded x_val, y_val Datasets")

        for path in paths:
            name = os.path.basename(path).replace("_model.pkl", "")
            model = joblib.load(f"{MODEL_SAVE_DIR}/{name}_model.pkl")
            preds = model.predict(x_val)
            
            acc = accuracy_score(y_val, preds)
            precision = precision_score(y_val, preds, average='macro', zero_division=0)
            recall = recall_score(y_val, preds, average='macro', zero_division=0)
            f1 = f1_score(y_val, preds, average='macro', zero_division=0)

            # W&B 기록
            run = wandb.init(
                project = "weather-prediction",
                name = f"{name}_eval",
                job_type = "eval",
                config = {"model_name": name},
                reinit = True
            )
            wandb.log({
                "val_accuracy": acc,
                "val_precision_macro": precision,
                "val_recall_macro": recall,
                "val_f1_macro": f1
            })
            run.finish()

        _logger.info("Evaluated Trained Models")

    @task
    def test(paths: list[str]) -> None:
        """모델 평가 및 성능 기록"""
        x_key = Variable.get(X_TEST_KEY)
        y_key = Variable.get(Y_TEST_KEY)

        x_test = storage.read_as_dataframe(x_key)
        y_test = storage.read_as_dataframe(y_key)

        _logger.info(f"Loaded x_test, y_test Datasets")

        
        for path in paths:
            name = os.path.basename(path).replace("_model.pkl", "")
            model = joblib.load(f"{MODEL_SAVE_DIR}/{name}_model.pkl")
            preds = model.predict(x_test)
            
            acc = accuracy_score(y_test, preds)
            precision = precision_score(y_test, preds, average='macro', zero_division=0)
            recall = recall_score(y_test, preds, average='macro', zero_division=0)
            f1 = f1_score(y_test, preds, average='macro', zero_division=0)

            # W&B 기록
            run = wandb.init(
                project="weather-prediction",
                name=f"{name}_test",
                job_type="test",
                config={"model_name": name},
                reinit=True
            )
            wandb.log({
                "test_accuracy": acc,
                "test_precision_macro": precision,
                "test_recall_macro": recall,
                "test_f1_macro": f1
            })
            run.finish()

        _logger.info("Tested Trained Models")

    @task
    def save_model(paths: list[str]) -> None:
        """모델들 WANDB에 저장"""
        run = wandb.init(
            project="weather-prediction",
            name="save_all_model",
            job_type="save",
            config={"num_models": len(paths)}
        )
        artifact = wandb.Artifact("all_models", type="model")

        artifact.metadata = {
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_names": [os.path.basename(p).replace("_model.pkl", "") for p in paths]
        }

        for path in paths:
            name = os.path.basename(path).replace("_model.pkl", "")
            artifact.add_file(path, name=f"{name}_model.pkl")

        run.log_artifact(artifact)
        run.finish()
        
        _logger.info("Saved All Trained Models")

    loaded = load_features_and_split()
    paths = train_and_save_models()
    evaluated = evaluate(paths)
    tested = test(paths)
    saved = save_model(paths)

    loaded >> paths >> evaluated >> tested >> saved

automated_pipeline_dag()