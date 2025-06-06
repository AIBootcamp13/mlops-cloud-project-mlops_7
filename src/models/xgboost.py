from xgboost import XGBClassifier

from src.models.base import BaseModel


class XGBoostModel(BaseModel):
    """XGBoost 모델 클래스"""

    NAME = "xgboost"

    def __init__(self, params: dict):
        super().__init__(name=self.NAME)

        self.params = params
        self.model = None

    def fit(self, x, y):
        """
        모델 학습 메서드

        Args:
            x (DataFrame): 학습 특성 (이미 LabelEncoder로 변환된 상태)
            y (ndarray/Series): 타겟 변수
        """
        self.model = XGBClassifier(**self.params)
        self.model.fit(x, y)
        return self

    def predict(self, x):
        """
        예측 메서드

        Args:
            x (DataFrame): 예측할 데이터 (이미 LabelEncoder로 변환된 상태)

        Returns:
            ndarray: 예측값
        """
        if self.model is None:
            raise ValueError(f"{self.NAME} 모델이 학습되지 않았습니다.")

        return self.model.predict(x)

    @staticmethod
    def default_params() -> dict:
        return {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 6,
            "min_child_weight": 1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "n_jobs": -1,
        }
