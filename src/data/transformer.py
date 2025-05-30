from sklearn.base import BaseEstimator, TransformerMixin


class WeatherDataTransformer(BaseEstimator, TransformerMixin):
    """기상 데이터의 모든 column 에 대해서 인코딩하는 class"""
