from abc import ABC, abstractmethod

from src.models.base import BaseModel


class MLExperimentTracker(ABC):
    """ML 실험 추적 및 모델 레지스트리를 위한 인터페이스"""

    @abstractmethod
    def start_experiment(self, experiment_name: str, params: dict, job_type: str, tags: list[str] | None = None):
        """새 실험 시작"""

    @abstractmethod
    def resume_experiment(self, run_id: str, job_type: str):
        """기존 실험 재개"""

    @abstractmethod
    def log_metrics(self, metrics: dict, step: int | None = None):
        """메트릭 로깅"""

    @abstractmethod
    def register_model(self, model: BaseModel, model_name: str, metadata: dict | None = None) -> str:
        """모델 레지스트리에 등록"""

    @abstractmethod
    def load_model(self, model_name: str, version: str = None) -> BaseModel:
        """레지스트리에서 모델 로드"""

    @abstractmethod
    def end_experiment(self):
        """실험 종료"""
