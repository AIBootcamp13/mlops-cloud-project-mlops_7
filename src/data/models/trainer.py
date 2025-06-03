from typing import Any, Dict, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from src.utils.log import get_logger

_logger = get_logger("model_trainer")

class ModelTrainer:
    def __init__(self, test_size: float = 0.2, random_state: int = 42):
        self.test_size = test_size
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        
    def prepare_data(self, features: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """데이터를 학습용과 테스트용으로 분할하고 전처리합니다."""
        # 특성과 타겟 분리
        X = features.drop('weather_label', axis=1)
        y = features['weather_label']
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state
        )
        
        # 특성 스케일링
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return pd.DataFrame(X_train_scaled, columns=X.columns), y_train, \
               pd.DataFrame(X_test_scaled, columns=X.columns), y_test
    
    def train(self, features: pd.DataFrame) -> Dict[str, Any]:
        """모델을 학습하고 결과를 반환합니다."""
        _logger.info("Starting model training...")
        
        # 데이터 준비
        X_train, y_train, X_test, y_test = self.prepare_data(features)
        
        # XGBoost 모델 초기화 및 학습
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=self.random_state
        )
        
        self.model.fit(X_train, y_train)
        
        # 학습 결과 평가
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        _logger.info(f"Training completed. Train score: {train_score:.4f}, Test score: {test_score:.4f}")
        
        return {
            'model': self.model,
            'scaler': self.scaler,
            'train_score': train_score,
            'test_score': test_score,
            'feature_names': X_train.columns.tolist()
        } 