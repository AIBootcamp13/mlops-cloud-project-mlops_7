import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_rmse(y_true, y_pred):
    """
    RMSE(Root Mean Squared Error) 계산

    Args:
        y_true (array): 실제값
        y_pred (array): 예측값

    Returns:
        float: RMSE 값
    """
    return np.sqrt(mean_squared_error(y_true, y_pred))


def calculate_mae(y_true, y_pred):
    """
    MAE(Mean Absolute Error) 계산

    Args:
        y_true (array): 실제값
        y_pred (array): 예측값

    Returns:
        float: MAE 값
    """
    return mean_absolute_error(y_true, y_pred)


def calculate_r2(y_true, y_pred):
    """
    R^2 Score 계산

    Args:
        y_true (array): 실제값
        y_pred (array): 예측값

    Returns:
        float: R^2 값
    """
    return r2_score(y_true, y_pred)


def evaluate_model(y_true, y_pred):
    """
    다양한 평가 지표 계산

    Args:
        y_true (array): 실제값
        y_pred (array): 예측값

    Returns:
        dict: 평가 지표 딕셔너리
    """
    return {
        "rmse": calculate_rmse(y_true, y_pred),
        "mae": calculate_mae(y_true, y_pred),
        "r2": calculate_r2(y_true, y_pred),
    }
