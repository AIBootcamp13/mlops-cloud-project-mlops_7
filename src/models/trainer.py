import pandas as pd
import numpy as np
import time

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import f1_score

import lightgbm as lgb
import xgboost as xgb
import wandb

from src.utils.log import get_logger

_logger = get_logger(__name__)


class Trainer:
    """LightGBM, XGBoost, RandomForest 모델을 모두 학습하는 클래스"""

    def __init__(self):
        self.model_defs = {
            "lightgbm": lgb.LGBMClassifier(n_estimators=100, random_state=42, verbose=-1),
            "randomforest": RandomForestClassifier(n_estimators=100, random_state=42),
            "xgboost": xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='mlogloss')
        }

    def train_all_models(self, X_train: pd.DataFrame, y_train: pd.Series) -> dict:
        """모든 모델 학습 + CV 결과 및 메타데이터 반환"""
        tscv = TimeSeriesSplit(n_splits=2)
        trained_models = {}

        for model_name, model in self.model_defs.items():
            _logger.info(f"Training model: {model_name}")
            start_time = time.time()
            cv_scores = []

            # Cross Validation
            for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
                X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
                y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

                model.fit(X_tr, y_tr)
                preds = model.predict(X_val)
                f1 = f1_score(y_val, preds, average="macro")

                wandb.log({f"{model_name}_fold{fold+1}_f1": f1})
                cv_scores.append(f1)

            cv_mean = np.mean(cv_scores)
            cv_std = np.std(cv_scores)

            _logger.info(f"{model_name} - CV Mean F1: {cv_mean:.4f}, Std: {cv_std:.4f}")

            # 전체 데이터로 재학습
            model.fit(X_train, y_train)

            elapsed_time = round(time.time() - start_time, 2)

            wandb.log({
                f"{model_name}_cv_mean_f1": cv_mean,
                f"{model_name}_cv_std_f1": cv_std,
                f"{model_name}_train_time_sec": elapsed_time
            })

            # 모델 + 메타데이터 저장
            trained_models[model_name] = {
                "model": model,
                "cv_scores": cv_scores,
                "cv_mean": cv_mean,
                "cv_std": cv_std,
                "train_time_sec": elapsed_time,
                "model_type": type(model).__name__,
                "retrained": True
            }

        return trained_models
