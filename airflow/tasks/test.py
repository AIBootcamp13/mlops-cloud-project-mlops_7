from airflow.decorators import task


@task
def test(test_x_key: str, test_y_key: str, experiment_id: str, model_artifact_ref: str) -> dict:
    """모델 검증"""
    from src.evaluation.metrics import evaluate_model
    from src.libs.storage import Storage
    from src.tracker.wandb import WandbTracker

    storage = Storage.create()
    test_x = storage.read_as_dataframe(test_x_key)
    test_y = storage.read_as_dataframe(test_y_key).to_numpy().ravel()

    tracker = WandbTracker.create()
    tracker.resume_experiment(experiment_id, job_type="test")

    model = tracker.load_model(model_artifact_ref)

    pred_y = model.predict(test_x)
    metrics = evaluate_model(test_y, pred_y)
    tracker.log_metrics(metrics)

    tracker.end_experiment()
    return {"experiment_id": experiment_id, "model_artifact_ref": model_artifact_ref}
