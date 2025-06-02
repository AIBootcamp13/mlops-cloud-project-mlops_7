from enum import Enum

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class WeatherType(str, Enum):
    CLEAR = "맑음"
    CLOUDY = "흐림"
    RAINY = "비"
    SNOWY = "눈"
    UNKNOWN = "알수없음"


class WeatherApplier:
    def __init__(self, daily_data: pd.Series):
        """daily_data 중 사용할 column 을 속성으로 저장"""
        # 전운량 (구름의 양)
        self.avg_tca = daily_data.get("avg_tca")

        # 강수 관련 데이터
        self.sum_rn = daily_data.get("sum_rn")  # 일 강수량
        self.hr1_max_rn = daily_data.get("hr1_max_rn")  # 1시간 최다 강수량

        # 기온 관련 데이터
        self.avg_ta = daily_data.get("avg_ta")  # 평균 기온
        self.min_ta = daily_data.get("min_ta")  # 최저 기온
        self.max_ta = daily_data.get("max_ta")  # 최고 기온

        # 일조 시간
        self.sum_ss_hr = daily_data.get("sum_ss_hr")  # 합계 일조 시간

    def _is_clear(self) -> bool:
        """'맑음' 상태인지 판단"""
        # 전운량이 3 이하 (구름이 적음), 비나 눈이 없음, 일조 시간이 충분
        if pd.isna(self.avg_tca) or pd.isna(self.sum_rn) or pd.isna(self.sum_ss_hr):
            return False

        return self.avg_tca <= 3 and self.sum_rn == 0 and self.sum_ss_hr >= 5  # 일조 시간이 5시간 이상

    def _is_cloudy(self) -> bool:
        """'흐림' 상태인지 판단"""
        # 전운량이 7 이상 (구름이 많음), 비나 눈이 없음
        if pd.isna(self.avg_tca) or pd.isna(self.sum_rn):
            return False

        return self.avg_tca >= 7 and self.sum_rn == 0

    def _is_rainy(self) -> bool:
        """'비' 상태인지 판단"""
        # 강수량이 있고, 기온이 영상
        if pd.isna(self.sum_rn) or pd.isna(self.avg_ta):
            return False

        return self.sum_rn > 0 and self.avg_ta > 0  # 평균 기온이 0°C 초과

    def _is_snowy(self) -> bool:
        """'눈' 상태인지 판단"""
        # 강수량이 있고, 기온이 낮음
        if pd.isna(self.sum_rn) or pd.isna(self.avg_ta) or pd.isna(self.max_ta):
            return False

        return (
            self.sum_rn > 0 and self.avg_ta <= 2 and self.max_ta <= 5
        )  # 평균 기온이 2°C 이하이고 최고 기온이 5°C 이하

    def determine_weather_label(self) -> str:
        if self._is_clear():
            return WeatherType.CLEAR.value

        if self._is_cloudy():
            return WeatherType.CLOUDY.value

        if self._is_rainy():
            return WeatherType.RAINY.value

        if self._is_snowy():
            return WeatherType.SNOWY.value

        return WeatherType.UNKNOWN.value  # 판단 불가


class WeatherLabeler(BaseEstimator, TransformerMixin):
    LABEL_COLUMN = "weather"

    def fit(self, df: pd.DataFrame, y=None):
        """pass"""
        return self

    def transform(self, df: pd.DataFrame, y=None):
        result = df.copy()
        result[self.LABEL_COLUMN] = result.apply(lambda row: WeatherApplier(row).determine_weather_label(), axis=1)
        return result

    def fit_transform(self, df: pd.DataFrame, y=None, **kwargs):
        return self.fit(df, y).transform(df, y)
