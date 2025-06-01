FROM apache/airflow:2.11.0-python3.11

USER root

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Poetry 설치
RUN pip install --no-cache-dir poetry

# 작업 디렉토리 설정
WORKDIR /opt/project

# 프로젝트 의존성 복사 및 설치
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && \
    poetry install --with airflow --no-interaction

# 소스 코드 복사
COPY src ./src

# 작업 디렉토리 재설정
WORKDIR /opt/airflow

# Airflow 관련 디렉토리 복사
COPY airflow/dags ./dags
COPY airflow/plugins ./plugins
COPY airflow/config ./config

# logs 디렉토리 생성 (복사하지 않고 빈 디렉토리 생성)
RUN mkdir -p ./logs

# PYTHONPATH 설정
ENV PYTHONPATH=/opt/airflow:/opt/project:$PYTHONPATH
