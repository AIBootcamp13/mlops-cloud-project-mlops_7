from dataclasses import asdict
from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta

from src.libs.storage import Storage
from src.libs.weather.asosstation import AsosStation
from src.libs.weather.fetcher import AsosDataFetcher
from src.utils import config


class AsosStationDataCollector:
    DATE_FORMAT = "%Y%m%d"

    def __init__(
        self,
        fetcher: AsosDataFetcher,
        asos_station: AsosStation,
        start_date: datetime,
        end_date: datetime,
    ):
        self.fetcher = fetcher
        self.asos_station = asos_station
        self.start_date = start_date
        self.end_date = end_date
        self.asos_df = pd.DataFrame()

    def collect(self) -> pd.DataFrame:
        res = self.fetcher.fetch_all(
            asos_station=self.asos_station,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.asos_df = pd.DataFrame([asdict(item) for item in res.items])
        return self.asos_df

    def generate_filename(self) -> str:
        prefix = f"{self.start_date.strftime(self.DATE_FORMAT)}-{self.end_date.strftime(self.DATE_FORMAT)}"
        return f"{prefix}-{self.asos_station.value}-{self.asos_station.name.lower()}.csv"


class Collector:
    def __init__(self, storage: Storage, fetcher: AsosDataFetcher):
        self.storage = storage
        self.fetcher = fetcher
        self.asos_station_collectors: dict[AsosStation, AsosStationDataCollector] = {}

    def collect_all_asos_data_3month_ago(self):
        today = datetime.now(config.timezone)
        three_months_ago = today + relativedelta(months=-3)
        self.collect_all_asos_data(start_date=three_months_ago, end_date=today)

    def collect_all_asos_data(self, start_date: datetime, end_date: datetime):
        self.asos_station_collectors = {}

        for station in AsosStation:
            collector = AsosStationDataCollector(
                fetcher=self.fetcher,
                asos_station=station,
                start_date=start_date,
                end_date=end_date,
            )

            collector.collect()

            self.asos_station_collectors[station] = collector

    def upload_all_asos_data(self, with_index: bool = False) -> list[str]:
        uploaded_keys = []
        for _, collector in self.asos_station_collectors.items():
            filename = collector.generate_filename()
            storage_key = self.storage.generate_csv_key_in_datasets(filename)
            is_uploaded = self.storage.upload_dataframe(collector.asos_df, key=storage_key, index=with_index)
            if is_uploaded:
                uploaded_keys.append(storage_key)
        return uploaded_keys
