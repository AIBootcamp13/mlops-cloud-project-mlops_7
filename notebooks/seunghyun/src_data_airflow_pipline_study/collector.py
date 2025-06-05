from dataclasses import asdict
from datetime import datetime

import pandas as pd

from src.libs.storage import Storage
from src.libs.weather.asosstation import AsosStation
from src.libs.weather.fetcher import AsosDataFetcher
from src.utils.config import DEFAULT_DATE_FORMAT
from src.utils.log import get_logger


_logger = get_logger(__name__)


class AsosStationDataCollector:
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
        prefix = f"{self.start_date.strftime(DEFAULT_DATE_FORMAT)}-{self.end_date.strftime(DEFAULT_DATE_FORMAT)}"
        return f"{prefix}-{self.asos_station.value}-{self.asos_station.name.lower()}.csv"


class Collector:
    def __init__(self, storage: Storage, fetcher: AsosDataFetcher):
        self.storage = storage
        self.fetcher = fetcher
        self.asos_station_collectors: dict[AsosStation, AsosStationDataCollector] = {}
        self.last_fetched_date: datetime | None = None

    def collect_all_asos_data(self, start_date: datetime, end_date: datetime):
        self.asos_station_collectors = {}
        self.last_fetched_date = end_date

        total_station_count = len(AsosStation)
        for idx, station in enumerate(AsosStation):
            collector = AsosStationDataCollector(
                fetcher=self.fetcher,
                asos_station=station,
                start_date=start_date,
                end_date=end_date,
            )

            collector.collect()

            progress = round(idx / total_station_count * 100)
            _logger.info(f"Successfully collect {collector.asos_station}; progress:{progress}%")

            self.asos_station_collectors[station] = collector

        _logger.info("Done collecting all asos data; progress:100%")

    def upload_all_asos_data(self, with_index: bool = False) -> list[str]:
        if not self.asos_station_collectors:
            # Nothing to Do
            _logger.warning("There are no data for upload!")
            return []

        sub_directory = self.last_fetched_date.strftime(DEFAULT_DATE_FORMAT) if self.last_fetched_date else None
        uploaded_keys = []
        for _, collector in self.asos_station_collectors.items():
            filename = collector.generate_filename()
            storage_key = self.storage.make_csv_key_in_datasets(filename, sub_directory=sub_directory)
            is_uploaded = self.storage.upload_dataframe(collector.asos_df, key=storage_key, index=with_index)
            if is_uploaded:
                uploaded_keys.append(storage_key)
                _logger.info(f"Successfully uploaded {storage_key}")
        return uploaded_keys
