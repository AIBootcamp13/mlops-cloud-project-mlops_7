import pandas as pd
import joblib
import wandb
import os
from datetime import datetime
from src.utils.log import get_logger

_logger = get_logger(__name__)

class WeatherModelSaver:
    """모델 저장 및 메타데이터 관리 클래스"""
    
    def __init__(self, model_name: str = "weather_prediction_model"):
        self.model_name = model_name
    
    def save_all_models(self, evaluation_results: dict) -> dict:
        """모든 모델을 WandB에 저장"""
        saved_artifacts = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for model_name, result in evaluation_results.items():
            model = result["model"]
            
            #모델 파일 저장
            model_filename = f"{model_name}_model{timestamp}.joblib"
            joblib.dump(model, model_filename)
            
            #WandB 아티팩트 생성
            model_artifact = wandb.Artifact(
                name=f"{model_name}_weather_model",
                type="model",
                description=f"{model_name} 날씨 예측 모델 - F1: {result['f1_score']:.4f}",
                metadata={
                    "model_name" : model_name,
                    "f1_score" : result['f1_score'],
                    "training_date" : timestamp
                }
            )
            
            model_artifact.add_file(model_filename)
            
            #Feature importance 저장 (있는 경우)
            if result.get('feature_importance') is not None:
                importance_df = pd.DataFrame({
                    'feature' : range(len(result['feature_importance'])),
                    'importance': result['feature_importance']
                })
                importance_filename = f"{model_name}_importance_{timestamp}.csv"
                importance_df.to_csv(importance_filename, index=False)
                model_artifact.add_file(importance_filename)
                os.remove(importance_filename)
                
            #아티팩트 로깅
            wandb.log_artifact(model_artifact)
            
            saved_artifacts[model_name] = model_artifact.id
            os.remove(model_filename)
            
            _logger.info(f"{model_name} model saved to WandB")
        
        return saved_artifacts