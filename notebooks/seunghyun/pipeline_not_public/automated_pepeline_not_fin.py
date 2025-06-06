from datetime import datetime

import joblib
import wandb
from config.default_args import get_dynamic_default_args
from config.keys import KEY_FEATURE_DATASET_STORAGE_KEY
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor

from airflow.decorators import dag, task, task_group
from airflow.models import Variable
from src.libs.storage import Storage
from src.utils.log import get_logger


# 공통 설정
_logger = get_logger("weather_automated_pipeline")
default_args = get_dynamic_default_args()
storage = Storage.create()

# 하이퍼파라미터 설정 (한 곳에서 관리)
HYPERPARAMS = {
    "DecisionTree": {"max_depth": 5},
    "RandomForest": {"n_estimators": 100, "max_depth": 10},
    "XGBoost": {"n_estimators": 100, "learning_rate": 0.1},
    "LightGBM": {"n_estimators": 100, "learning_rate": 0.1},
}

# WandB 설정
WANDB_PROJECT = "weather_modeling"
WANDB_API_KEY = Variable.get("WANDB_API_KEY")


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
    def load_data():
        # Ncloud Storage 에서 전처리 완료된 데이터 불러오기
        key = Variable.get(KEY_FEATURE_DATASET_STORAGE_KEY)
        df = storage.read_as_dataframe(key)
        # weather 컬럼을 예측 대상 변수로 지정
        X = df.drop(columns=["weather"])
        y = df["weather"]
        return X, y

    @task_group(group_id="train_test_evaluate")
    def train_test_evaluate_group(data):
        X, y = data

        @task
        def train_and_evaluate(model_name: str, model_class, params: dict):
            # 6:2:2 비율로 데이터 분할 (train, val, test)
            X_trainval, X_test, y_trainval, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            X_train, X_val, y_train, y_val = train_test_split(X_trainval, y_trainval, test_size=0.25, random_state=42)

            # 모델 생성 및 교차 검증 수행
            model = model_class(**params)
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            cv_scores = cross_val_score(model, X_train, y_train, scoring="neg_root_mean_squared_error", cv=kf)
            _logger.info(f"[{model_name}] Cross-validated RMSE: {-cv_scores.mean():.4f}")

            # 전체 학습 후 테스트셋 평가
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            rmse = mean_squared_error(y_test, y_pred, squared=False)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            _logger.info(f"[{model_name}] Test RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")

            # WandB에 실험 기록 및 모델 업로드
            wandb.login(key=WANDB_API_KEY)
            run = wandb.init(project=WANDB_PROJECT, name=f"{model_name}_run", reinit=True)
            run.config.update(params)
            wandb.log({"RMSE": rmse, "MAE": mae, "R2": r2})

            # 모델 저장 및 업로드
            model_path = f"{model_name}_model.pkl"
            joblib.dump(model, model_path)
            storage.upload_model(model_path, f"models/{model_name}_model.pkl")
            wandb.save(model_path)
            run.finish()

        # 4개 모델 순차 실행
        train_and_evaluate.override(task_id="decision_tree")(
            model_name="DecisionTree", model_class=DecisionTreeRegressor, params=HYPERPARAMS["DecisionTree"]
        )
        train_and_evaluate.override(task_id="random_forest")(
            model_name="RandomForest", model_class=RandomForestRegressor, params=HYPERPARAMS["RandomForest"]
        )
        train_and_evaluate.override(task_id="xgboost")(
            model_name="XGBoost", model_class=XGBRegressor, params=HYPERPARAMS["XGBoost"]
        )
        train_and_evaluate.override(task_id="lightgbm")(
            model_name="LightGBM", model_class=LGBMRegressor, params=HYPERPARAMS["LightGBM"]
        )

    # 전체 실행 순서: 데이터 불러오기 ➝ 학습/평가 수행
    data = load_data()
    train_test_evaluate_group(data=data)


automated_pipeline_dag()
