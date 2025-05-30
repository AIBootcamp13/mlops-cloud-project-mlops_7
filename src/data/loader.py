import pandas as pd

from src.libs.storage import Storage
from src.libs.weather.asosstation import AsosStation


class AsosDataLoader:
    """Ncloud Storage 에서 원본 기상 데이터 가져오는 class"""

    UNNAMED_COLUMN = "Unnamed: 0"

    def __init__(self, storage: Storage):
        self.storage = storage

    def load(self) -> dict[AsosStation, pd.DataFrame]:
        asos_data = {}

        filenames = self.storage.retrieve_datasets()
        for filename in filenames:
            expected_id = filename.split("-")[-2]
            if not expected_id.isnumeric():
                continue

            station_id = int(expected_id)
            asos_station = AsosStation(station_id)

            storage_key = self.storage.make_csv_key_in_datasets(filename)
            asos_station_df = self.storage.read_as_dataframe(storage_key)

            if self.UNNAMED_COLUMN in asos_station_df.columns:
                asos_station_df = asos_station_df.drop(self.UNNAMED_COLUMN, axis=1)

            asos_data[asos_station] = asos_station_df

        return asos_data
