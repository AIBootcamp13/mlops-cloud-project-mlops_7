from __future__ import annotations

import re
import time
from io import StringIO

import boto3
import pandas as pd
from botocore.client import Config
from botocore.exceptions import ClientError

from src.utils import config
from src.utils.log import get_logger


storage_logger = get_logger(__name__)


class Storage:
    STATUS_OK = 200
    STATUS_NO_CONTENT = 204

    PATTERN = r"^(\d{8})-(\d{8})-(\d+)-([a-zA-Z]+)\.csv$"

    DATASETS_DIR = "datasets"
    FEATURES_DIR = "features"

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

    def make_csv_key_in_datasets(self, filename: str) -> str:
        return self._make_csv_key(self.DATASETS_DIR, filename)

    def make_csv_key_in_features(self, filename: str) -> str:
        return self._make_csv_key(self.FEATURES_DIR, filename)

    def generate_csv_key_in_datasets(self, filename: str) -> str:
        return self._generate_csv_key(self.DATASETS_DIR, filename)

    def generate_csv_key_in_features(self, filename: str) -> str:
        return self._generate_csv_key(self.FEATURES_DIR, filename)

    def retrieve_datasets(self) -> list[str]:
        filenames = []
        try:
            r = self.client.list_objects_v2(Bucket=self.bucket, Prefix=self.DATASETS_DIR)
        except ClientError as e:
            storage_logger.error(f"Failed to retrieve dataset; {e}")
            return filenames

        if not self._check_and_log_response(task="retrieve", key="", response=r):
            return filenames

        storage_keys = [content.get("Key", "") for content in r.get("Contents", [])]
        filenames = [storage_key.split("/")[-1] for storage_key in storage_keys]
        return [filename for filename in filenames if re.match(self.PATTERN, filename)]

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
            storage_logger.error(f"Failed to upload {key}; {e}")
            return False

        return self._check_and_log_response(task="upload", key=key, response=r)

    def read_as_dataframe(self, key: str) -> pd.DataFrame | None:
        try:
            r = self.client.get_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            storage_logger.warning(f"Failed to read {key}; {e}")
            return None

        if not self._check_and_log_response(task="read", key=key, response=r):
            return None

        file_content = r["Body"].read().decode("utf-8")
        return pd.read_csv(StringIO(file_content))

    def delete(self, key: str) -> bool:
        try:
            r = self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            storage_logger.warning(f"Failed to delete {key}; {e}")
            return False
        return self._check_and_log_response(task="delete", key=key, response=r)

    def _check_and_log_response(self, task: str, key: str, response: dict) -> bool:
        metadata = response.get("ResponseMetadata", {})
        status_code = metadata.get("HTTPStatusCode")

        if status_code not in [self.STATUS_OK, self.STATUS_NO_CONTENT]:
            storage_logger.warning(f"Failed to {task} {key}; status code: {status_code}", extra=response)
            return False

        storage_logger.info(f"Success to {task} {key}", extra=response)
        return True

    @classmethod
    def _generate_csv_key(cls, directory: str, filename: str) -> str:
        current_millis = round(time.time() * 1000)
        unique_filename = f"{current_millis}-{filename}"
        return cls._make_csv_key(directory, unique_filename)

    @classmethod
    def _make_csv_key(cls, directory: str, filename: str) -> str:
        storage_key = f"{directory}/{filename}"

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
