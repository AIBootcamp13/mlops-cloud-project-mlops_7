# src/models/__init__.py

from src.models.random_forest import RandomForestModel
from src.models.xgboost import XGBoostModel
from src.models.lightgbm import LightGBMModel

MODEL_REGISTRY = {
    "random_forest": RandomForestModel,
    "xgboost": XGBoostModel,
    "lightgbm": LightGBMModel,
}