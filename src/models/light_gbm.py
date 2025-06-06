import lightgbm as lgb

from src.models.base import BaseModel


class LightGBMModel(BaseModel):
    """LightGBM 모델 클래스"""

    NAME = "lightgbm"

    def __init__(self, categorical_features: list[str], params: dict):
        super().__init__(name=self.NAME)

        self.categorical_features = categorical_features
        self.params = params
        self.model = None

    def fit(self, x, y):
        """
        모델 학습 메서드

        Args:
            x (DataFrame): 학습 특성 (이미 LabelEncoder로 변환된 상태)
            y (ndarray/Series): 타겟 변수
        """
        # LightGBM 데이터셋 생성
        train_data = lgb.Dataset(data=x, label=y, categorical_feature=self.categorical_features)

        # 모델 학습
        self.model = lgb.train(
            params=self.params,
            train_set=train_data,
        )

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
            "n_estimators": 200,  # 부스팅 단계 수 (기본값: 100)
            "learning_rate": 0.01,  # 학습률 (기본값: 0.1)
            "max_depth": -1,  # 트리의 최대 깊이 (기본값: -1, 제한 없음)
            "num_leaves": 31,  # 한 트리에 포함될 최대 리프 노드 수 (기본값: 31)
            "min_child_samples": 20,  # 리프 노드가 되기 위한 최소 데이터 수 (기본값: 20)
            "subsample": 1.0,  # 훈련 인스턴스의 하위 샘플 비율 (기본값: 1.0)
            "colsample_bytree": 1.0,  # 각 트리 구성 시 사용되는 특성의 비율 (기본값: 1.0)
            "reg_alpha": 0,  # L1 정규화 항 (기본값: 0)
            "reg_lambda": 0,  # L2 정규화 항 (기본값: 0)
            "random_state": None,  # 난수 생성을 위한 시드값 (기본값: None)
            "boosting_type": "gbdt",  # 부스팅 방법 (기본값: 'gbdt')
            "objective": "regression",
            "metric": "rmse",
            "n_jobs": -1,  # 병렬 처리에 사용할 스레드 수 (기본값: None)
        }
