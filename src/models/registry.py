import os
from datetime import datetime
from typing import Any, Dict

import joblib
import wandb
from src.utils.log import get_logger

_logger = get_logger("model_registry")

class ModelRegistry:
    def __init__(self, project_name: str = "weather-prediction"):
        self.project_name = project_name
        self.run = None
    
    def init_wandb(self, config: Dict[str, Any] = None):
        """Weights & Biases 초기화"""
        if config is None:
            config = {}
        
        self.run = wandb.init(
            project=self.project_name,
            config=config
        )
        _logger.info(f"Initialized W&B run: {self.run.name}")
    
    def save_model(self, model: Any, scaler: Any, metrics: Dict[str, Any], 
                  feature_importance: Dict[str, float], model_name: str = None) -> str:
        """모델과 관련 정보를 저장합니다."""
        if self.run is None:
            self.init_wandb()
        
        # 모델 저장 경로 설정
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = model_name or f"weather_model_{timestamp}"
        save_dir = os.path.join("models", model_name)
        os.makedirs(save_dir, exist_ok=True)
        
        # 모델과 스케일러 저장
        model_path = os.path.join(save_dir, "model.joblib")
        scaler_path = os.path.join(save_dir, "scaler.joblib")
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # W&B에 모델 아티팩트로 저장
        artifact = wandb.Artifact(
            name=model_name,
            type="model",
            description="Weather prediction model with scaler"
        )
        artifact.add_file(model_path)
        artifact.add_file(scaler_path)
        
        # 메트릭과 특성 중요도 로깅
        wandb.log({
            **metrics,
            "feature_importance": wandb.Table(
                data=[[k, v] for k, v in feature_importance.items()],
                columns=["feature", "importance"]
            )
        })
        
        # 아티팩트 저장
        self.run.log_artifact(artifact)
        
        _logger.info(f"Model saved successfully: {model_name}")
        return model_name
    
    def finish(self):
        """W&B 실행을 종료합니다."""
        if self.run is not None:
            self.run.finish()
            _logger.info("W&B run finished") 