from __future__ import annotations

import re
from io import StringIO

import boto3
import pandas as pd
from botocore.client import Config
from botocore.exceptions import ClientError

from src.utils import config
from src.utils.log import get_logger


_storage_logger = get_logger(__name__)


class Storage:
    STATUS_OK = 200
    STATUS_NO_CONTENT = 204

    PATTERN = r"^(\d{8})-(\d{8})-(\d+)-([a-zA-Z]+)\.csv$"

    DATASETS_DIR = "datasets"
    FEATURES_DIR = "features"
    PREPROCESSED_DATASETS_DIR = "preprocessed_datasets"

    def __init__(self, access_key: str, secret_key: str, region: str, bucket: str, endpoint: str):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            endpoint_url=endpoint,
            config=Config(signature_version="s3v4"),
        )

    def make_csv_key_in_datasets(self, filename: str, sub_directory: str | None = None) -> str:
        return self._make_csv_key(
            directory=self.DATASETS_DIR,
            filename=filename,
            sub_directory=sub_directory,
        )

    def retrieve_in_datasets(self, sub_directory: str | None = None) -> list[str]:
        filenames = []
        try:
            prefix = self._make_prefix_of_key(self.DATASETS_DIR, sub_directory)
            r = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        except ClientError as e:
            _storage_logger.error(f"Failed to retrieve dataset; {e}")
            return filenames

        if not self._check_and_log_response(task="retrieve", key="", response=r):
            return filenames

        storage_keys = [content.get("Key", "") for content in r.get("Contents", [])]

        # 이 모듈로 올린 형식의 file 만 거르기
        filtered_storage_keys = []
        for storage_key in storage_keys:
            filename = storage_key.split("/")[-1]
            if not re.match(self.PATTERN, filename):
                continue
            filtered_storage_keys.append(storage_key)
        return filtered_storage_keys

    def upload_dataframe(self, df: pd.DataFrame, key: str, index: bool = False) -> bool:
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=index)
        try:
            r = self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=csv_buffer.getvalue(),
            )
        except ClientError as e:
            _storage_logger.error(f"Failed to upload {key}; {e}")
            return False

        return self._check_and_log_response(task="upload", key=key, response=r)

    def read_as_dataframe(self, key: str) -> pd.DataFrame | None:
        try:
            r = self.client.get_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            _storage_logger.warning(f"Failed to read {key}; {e}")
            return None

        if not self._check_and_log_response(task="read", key=key, response=r):
            return None

        file_content = r["Body"].read().decode("utf-8")
        return pd.read_csv(StringIO(file_content))

    def delete(self, key: str) -> bool:
        try:
            r = self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            _storage_logger.warning(f"Failed to delete {key}; {e}")
            return False
        return self._check_and_log_response(task="delete", key=key, response=r)

    def upload_preprocessed_df(
        self, df: pd.DataFrame, filename: str, sub_directory: str | None = None, err_msg: str | None = None
    ) -> str:
        """preprocess 디렉토리에 dataframe 을 업로드."""
        storage_key = self._make_csv_key_in_preprocessed_datasets(filename, sub_directory)
        if self.upload_dataframe(df, storage_key):
            return storage_key
        raise RuntimeError(err_msg if err_msg else f"Failed to upload {storage_key}")

    def upload_feature_df(
        self, df: pd.DataFrame, filename: str, sub_directory: str | None = None, err_msg: str | None = None
    ) -> str:
        """features 디렉토리에 dataframe 을 업로드."""
        storage_key = self._make_csv_key_in_features(filename, sub_directory)
        if self.upload_dataframe(df, storage_key):
            return storage_key
        raise RuntimeError(err_msg if err_msg else f"Failed to upload {storage_key}")

    def _check_and_log_response(self, task: str, key: str, response: dict) -> bool:
        metadata = response.get("ResponseMetadata", {})
        status_code = metadata.get("HTTPStatusCode")

        if status_code not in [self.STATUS_OK, self.STATUS_NO_CONTENT]:
            _storage_logger.warning(f"Failed to {task} {key}; status code: {status_code}", extra=response)
            return False

        _storage_logger.info(f"Success to {task} {key}", extra=response)
        return True

    def _make_csv_key_in_preprocessed_datasets(self, filename: str, sub_directory: str | None = None) -> str:
        return self._make_csv_key(
            directory=self.PREPROCESSED_DATASETS_DIR,
            filename=filename,
            sub_directory=sub_directory,
        )

    def _make_csv_key_in_features(self, filename: str, sub_directory: str | None = None) -> str:
        return self._make_csv_key(
            directory=self.FEATURES_DIR,
            filename=filename,
            sub_directory=sub_directory,
        )

    @staticmethod
    def _make_prefix_of_key(directory: str, sub_directory: str | None) -> str:
        return f"{directory}/{sub_directory}" if sub_directory else directory

    @classmethod
    def _make_csv_key(cls, directory: str, filename: str, sub_directory: str | None = None) -> str:
        prefix = cls._make_prefix_of_key(directory, sub_directory)
        storage_key = f"{prefix}/{filename}"

        if not filename.endswith(".csv"):
            storage_key += ".csv"

        return storage_key

    @staticmethod
    def create() -> Storage:
        return Storage(
            access_key=config.NCLOUD_ACCESS_KEY,
            secret_key=config.NCLOUD_SECRET_KEY,
            region=config.NCLOUD_STORAGE_REGION,
            bucket=config.NCLOUD_STORAGE_BUCKET,
            endpoint=config.NCLOUD_STORAGE_ENDPOINT_URL,
        )
