from sklearn.ensemble import RandomForestRegressor

from src.models.base import BaseModel


class RandomForestModel(BaseModel):
    """RandomForestModel 모델 클래스"""

    NAME = "random_forest"

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
        self.model = RandomForestRegressor(**self.params)
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
            "n_estimators": 100,  # 모델에서 사용할 트리의 개수 (기본값: 100)
            "criterion": "squared_error",  # 분기 품질을 측정하는 함수 (기본값: 'squared_error')
            "max_depth": None,  # 트리의 최대 깊이 (기본값: None, 제한 없음)
            "min_samples_split": 2,  # 내부 노드를 분할하는 데 필요한 최소 샘플 수 (기본값: 2)
            "min_samples_leaf": 1,  # 리프 노드에 필요한 최소 샘플 수 (기본값: 1)
            "max_features": "sqrt",  # 최적의 분할을 찾을 때 고려할 특성의 수 (기본값: 'sqrt')
            "bootstrap": True,  # 부트스트랩 샘플 사용 여부 (기본값: True)
            "random_state": None,  # 난수 생성을 위한 시드값 (기본값: None)
            "n_jobs": -1,  # 병렬 처리에 사용할 코어 수 (기본값: None)
        }
