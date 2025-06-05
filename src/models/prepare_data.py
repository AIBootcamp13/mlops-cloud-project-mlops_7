"""
데이터 준비 모듈
- S3에서 데이터 로드
- 시계열 기준 데이터셋 분할 (train: 2020-2022, validation: 2023, test: 2024)
- 전처리 및 피처 엔지니어링
"""

import pandas as pd 
import numpy as np
from datetime import datetime
from typing import Tuple, Dict
from sklearn.preprocessing import Standard 