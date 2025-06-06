from airflow.decorators import task


@task
def evaluate(val_x_key: str, val_y_key: str, experiment_name: str, model_artifact_ref: str) -> str:
    """모델 평가 및 메트릭 + 메타데이터 기록"""
    import tempfile
    from pathlib import Path

    import joblib
    from sklearn.metrics import confusion_matrix, f1_score

    from src.libs.storage import Storage
    from src.tracker.wandb import WandbTracker
    from src.utils.log import get_logger

    _logger = get_logger(__name__)
    storage = Storage.create()

    val_x = storage.read_as_dataframe(val_x_key)
    val_y = storage.read_as_dataframe(val_y_key).to_numpy().ravel()

    tracker = WandbTracker.create()
    tracker.start_experiment(
        experiment_name=experiment_name,
        params={},
        job_type="evaluation",
    )

    model = tracker.load_model(model_artifact_ref)
    predictions = model.predict(val_x)

    f1 = f1_score(val_y, predictions, average="weighted")
    conf_matrix = confusion_matrix(val_y, predictions)

    # Feature importance (옵션)
    feature_importance = None
    if hasattr(model, "feature_importances_"):
        feature_importance = model.feature_importances_

    metrics = {
        "model": model.name,
        "f1_score": f1,
        "confusion_matrix": conf_matrix.tolist(),
        "feature_importance": feature_importance.tolist() if feature_importance is not None else None,
    }

    _logger.info(f"{model.name} Final - F1-Score: {f1:.4f}")
    tracker.log_metrics(metrics)

    with tempfile.TemporaryDirectory() as tmp_dir:
        model_path = Path(tmp_dir) / f"{model.name}.joblib"
        joblib.dump(model, model_path)
        model_size = model_path.stat().st_size  # ✅ ruff: PTH202 해결

        artifact_ref = tracker.register_model(
            model=model,
            model_name=model.name,
            metadata={
                "f1_score": f1,
                "model_size": model_size,
                "experiment_name": experiment_name,
            },
        )

    tracker.end_experiment()
    return artifact_ref
