import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelEncoder


class SafeLabelEncoder:
    CATEGORY_UNKNOWN = "unknown"

    def __init__(self, unknown_value=-1):
        self.classes_ = []
        self.le = LabelEncoder()
        self.unknown_value = unknown_value

    def fit(self, y):
        self.le.fit(y)
        self.classes_ = self.le.classes_
        return self

    def transform(self, y):
        y_new = np.array(y).copy()
        for i, val in enumerate(y):
            if val not in self.classes_:
                y_new[i] = self.unknown_value
            else:
                y_new[i] = self.le.transform([val])[0]
        return y_new

    def fit_transform(self, y):
        return self.fit(y).transform(y)

    def inverse_transform(self, y):
        mask = y == self.unknown_value
        y_transformed = np.array(y).copy()
        y_transformed[~mask] = self.le.inverse_transform(y_transformed[~mask])
        y_transformed[mask] = self.CATEGORY_UNKNOWN
        return y_transformed


class WeatherDataTransformer(BaseEstimator, TransformerMixin):
    """기상 데이터의 column 에 대해서, scaling 및 encoding 을 하는 class"""

    DATE_FORMAT = "%Y%m%d"

    TARGET_COLUMN = "weather"
    DATETIME_COLUMN = "tm"
    CATEGORICAL_COLUMNS = (
        "stn_id",
        "stn_nm",
        "min_ta_hrmt",
        "max_ta_hrmt",
        "mi10_max_rn_hrmt",
        "hr1_max_rn_hrmt",
        "max_ins_ws_wd",
        "max_ins_ws_hrmt",
        "max_ws_wd",
        "max_ws_hrmt",
        "max_wd",
        "min_rhm_hrmt",
        "max_ps_hrmt",
        "min_ps_hrmt",
    )
    NUMERICAL_COLUMNS = (
        "tm",
        "avg_ta",
        "min_ta",
        "max_ta",
        "mi10_max_rn",
        "hr1_max_rn",
        "sum_rn",
        "max_ins_ws",
        "max_ws",
        "avg_ws",
        "hr24_sum_rws",
        "avg_td",
        "min_rhm",
        "avg_rhm",
        "avg_pv",
        "avg_pa",
        "max_ps",
        "min_ps",
        "avg_ps",
        "ss_dur",
        "sum_ss_hr",
        "avg_tca",
        "avg_lmac",
        "avg_ts",
        "min_tg",
    )

    def __init__(self):
        self.label_encoders: dict[str, SafeLabelEncoder] = {}
        self.target_encoder = SafeLabelEncoder()

    def fit(self, df: pd.DataFrame, y=None):
        """수치형 데이터에 대한 스케일러와 범주형 데이터에 대한 인코더를 학습시킵니다."""
        result = df.copy()

        # 범주형 데이터 처리
        for column in self.CATEGORICAL_COLUMNS:
            if column not in result.columns:
                continue

            self.label_encoders[column] = SafeLabelEncoder()

            # 문자열로 변환하여 인코더 학습
            valid_data = result[column].dropna().astype(str).to_numpy()
            if len(valid_data) > 0:
                self.label_encoders[column].fit(valid_data)

        # 타겟 변수 처리
        target = result[self.TARGET_COLUMN]
        self.target_encoder.fit(target)

        return self

    def transform(self, df: pd.DataFrame, y=None):
        """데이터를 변환합니다."""
        result = df.copy()

        # 일시 데이터 처리
        # '%Y-%m-%d' 형식을 datetime으로 변환 후 '%Y%m%d' 형식의 정수로 변환
        result[self.DATETIME_COLUMN] = (
            pd.to_datetime(result[self.DATETIME_COLUMN]).dt.strftime(self.DATE_FORMAT).astype(int)
        )

        # 범주형 데이터 처리
        for column in self.CATEGORICAL_COLUMNS:
            if column not in result.columns:
                continue

            # 결측치가 아닌 데이터만 인코딩
            non_null_mask = result[column].notna()
            if not non_null_mask.any():
                continue

            result.loc[non_null_mask, column] = self.label_encoders[column].transform(
                result.loc[non_null_mask, column].astype(str).values
            )

        # 타겟 변수 변환
        if self.TARGET_COLUMN in result.columns:
            target = result[self.TARGET_COLUMN]
            result[self.TARGET_COLUMN] = self.target_encoder.transform(target)

        return result

    def fit_transform(self, df: pd.DataFrame, y=None, **kwargs):
        """데이터를 학습시키고 변환합니다."""
        return self.fit(df, y).transform(df, y)
