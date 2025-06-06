from abc import ABC, abstractmethod


class BaseModel(ABC):
    """모델의 기본 추상 클래스"""

    def __init__(self, name):
        self.name = name
        self.model = None

    @abstractmethod
    def fit(self, x, y):
        """모델 학습 메서드"""

    @abstractmethod
    def predict(self, x):
        """예측 메서드"""
