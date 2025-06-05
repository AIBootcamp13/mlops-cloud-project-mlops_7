import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class WeatherDataImputer(BaseEstimator, TransformerMixin):
    """기상 데이터의 특정 column 에 대해서 결측치를 처리하는 class"""

    GROUP_BY_COLUMN = "stn_id"

    def __init__(self):
        # 보간(interpolate)할 컬럼들; 13개
        self.interpolate_cols = [
            "avg_ta",  # 평균 기온(°C)
            "min_ta",  # 최저 기온(°C)
            "max_ta",  # 최고 기온(°C)
            "avg_ts",  # 평균 지면온도(°C)
            "avg_ps",  # 평균 해면기압(hPa)
            "avg_rhm",  # 평균 상대습도(%)
            "avg_pv",  # 평균 증기압(hPa)
            "avg_ws",  # 평균 풍속(m/s)
            "avg_tca",  # 평균 전운량(10분위)
            "sum_ss_hr",  # 합계 일조 시간(hr)
            "avg_lmac",  # 평균 중하층운량(10분위)
            "max_ws",  # 최대 풍속(m/s)
            "avg_td",  # 평균 이슬점온도(°C)
            "avg_pa",  # 평균 현지기압(hPa)
            "ss_dur",  # 가조시간(hr)
            "sum_ss_hr",  # 합계 일조 시간(hr)
        ]

        # 0으로 채울(fillzero) 컬럼들; 5개
        self.fillzero_cols = [
            "sum_rn",  # 일강수량(mm)
            "mi10_max_rn",  # 10분 최다강수량(mm)
            "mi10_max_rn_hrmt",  # 10분 최다강수량 시각(hhmi)
            "hr1_max_rn",  # 1시간 최다강수량(mm)
            "hr1_max_rn_hrmt",  # 1시간 최다 강수량 시각(hhmi)
        ]

        # drop 할 column 들; 23개
        self.cols_to_drop = [
            "avg_cm10_te",
            "avg_cm20_te",
            "avg_cm30_te",
            "avg_cm5_te",
            "avg_m05_te",
            "avg_m10_te",
            "avg_m15_te",
            "avg_m30_te",
            "avg_m50_te",
            "dd_mefs",
            "dd_mefs_hrmt",
            "dd_mes",
            "dd_mes_hrmt",
            "hr1_max_icsr",
            "hr1_max_icsr_hrmt",
            "iscs",
            "n99_rn",
            "sum_dpth_fhsc",
            "sum_fog_dur",
            "sum_gsr",
            "sum_lrg_ev",
            "sum_rn_dur",
            "sum_sml_ev",
        ]

    def fit(self, x, y=None):
        """
        학습 단계로, 이 경우 따로 학습할 파라미터가 없으므로 self를 반환합니다.
        """
        return self

    def transform(self, x, y=None):
        """
        주어진 데이터의 결측치를 채웁니다.
        """
        # 원본 데이터를 변경하지 않기 위해 복사본 생성
        result = x.copy()

        # 날릴 컬럼 날림
        result = result.drop(self.cols_to_drop, axis=1)

        # 나머지는 0으로 채움
        result[self.fillzero_cols] = result[self.fillzero_cols].fillna(0)

        # 각 선형 보간할 columns 에 대해 결측치 처리 수행
        for column in self.interpolate_cols:
            result = self._fill_single_column_grouped(result, column)

        return result

    def fit_transform(self, x, y=None, **kwargs):
        """fit과 transform을 한 번에 수행합니다."""
        return self.fit(x).transform(x)

    def _fill_single_column_grouped(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """
        그룹별로 단일 컬럼의 결측치를 채우는 내부 메서드
        """

        result = df.copy()

        # 그룹별로 처리
        for _, group_df in result.groupby(self.GROUP_BY_COLUMN):
            # 시간순 정렬
            group_df_sorted = group_df.sort_values("tm")

            # 보간 적용 (선형 보간이 기본)
            group_df_sorted[col] = group_df_sorted[col].interpolate(method="linear")

            # 앞쪽 결측값은 첫 유효값으로 채움
            group_df_sorted[col] = group_df_sorted[col].bfill()

            # 뒤쪽 결측값은 마지막 유효값으로 채움
            group_df_sorted[col] = group_df_sorted[col].ffill()

            # 결과 반영
            result.loc[group_df_sorted.index, col] = group_df_sorted[col]

        return result
