from src.models.lightgbm import LightGBMModel
from src.models.random_forest import RandomForestModel
from src.models.xgboost import XGBoostModel


MODEL_REGISTRY = {
    RandomForestModel.NAME: RandomForestModel,
    XGBoostModel.NAME: XGBoostModel,
    LightGBMModel.NAME: LightGBMModel,
}
