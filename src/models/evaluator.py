from typing import Dict, Any

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

from src.utils.log import get_logger

_logger = get_logger("model_evaluator")

class ModelEvaluator:
    def __init__(self):
        self.metrics = {}
    
    def evaluate(self, model: Any, scaler: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """모델을 평가하고 성능 지표를 반환합니다."""
        _logger.info("Starting model evaluation...")
        
        # 예측
        X_test_scaled = scaler.transform(X_test)
        y_pred = model.predict(X_test_scaled)
        
        # 성능 지표 계산
        report = classification_report(y_test, y_pred, output_dict=True)
        conf_matrix = confusion_matrix(y_test, y_pred)
        
        # 결과 저장
        self.metrics = {
            'accuracy': report['accuracy'],
            'precision': report['weighted avg']['precision'],
            'recall': report['weighted avg']['recall'],
            'f1_score': report['weighted avg']['f1-score'],
            'confusion_matrix': conf_matrix.tolist(),
            'class_report': report
        }
        
        _logger.info(f"Evaluation completed. Accuracy: {self.metrics['accuracy']:.4f}")
        
        return self.metrics
    
    def get_feature_importance(self, model: Any, feature_names: list) -> Dict[str, float]:
        """특성 중요도를 계산하고 반환합니다."""
        importance_scores = model.feature_importances_
        feature_importance = dict(zip(feature_names, importance_scores))
        
        # 중요도 기준으로 정렬
        sorted_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return sorted_importance 