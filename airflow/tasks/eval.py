from airflow.decorators import task


@task
def evaluate(val_x_key: str, val_y_key: str, experiment_name: str, model_artifact_ref: str) -> str:
    """모델 평가"""
    from src.evaluation.metrics import evaluate_model
    from src.libs.storage import Storage
    from src.tracker.wandb import WandbTracker

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
    pred_y = model.predict(val_x)
    metrics = evaluate_model(val_y, pred_y)

    tracker.log_metrics(metrics)

    tracker.end_experiment()

    return model_artifact_ref
