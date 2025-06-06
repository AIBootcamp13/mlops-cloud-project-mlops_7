from airflow.decorators import task


@task
def train(train_x_storage_key: str, train_y_storage_key: str, experiment_name: str) -> str:
    """모델 학습"""
    from src.libs.storage import Storage
    from src.models.random_forest import RandomForestModel
    from src.tracker.wandb import WandbTracker

    storage = Storage.create()
    train_x = storage.read_as_dataframe(train_x_storage_key)
    train_y = storage.read_as_dataframe(train_y_storage_key).to_numpy().ravel()

    tracker = WandbTracker.create()
    model_params = RandomForestModel.default_params()

    tracker.start_experiment(
        experiment_name=experiment_name,
        params=model_params,
        job_type="training",
    )

    model = RandomForestModel(model_params)
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
    return model_artifact_ref
