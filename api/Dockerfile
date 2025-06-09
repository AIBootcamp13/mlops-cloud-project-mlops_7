FROM python:3.11-slim

WORKDIR /app

# 필요한 시스템 라이브러리 설치 (libgomp1이 libgomp.so.1 파일 제공)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install -U pip setuptools
RUN pip install --no-cache-dir poetry

# 프로젝트 의존성만 복사
COPY pyproject.toml ./

# API 관련 의존성만 설치
RUN poetry config virtualenvs.create false && \
    poetry install --with api --no-interaction

# 소스 코드 복사
COPY src /app/src
COPY api /app/api

# PYTHONPATH 설정
ENV PYTHONPATH=/app

# API 서버 실행
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
