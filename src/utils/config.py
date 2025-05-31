import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


load_dotenv()


def get_env_or_raise(key: str) -> str:
    env_value = os.getenv(key)
    if env_value is None:
        raise ValueError(f"{key} not set in environment variables")
    return env_value


timezone: ZoneInfo = ZoneInfo("Asia/Seoul")

# %% directory

# LOG_ROOT_DIR = Path(os.getenv("LOG_ROOT_DIR", "./logs"))
LOG_ROOT_DIR = Path("/opt/airflow/logs")
LOG_ROOT_DIR.mkdir(parents=True, exist_ok=True)


# %% 환경변수

# ncloud api key
NCLOUD_ACCESS_KEY = get_env_or_raise("NCLOUD_ACCESS_KEY")
NCLOUD_SECRET_KEY = get_env_or_raise("NCLOUD_SECRET_KEY")

# ncloud storage 정보
NCLOUD_STORAGE_REGION = get_env_or_raise("NCLOUD_STORAGE_REGION")
NCLOUD_STORAGE_BUCKET = get_env_or_raise("NCLOUD_STORAGE_BUCKET")
NCLOUD_STORAGE_ENDPOINT_URL = get_env_or_raise("NCLOUD_STORAGE_ENDPOINT_URL")


# 공공 데이터 포털의 기상청 데이터 권한이 있는 api key
WEATHER_API_KEY = get_env_or_raise("WEATHER_API_KEY")

WEATHER_API_URL = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
