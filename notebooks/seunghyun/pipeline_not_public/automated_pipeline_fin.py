from datetime import datetime
import numpy as np
import pandas as pd
import joblib
import wandb
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from airflow.decorators import dag, task, task_group
from airflow.models import Variable
from config.default_args import KEY_FEATURE_DATASET_STORAGE_KEY, get_dynamic_default_args
from src.libs.storage import Storage
from src.utils.log import get_logger

# 공통 설정: 로거, 기본 인자, 스토리지 인스턴스 생성
_logger = get_logger("weather_automated_pipeline")
default_args = get_dynamic_default_args()
storage = Storage.create()

# 모델별 하이퍼파라미터 설정
HYPERPARAMS = {
    "DecisionTree": {"max_depth": 7},
    "RandomForest": {"n_estimators": 30, "max_depth": 5},
    "XGBoost": {"n_estimators": 75, "learning_rate": 0.1},
    "LightGBM": {"n_estimators": 75, "learning_rate": 0.1}
}

# Weights & Biases 설정
WANDB_PROJECT = "weather_modeling"
WANDB_API_KEY = Variable.get("WANDB_API_KEY")

# DAG 정의
@dag(
    dag_id="weather_automated_pipeline_optimized",
    start_date=datetime(2025, 6, 1),
    schedule="@daily",
    catchup=False,
    tags=["weather", "ml-modeling"],
    default_args=default_args,
)
def optimized_pipeline_dag():

    @task
    def load_data():
        # 저장소에서 전처리된 데이터를 로드하고 feature/target 분리
        key = Variable.get(KEY_FEATURE_DATASET_STORAGE_KEY)
        df = storage.read_as_dataframe(key)
        X = df.drop(columns=["weather"])
        y = df["weather"]
        return X, y

    @task_group(group_id="train_with_kfold")
    def train_models_with_kfold(data):
        X, y = data

        @task
        def train_model(model_name: str, model_class, params: dict):
            # 6:2:2 비율로 데이터 분할
            X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.25, random_state=42)
            
            # 훈련용 데이터셋 전체 : K-Fold 수행용 데이터셋 생성
            X_trainval = pd.concat([X_train, X_val])
            y_trainval = pd.concat([y_train, y_val])

            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            fold_rmse_scores = []
            models = []

            # K-Fold 검증: 훈련/검증 세트로 반복 학습 및 평가
            for i, (train_idx, val_idx) in enumerate(kf.split(X_trainval)):
                X_tr, X_val_fold = X_trainval.iloc[train_idx], X_trainval.iloc[val_idx]
                y_tr, y_val_fold = y_trainval.iloc[train_idx], y_trainval.iloc[val_idx]

                model = model_class(**params)
                model.fit(X_tr, y_tr)
                y_val_pred = model.predict(X_val_fold)
                rmse = mean_squared_error(y_val_fold, y_val_pred, squared=False)
                fold_rmse_scores.append(rmse)
                models.append(model)

                _logger.info(f"[{model_name}] Fold {i+1} RMSE: {rmse:.4f}")

            # 평균 RMSE 계산 및 최적 fold 선택
            mean_rmse = np.mean(fold_rmse_scores)
            _logger.info(f"[{model_name}] Cross-validated RMSE (mean): {mean_rmse:.4f}")

            best_model_idx = int(np.argmin(fold_rmse_scores))
            best_model = models[best_model_idx]

            # 테스트 세트로 최종 성능 평가
            y_pred = best_model.predict(X_test)
            rmse = mean_squared_error(y_test, y_pred, squared=False)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            _logger.info(f"[{model_name}] Test RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")

            # WandB에 실험 기록 및 모델 정보 저장
            wandb.login(key=WANDB_API_KEY)
            run = wandb.init(project=WANDB_PROJECT, name=f"{model_name}_run", reinit=True)
            run.config.update(params)
            wandb.log({
                "CV_RMSE": mean_rmse,  # 평균 교차검증 RMSE
                "Test_RMSE": rmse,     # 테스트셋 RMSE
                "MAE": mae,
                "R2": r2
            })

            # 최적 모델 저장 및 업로드
            model_path = f"{model_name}_model.pkl"
            joblib.dump(best_model, model_path)
            storage.upload_model(model_path, f"{model_name}_model.pkl")
            wandb.save(model_path)
            run.finish()

        # 모델별 Task 실행 정의
        train_model.override(task_id="decision_tree")(
            model_name="DecisionTree",
            model_class=DecisionTreeRegressor,
            params=HYPERPARAMS["DecisionTree"]
        )
        train_model.override(task_id="random_forest")(
            model_name="RandomForest",
            model_class=RandomForestRegressor,
            params=HYPERPARAMS["RandomForest"]
        )
        train_model.override(task_id="xgboost")(
            model_name="XGBoost",
            model_class=XGBRegressor,
            params=HYPERPARAMS["XGBoost"]
        )
        train_model.override(task_id="lightgbm")(
            model_name="LightGBM",
            model_class=LGBMRegressor,
            params=HYPERPARAMS["LightGBM"]
        )

    # 전체 파이프라인 실행 흐름 정의
    train_models_with_kfold(load_data())

# DAG 호출
optimized_pipeline_dag()