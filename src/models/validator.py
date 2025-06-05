import pandas as pd
from sklearn.metrics import f1_score, confusion_matrix
import wandb
from src.utils.log import get_logger

_logger = get_logger(__name__)

class Validator:
    """모든 모델 검증 클래스"""
    
    def validate_all_models(self, trained_models: dict, X_val: pd.DataFrame, y_val: pd.Series) -> dict:
        validation_results = {}
        
        for model_name, model_info in trained_models.items():
            model = model_info["model"]
            predictions = model.predict(X_val)
            f1 = f1_score(y_val, predictions, average="macro")
            cm = confusion_matrix(y_val, predictions)
            
            # W&B 로깅
            wandb.log({
                f"{model_name}_val_f1": f1,
                f"{model_name}_val_confusion_matrix": cm.tolist()
            })

            # 결과 저장
            validation_results[model_name] = {
                "model": model,
                "f1_score": f1,
                "confusion_matrix": cm.tolist(),
                "predictions": predictions.tolist()
            }
            
            _logger.info(f"{model_name} - Validation F1: {f1:.4f}")
        
        return validation_results
