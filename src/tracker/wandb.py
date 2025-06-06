from __future__ import annotations

import tempfile
from pathlib import Path

import wandb

from src.models.base import BaseModel
from src.tracker.base import MLExperimentTracker
from src.utils import config


class WandbTracker(MLExperimentTracker):
    """Weights & Biases를 사용한 ML 실험 추적 구현"""

    def __init__(self, api_key: str, project_name: str, entity: str | None = None):
        """
        W&B 기반 실험 추적 초기화

        Args:
            api_key: weights & biases 의 api key
            project_name: W&B 프로젝트 이름
            entity: W&B 팀/조직 이름 (optional)
        """
        self.api_key = api_key
        self.project_name = project_name
        self.entity = entity
        self.run = None
        self.is_active = False

    def start_experiment(
        self, experiment_name: str, params: dict, job_type: str, tags: list[str] | None = None
    ) -> wandb.sdk.wandb_run.Run:
        """
        새 실험 시작

        Args:
            experiment_name: 실험 이름
            params: 하이퍼파라미터 및 설정
            job_type: 실행하는 작업의 종류나 목적
            tags: 실험 태그

        Returns:
            W&B 실행 객체
        """
        # 로그인
        wandb.login(key=self.api_key)

        if self.is_active:
            print("실험이 이미 활성화되어 있습니다.")
            return self.run

        self.run = wandb.init(
            project=self.project_name,
            entity=self.entity,
            name=experiment_name,
            job_type=job_type,
            config=params,
            tags=tags,
        )

        self.is_active = True
        return self.run

    def log_metrics(self, metrics: dict, step: int | None = None):
        """
        메트릭 로깅

        Args:
            metrics: 로깅할 메트릭 딕셔너리
            step: 현재 스텝 (선택적)
        """
        if not self.is_active:
            raise RuntimeError("활성화된 실험이 없습니다. start_experiment()를 먼저 호출하세요.")

        wandb.log(metrics, step=step)

    def register_model(self, model: BaseModel, model_name: str, metadata: dict | None = None) -> str:
        """
        모델 레지스트리에 등록

        Args:
            model: 모델 객체
            model_name: 모델 이름
            metadata: 모델 메타데이터

        Returns:
            모델 참조 문자열 (name:version)
        """
        if not self.is_active:
            raise RuntimeError("활성화된 실험이 없습니다. start_experiment()를 먼저 호출하세요.")

        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 모델 저장
            import joblib

            model_path = Path(tmp_dir) / f"model-{model_name}.joblib"
            joblib.dump(model, model_path)

            # Artifact 생성
            artifact = wandb.Artifact(name=model_name, type="model", metadata=metadata)

            # 모델 파일 추가
            artifact.add_file(str(model_path))

            # Artifact 로깅
            artifact = wandb.log_artifact(artifact)

            # 로깅이 완료될 때까지 기다림
            artifact.wait()

            # 모델 참조 문자열 반환
            return f"{model_name}:{artifact.version}"

    def load_model(self, model_name: str, version: str = "latest") -> BaseModel:
        """
        레지스트리에서 모델 로드

        Args:
            model_name: 모델 이름
            version: 모델 버전 (기본값: latest)

        Returns:
            로드된 모델 객체
        """
        if not self.is_active:
            raise RuntimeError("활성화된 실험이 없습니다. start_experiment()를 먼저 호출하세요.")

        # Artifact 참조 문자열 생성
        artifact_ref = model_name if ":" in model_name else f"{model_name}:{version}"

        # Artifact 불러오기
        artifact = self.run.use_artifact(artifact_ref, type="model")

        # 임시 디렉토리에 다운로드
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_dir = Path(artifact.download(root=tmp_dir))

            import joblib

            # 모델 파일 찾기
            model_files = list(model_dir.glob("*.joblib"))
            if not model_files:
                raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_dir}")

            model_path = model_files[0]

            # 모델 로드
            return joblib.load(model_path)

    def end_experiment(self):
        """실험 종료"""
        if self.is_active:
            wandb.finish()
            self.is_active = False
            self.run = None

    @classmethod
    def create(cls) -> WandbTracker:
        return WandbTracker(
            api_key=config.WANDB_API_KEY,
            project_name=config.WANDB_PROJECT,
            entity=config.WANDB_ENTITY,
        )
