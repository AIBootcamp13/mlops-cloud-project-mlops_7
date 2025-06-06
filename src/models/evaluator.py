import pandas as pd
from sklearn.metrics import f1_score, confusion_matrix
import wandb
from src.utils.log import get_logger

_logger = get_logger(__name__)


class Evaluator:
    """모든 모델 최종 평가 클래스"""
    
    def evaluate_all_models(self, trained_models: dict, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """모든 모델 최종 평가"""
        evaluation_results = {}
        
        for model_name, model_info in trained_models.items():
            model = model_info["model"]
            predictions = model.predict(X_test)
            
            f1 = f1_score(y_test, predictions, average='weighted')
            conf_matrix = confusion_matrix(y_test, predictions)
            
            # Feature importance
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = model.feature_importances_
            
            wandb.log({f"{model_name}_test_f1_score": f1})
            
            evaluation_results[model_name] = {
                "model": model,
                "f1_score": f1,
                "confusion_matrix": conf_matrix,
                "feature_importance": feature_importance,
                "predictions": predictions
            }
            
            _logger.info(f"{model_name} Final - F1-Score: {f1:.4f}")
        
        return evaluation_results