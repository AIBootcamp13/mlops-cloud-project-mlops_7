import pandas as pd
from sklearn.preprocessing import LabelEncoder

def simplify_iscs(value: str) -> str:
    """
    iscs 문자열을 대표적인 날씨 상태로 정제
    """
    if pd.isna(value) or value.strip() == "":
        return "없음"  # 결측 취급
    if "비" in value:
        return "비"
    elif "눈" in value:
        return "눈"
    elif "안개" in value:
        return "안개"
    elif "맑음" in value or "깨끗" in value:
        return "맑음"
    else:
        return "기타"

class WeatherPreprocessor:
    def __init__(self):
        self.label_encoders = {}
        self.target_encoder = LabelEncoder()
        self.feature_cols = []
        self.target_col = "iscs"

    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        df = df.copy()

        # 1. iscs 전처리
        df[self.target_col] = df[self.target_col].astype(str).apply(simplify_iscs)
        df = df[df[self.target_col] != "없음"]

        # 2. 전체 범주형 인코딩
        for col in df.columns:
            if col == self.target_col:
                continue
            self.label_encoders[col] = LabelEncoder()
            df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
            self.feature_cols.append(col)

        # 3. 타겟 인코딩
        df[self.target_col] = self.target_encoder.fit_transform(df[self.target_col].astype(str))

        X = df[self.feature_cols]
        y = df[self.target_col]
        return X, y

    def transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        df = df.copy()

        # iscs 정제
        df[self.target_col] = df[self.target_col].astype(str).apply(simplify_iscs)

        for col in self.feature_cols:
            if col in self.label_encoders:
                df[col] = self.label_encoders[col].transform(df[col].astype(str))

        y = self.target_encoder.transform(df[self.target_col].astype(str))
        X = df[self.feature_cols]
        return X, y