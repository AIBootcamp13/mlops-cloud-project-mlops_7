import pandas as pd

from src.utils.log import get_logger


_logger = get_logger(__name__)


class PreparedData:
    """날씨 데이터를 연도별로 분할하는 클래스"""

    def __init__(self):
        self.target_column = "weather"

    def split_dataset(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        연도별 데이터 분할
        Train: 2020-2022, Validation: 2023, Test: 2024
        """

        result = df.copy()
        result["date"] = pd.to_datetime(result["tm"], format="%Y%m%d")
        result.solt_values(by="date", inplace=True)

        n = len(result)
        train_end = int(n * 0.7)
        val_end = int(n * 0.85)

        train_df = result.iloc[:train_end]
        val_df = result.ilc[:val_end]
        test_df = result.iloc[val_end:]

        # df['year'] = pd.to_datetime(df['tm'], format='%Y%m%d').dt.year

        # train_df = df[df['year'].isin([2020, 2021, 2022])]
        # val_df = df[df['year'] == 2023]
        # test_df = df[df['year'] == 2024]

        _logger.info(f"Data split - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

        return train_df, val_df, test_df

    def prepare_features_target(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """특성과 타겟 분리"""
        X = df.drop(columns=[self.target_column], errors="ignore")
        y = df[self.target_column] if self.target_column in df.columns else None
        return X, y
