import os
import math
import requests
import pandas as pd
from time import sleep
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.utils.uploader import S3Uploader
from src.utils.weather_station import WeatherStation

load_dotenv()

class WeatherDataFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"

    def fetch(self, station: WeatherStation, start_date: str, end_date: str) -> pd.DataFrame:
        common_params = {
            "serviceKey": self.api_key,
            "pageNo": "1",
            "numOfRows": "999",
            "dataType": "JSON",
            "dataCd": "ASOS",
            "dateCd": "DAY",
            "startDt": start_date,
            "endDt": end_date,
            "stnIds": station.id,
        }

        try:
            response = requests.get(self.base_url, params=common_params, timeout=20)
            response.raise_for_status()
            total_count = int(response.json()['response']['body']['totalCount'])
            max_page = math.ceil(total_count / int(common_params["numOfRows"]))
        except Exception as e:
            print(f"❌ {station.name} 페이지 수 계산 실패: {e}")
            return pd.DataFrame()

        all_pages = []
        for page in range(1, max_page + 1):
            common_params["pageNo"] = str(page)
            try:
                response = requests.get(self.base_url, params=common_params, timeout=20)
                response.raise_for_status()
                items = response.json()['response']['body']['items']['item']
                df = pd.DataFrame(items)
                df["stnId"] = station.id
                df["stnNm"] = station.name
                all_pages.append(df)
                sleep(1)
            except Exception as e:
                print(f"⚠️ {station.name} - 페이지 {page} 실패: {e}")
        return pd.concat(all_pages, ignore_index=True) if all_pages else pd.DataFrame()


if __name__ == "__main__":
    # 🔧 설정값 불러오기
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    NCLOUD_ACCESS_KEY = os.getenv("NCLOUD_ACCESS_KEY")
    NCLOUD_SECRET_KEY = os.getenv("NCLOUD_SECRET_KEY")
    NCLOUD_STORAGE_REGION = os.getenv("NCLOUD_STORAGE_REGION")
    NCLOUD_STORAGE_BUCKET = os.getenv("NCLOUD_STORAGE_BUCKET")
    NCLOUD_STORAGE_ENDPOINT_URL = os.getenv("NCLOUD_STORAGE_ENDPOINT_URL")

    yesterday_str = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")

    fetcher = WeatherDataFetcher(api_key=WEATHER_API_KEY)
    uploader = S3Uploader(
        bucket_name=NCLOUD_STORAGE_BUCKET,
        endpoint_url=NCLOUD_STORAGE_ENDPOINT_URL,
        access_key=NCLOUD_ACCESS_KEY,
        secret_key=NCLOUD_SECRET_KEY,
        region=NCLOUD_STORAGE_REGION,
    )

    all_data = []
    for station in WeatherStation:
        print(f"📍 {station.name} 수집 시작")
        df = fetcher.fetch(station, "20200101", yesterday_str)
        if not df.empty:
            all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        uploader.upload_csv(final_df, "datasets/weather_all_station.csv")
    else:
        print("❌ 전체 수집 실패")