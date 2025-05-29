import os
import pandas as pd
import boto3
from io import StringIO
from botocore.client import Config

class S3Uploader:
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

    def upload_csv(self, df: pd.DataFrame, key: str):
        """
        S3에서 CSV 파일을 저장
        """
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        self.client.put_object(Bucket=self.bucket, Key=key, Body=csv_buffer.getvalue())
        print(f"✅ S3 저장 완료: {key}")