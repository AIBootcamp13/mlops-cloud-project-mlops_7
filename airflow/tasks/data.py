from config.keys import KEY_FEATURE_DATASET_STORAGE_KEY

from airflow.decorators import task
from airflow.models import Variable


TARGET_COLUMN = "weather"


@task
def prepare_data() -> dict[str, str]:
    """
    dataset 을 훈련(60%), 검증(20%), 테스트(20%)로 나눠서
    Cloud Storage 에 저장하고, 그 key 들을 반환
    """
    import uuid
    from pathlib import Path

    from src.data.selection import Spliter
    from src.libs.storage import Storage

    storage = Storage.create()
    feature_storage_key = Variable.get(KEY_FEATURE_DATASET_STORAGE_KEY)
    features = storage.read_as_dataframe(feature_storage_key)

    spliter = Spliter()
    train_df, val_df, test_df = spliter.split(features)
    train_x, train_y = spliter.prepare_features_target(train_df)
    val_x, val_y = spliter.prepare_features_target(val_df)
    test_x, test_y = spliter.prepare_features_target(test_df)

    # 최종적으로, 원래 데이터의 60% 가 훈련 세트, 20% 가 검증 세트, 20% 가 테스트 세트
    dfs = {
        "train_x": train_x,
        "val_x": val_x,
        "test_x": test_x,
        "train_y": train_y,
        "val_y": val_y,
        "test_y": test_y,
    }
    result = {}
    sub_directory = f"{Path(feature_storage_key).parent.name}/split-{uuid.uuid4()}"
    for dataset_name, df in dfs.items():
        storage_key = storage.upload_feature_df(df, filename=dataset_name, sub_directory=sub_directory)
        result[dataset_name] = storage_key
    return result
