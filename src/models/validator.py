from typing import Dict, Any, Tuple

import pandas as pd
from sklearn.model_selection import cross_val_score
import numpy as np

from src.utils.log import get_logger

_logger = get_logger("model_validator")

class ModelValidator:
    def __init__(self, cv: int = 5):
        self.cv = cv
        self.validation_scores = {}
    
    def validate(self, model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """교차 검증을 수행하고 결과를 반환합니다."""
        _logger.info(f"Starting {self.cv}-fold cross validation...")
        
        # 교차 검증 수행
        cv_scores = cross_val_score(model, X, y, cv=self.cv, scoring='accuracy')
        
        # 결과 저장
        self.validation_scores = {
            'mean_score': np.mean(cv_scores),
            'std_score': np.std(cv_scores),
            'cv_scores': cv_scores.tolist()
        }
        
        _logger.info(f"Validation completed. Mean CV score: {self.validation_scores['mean_score']:.4f}")
        
        return self.validation_scores
    
    def validate_with_threshold(self, model: Any, X: pd.DataFrame, y: pd.Series, 
                              threshold: float = 0.8) -> Tuple[bool, Dict[str, Any]]:
        """임계값을 기준으로 모델 검증을 수행합니다."""
        validation_results = self.validate(model, X, y)
        
        # 임계값 기준 검증
        is_valid = validation_results['mean_score'] >= threshold
        
        _logger.info(f"Model validation {'passed' if is_valid else 'failed'} "
                    f"(threshold: {threshold}, score: {validation_results['mean_score']:.4f})")
        
        return is_valid, validation_results 