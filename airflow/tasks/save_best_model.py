from airflow.decorators import task


@task
def save_best_model(experiment_name: str, model_names: list[str]) -> str:
    """모델 metadata 기반으로 가장 좋은 모델 선택 후 best_model로 저장"""
    from pathlib import Path

    import joblib

    from src.tracker.wandb import WandbTracker
    from src.utils.log import get_logger

    logger = get_logger(__name__)
    tracker = WandbTracker.create()
    tracker.start_experiment(experiment_name, {}, job_type="model_selection")

    best_model = None
    best_score = -1.0
    best_size = float("inf")

    for model_name in model_names:
        try:
            artifact_ref = f"{tracker.project_name}/{model_name}:latest"
            artifact = tracker.run.use_artifact(artifact_ref, type="model")

            f1_score = artifact.metadata.get("f1_score")
            model_size = artifact.metadata.get("model_size")

            if f1_score is None or model_size is None:
                logger.warning(f"모델 {model_name}의 metadata 정보 부족 → 스킵")
                continue

            logger.info(f"모델 {model_name} - f1: {f1_score}, size: {model_size}")

            if (f1_score > best_score) or (f1_score == best_score and model_size < best_size):
                best_model = artifact
                best_score = f1_score
                best_size = model_size

        except Exception as e:
            logger.warning(f"모델 {model_name} 로딩 실패: {e}")
            continue

    if best_model is None:
        raise RuntimeError("성능 비교 가능한 모델이 없습니다.")

    # best 모델 복사 → 새 artifact로 등록
    model_dir = Path(best_model.download())
    model_files = list(model_dir.glob("*.joblib"))  # ✅ PTH207 해결

    if not model_files:
        raise FileNotFoundError("best 모델의 joblib 파일을 찾을 수 없습니다.")

    model = joblib.load(model_files[0])

    best_model_artifact_ref = tracker.register_model(
        model=model,
        model_name="best_model",
        metadata={
            "source_model": best_model.name,
            "f1_score": best_score,
            "model_size": best_size,
            "selection_criteria": "best f1_score and smallest size",
        },
    )

    logger.info(f"Best model selected: {best_model.name} with f1_score={best_score}, size={best_size}")
    tracker.end_experiment()
    return best_model_artifact_ref
