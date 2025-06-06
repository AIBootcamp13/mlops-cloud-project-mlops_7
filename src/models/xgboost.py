from xgboost import XGBRegressor

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
        self.model = XGBRegressor(**self.params)
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
            "n_estimators": 100,  # 부스팅 단계 수 (기본값: 100)
            "learning_rate": 0.01,  # 학습률 (기본값: 0.3)
            "max_depth": 6,  # 트리의 최대 깊이 (기본값: 6)
            "min_child_weight": 1,  # 자식 노드에 필요한 최소 가중치 합계 (기본값: 1)
            "gamma": 0,  # 노드 분할 시 발생하는 손실 감소에 대한 최소값 (기본값: 0)
            "subsample": 1.0,  # 훈련 인스턴스의 하위 샘플 비율 (기본값: 1)
            "colsample_bytree": 1.0,  # 각 트리 구성 시 사용되는 특성의 비율 (기본값: 1)
            "objective": "reg:squarederror",  # 목적 함수 (기본값: 'reg:squarederror')
            "reg_alpha": 0,  # L1 정규화 항 (기본값: 0)
            "reg_lambda": 1,  # L2 정규화 항 (기본값: 1)
            "random_state": None,  # 난수 생성을 위한 시드값 (기본값: None)
            "tree_method": "hist",
            "enable_categorical": True,
            "n_jobs": -1,  # 병렬 처리에 사용할 스레드 수 (기본값: None)
        }
