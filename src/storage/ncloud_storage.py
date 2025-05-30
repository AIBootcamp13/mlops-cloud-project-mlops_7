import os
import boto3
import pandas as pd
from io import StringIO
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

class SimpleNCloudStorage:
    def __init__(self):
        # 설정과 클라이언트 초기화를 한 번에
        self.client = boto3.client(
            "s3",
            endpoint_url=os.getenv("NCLOUD_STORAGE_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("NCLOUD_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("NCLOUD_SECRET_KEY"),
            region_name=os.getenv("NCLOUD_STORAGE_REGION"),
            config=Config(signature_version="s3v4"),
        )
        self.bucket = os.getenv("NCLOUD_STORAGE_BUCKET")
        self.datasets_dir = "datasets"
    
    # DataFrame 관련 메서드들
    def upload_dataframe_as_csv(self, df: pd.DataFrame, filename: str = "data.csv", index: bool = False) -> dict:
        """DataFrame을 CSV로 변환하여 업로드"""
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=index)
        key = f"{self.datasets_dir}/{filename}"
        return self.client.put_object(Bucket=self.bucket, Key=key, Body=csv_buffer.getvalue())
    
    def read_csv_as_dataframe(self, filename: str = "data.csv") -> pd.DataFrame:
        """CSV 파일을 다운로드하여 DataFrame으로 변환"""
        key = f"{self.datasets_dir}/{filename}"
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        file_content = response["Body"].read().decode("utf-8")
        return pd.read_csv(StringIO(file_content))
    
    def delete_csv(self, filename: str = "data.csv") -> dict:
        """CSV 파일 삭제"""
        key = f"{self.datasets_dir}/{filename}"
        return self.client.delete_object(Bucket=self.bucket, Key=key)
    
    # 원시 파일 메서드들 (필요시 사용)
    def upload_file(self, content: str, filename: str) -> dict:
        """임의의 파일 업로드"""
        key = f"{self.datasets_dir}/{filename}"
        return self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
    
    def download_file(self, filename: str) -> str:
        """임의의 파일 다운로드"""
        key = f"{self.datasets_dir}/{filename}"
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read().decode("utf-8")