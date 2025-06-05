import pandas as pd

from src.libs.storage import Storage
from src.libs.weather.asosstation import AsosStation
from src.utils.log import get_logger


_logger = get_logger(__name__)


class AsosDataLoader:
    """Ncloud Storage 에서 원본 기상 데이터 가져오는 class"""

    UNNAMED_COLUMN = "Unnamed: 0"

    def __init__(self, storage: Storage):
        self.storage = storage

    def load(self) -> dict[AsosStation, pd.DataFrame]:
        asos_data = {}

        storage_keys = self.storage.retrieve_in_datasets()
        _logger.info("Result of retrieve_in_datasets", extra={"storage_keys": storage_keys})
        for storage_key in storage_keys:
            expected_id = storage_key.split("-")[-2]
            if not expected_id.isnumeric():
                continue

            station_id = int(expected_id)
            asos_station = AsosStation(station_id)
            asos_station_df = self.storage.read_as_dataframe(storage_key)

            if self.UNNAMED_COLUMN in asos_station_df.columns:
                asos_station_df = asos_station_df.drop(self.UNNAMED_COLUMN, axis=1)

            asos_data[asos_station] = asos_station_df

        return asos_data

    def load_weather_dataset_at(self, sub_directory: str) -> pd.DataFrame:
        storage_keys = self.storage.retrieve_in_datasets(sub_directory=sub_directory)
        _logger.info(
            "Result of retrieve_in_datasets",
            extra={
                "sub_directory": sub_directory,
                "storage_keys": storage_keys,
            },
        )

        weather_dfs = []
        for storage_key in storage_keys:
            asos_station_df = self.storage.read_as_dataframe(storage_key)

            if self.UNNAMED_COLUMN in asos_station_df.columns:
                asos_station_df = asos_station_df.drop(self.UNNAMED_COLUMN, axis=1)

            weather_dfs.append(asos_station_df)

        return pd.concat(weather_dfs)
