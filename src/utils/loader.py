import os
import pandas as pd
import boto3
from io import StringIO
from botocore.client import Config

class S3Loader:
    def __init__(self, bucket_name: str, endpoint_url: str, access_key: str, secret_key: str, region: str = "kr-standard"):
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = bucket_name

    def load_csv(self, key: str) -> pd.DataFrame:
        """
        S3에서 CSV 파일을 불러와 DataFrame으로 반환
        """
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        csv_data = response["Body"].read().decode("utf-8")
        df = pd.read_csv(StringIO(csv_data))
        print(f"✅ S3 로드 완료: {key}")
        return df