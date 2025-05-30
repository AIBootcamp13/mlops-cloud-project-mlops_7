import pandas as pd
from sklearn.preprocessing import LabelEncoder


class WeatherPreprocessor:
    def __init__(self):
        self.label_encoders = {}
        self.target_encoder = LabelEncoder()
        self.feature_cols = []
        self.target_col = "weather"

    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """날씨 레이블을 가진 df"""
        result = df.copy()

        # 1. iscs 전처리
        result = result[~result[self.target_col].isna()]

        # 2. 전체 범주형 인코딩
        for col in result.columns:
            if col == self.target_col:
                continue
            self.label_encoders[col] = LabelEncoder()
            result[col] = self.label_encoders[col].fit_transform(result[col].astype(str))
            self.feature_cols.append(col)

        # 3. 타겟 인코딩
        result[self.target_col] = self.target_encoder.fit_transform(result[self.target_col].astype(str))

        x = result[self.feature_cols]
        y = result[self.target_col]
        return x, y

    def transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """df 는 레이블을 가진 것"""
        result = df.copy()

        for col in self.feature_cols:
            if col in self.label_encoders:
                result[col] = self.label_encoders[col].transform(result[col].astype(str))

        y = self.target_encoder.transform(result[self.target_col].astype(str))
        x = result[self.feature_cols]
        return x, y
