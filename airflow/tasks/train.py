from airflow.decorators import task


@task
def train(train_x_storage_key: str, train_y_storage_key: str, experiment_name: str, model_name: str) -> str:
    """모델 학습"""
    from src.libs.storage import Storage
    from src.models import MODEL_REGISTRY
    from src.tracker.wandb import WandbTracker
    from src.utils.log import get_logger

    logger = get_logger(f"train_{model_name}")

    if model_name not in MODEL_REGISTRY:
        logger.info(f"Not supported model: {model_name}")
        raise ValueError(f"Not supported model: {model_name}")

    logger.info(f"Starting training for {model_name} model")
    storage = Storage.create()
    train_x = storage.read_as_dataframe(train_x_storage_key)
    train_y = storage.read_as_dataframe(train_y_storage_key).to_numpy().ravel()

    tracker = WandbTracker.create()
    model_params = MODEL_REGISTRY[model_name].default_params()

    tracker.start_experiment(
        experiment_name=experiment_name,
        params=model_params,
        job_type="training",
    )

    model = MODEL_REGISTRY[model_name](model_params)
    model.fit(train_x, train_y)

    model_artifact_ref = tracker.register_model(
        model,
        model_name="random-forest",
        metadata={
            "framework": "sklearn",
            "datasets": {
                "storage": {
                    "name": "ncloud",
                    "bucket": storage.bucket,
                    "train_x": train_x_storage_key,
                    "train_y": train_y_storage_key,
                }
            },
            "params": model_params,
        },
    )

    tracker.end_experiment()
    logger.info(f"Finish training for {model_name} model")
    return model_artifact_ref
