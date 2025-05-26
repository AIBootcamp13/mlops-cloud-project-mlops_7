FROM python:3.11-slim

WORKDIR /app

# Poetry 설치
RUN pip install -U pip setuptools
RUN pip install --no-cache-dir poetry

# 프로젝트 의존성만 복사
COPY pyproject.toml poetry.lock* ./

# API 관련 의존성만 설치
RUN poetry config virtualenvs.create false && \
    poetry install --only api --no-interaction

# 소스 코드 복사
COPY src /app/src
COPY api /app/api

# PYTHONPATH 설정
ENV PYTHONPATH=/app:$PYTHONPATH

# API 서버 실행
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
