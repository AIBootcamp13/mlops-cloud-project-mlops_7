import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class WeatherDataOutlierHandler(BaseEstimator, TransformerMixin):
    """수치형 변수에 대해서 이상치 처리: IQR 기반 윈저화(경계값으로 대체)"""

    def __init__(self, columns: list[str] | None = None, iqr_multiplier: float = 1.5):
        self.columns_ = columns
        self.iqr_multiplier = iqr_multiplier
        self.bounds_ = {}

    def fit(self, x, y=None):
        """데이터에서 IQR 기반 경계값을 계산"""
        # 처리할 컬럼 결정
        self.columns_ = self.columns_ if self.columns_ else x.select_dtypes(include=np.number).columns.tolist()

        # 각 컬럼별 IQR 기반 경계값 계산
        for col in self.columns_:
            if col not in x.columns:
                continue

            q1 = x[col].quantile(0.25)
            q3 = x[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - (self.iqr_multiplier * iqr)
            upper_bound = q3 + (self.iqr_multiplier * iqr)
            self.bounds_[col] = {"lower": lower_bound, "upper": upper_bound}

        return self

    def transform(self, x, y=None):
        """이상치를 식별하고 윈저화 적용"""
        x_transformed = x.copy()

        # 각 컬럼별 이상치 처리
        for col in self.columns_:
            if col not in x.columns or col not in self.bounds_:
                continue

            lower_bound = self.bounds_[col]["lower"]
            upper_bound = self.bounds_[col]["upper"]

            # 윈저화 적용: 경계값으로 대체
            x_transformed[col] = x_transformed[col].clip(lower=lower_bound, upper=upper_bound)

        return x_transformed

    def fit_transform(self, x, y=None, **kwargs):
        """데이터에 맞게 모델을 학습시키고 변환"""
        return self.fit(x, y).transform(x)
