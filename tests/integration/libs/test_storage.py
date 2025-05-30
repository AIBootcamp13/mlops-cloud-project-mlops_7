import time
import uuid

import pandas as pd
import pytest

from src.libs.storage import Storage


@pytest.fixture
def storage_instance():
    """실제 Ncloud 서비스와 연결된 Storage 인스턴스를 생성합니다."""
    # config에서 설정값을 가져와 실제 인스턴스 생성
    return Storage.create()


@pytest.fixture
def sample_dataframe():
    """테스트용 샘플 데이터프레임 생성"""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 30.1],
        }
    )


@pytest.fixture
def unique_filename():
    """테스트마다 고유한 파일명 생성"""
    return f"test-file-{uuid.uuid4()}"


def test_connection(storage_instance):
    """Ncloud 스토리지와의 연결 테스트"""
    # 단순히 버킷 리스트를 요청하여 연결 확인
    response = storage_instance.client.list_buckets()
    assert response["ResponseMetadata"]["HTTPStatusCode"] == Storage.STATUS_OK
    print(f"연결 성공, 사용 가능한 버킷: {[b['Name'] for b in response['Buckets']]}")


def test_make_csv_keys(storage_instance, unique_filename):
    """키 생성 함수 테스트"""
    datasets_key = storage_instance.generate_csv_key_in_datasets(unique_filename)
    features_key = storage_instance.generate_csv_key_in_features(unique_filename)

    assert datasets_key.startswith(f"{Storage.DATASETS_DIR}/")
    assert datasets_key.endswith(f"{unique_filename}.csv")

    assert features_key.startswith(f"{Storage.FEATURES_DIR}/")
    assert features_key.endswith(f"{unique_filename}.csv")


def test_full_upload_read_delete_cycle(storage_instance, sample_dataframe, unique_filename):
    """업로드, 읽기, 삭제의 전체 사이클 테스트"""
    # 1. 키 생성
    key = storage_instance.generate_csv_key_in_datasets(unique_filename)
    print(f"테스트 키: {key}")

    try:
        # 2. 업로드 테스트
        upload_result = storage_instance.upload_dataframe(sample_dataframe, key)
        assert upload_result is True
        print(f"업로드 성공: {key}")

        # 잠시 대기하여 업로드 완료 확인
        time.sleep(2)

        # 3. 읽기 테스트
        read_df = storage_instance.read_as_dataframe(key)
        assert read_df is not None
        assert len(read_df) == len(sample_dataframe)
        assert all(col in read_df.columns for col in sample_dataframe.columns)
        print(f"읽기 성공, 데이터: \n{read_df.head()}")

    finally:
        # 4. 삭제 테스트 (테스트 후 정리)
        delete_result = storage_instance.delete(key)
        assert delete_result is True
        print(f"삭제 성공: {key}")

        # 삭제 후 파일이 실제로 없는지 확인
        time.sleep(2)
        read_after_delete = storage_instance.read_as_dataframe(key)
        assert read_after_delete is None
        print("삭제 확인 완료")


def test_upload_to_features(storage_instance, sample_dataframe, unique_filename):
    """특성 디렉토리에 파일 업로드 테스트"""
    key = storage_instance.generate_csv_key_in_features(unique_filename)
    print(f"특성 테스트 키: {key}")

    try:
        # 업로드 테스트
        upload_result = storage_instance.upload_dataframe(sample_dataframe, key, index=True)
        assert upload_result is True
        print(f"특성 디렉토리 업로드 성공: {key}")

        # 잠시 대기하여 업로드 완료 확인
        time.sleep(2)

        # 읽기 테스트 - 인덱스를 포함하여 업로드했으므로 열이 하나 더 있어야 함
        read_df = storage_instance.read_as_dataframe(key)
        assert read_df is not None
        assert len(read_df) == len(sample_dataframe)
        print(f"특성 디렉토리 읽기 성공, 데이터: \n{read_df.head()}")

    finally:
        # 삭제 테스트 (테스트 후 정리)
        delete_result = storage_instance.delete(key)
        assert delete_result is True
        print(f"특성 디렉토리 삭제 성공: {key}")


def test_nonexistent_file(storage_instance):
    """존재하지 않는 파일 읽기 시도"""
    # 존재하지 않을 가능성이 높은 무작위 키 생성
    nonexistent_key = f"nonexistent/{uuid.uuid4()}.csv"

    # 읽기 시도
    result = storage_instance.read_as_dataframe(nonexistent_key)
    assert result is None
    print(f"존재하지 않는 파일 테스트 성공: {nonexistent_key}")


def test_large_dataframe(storage_instance, unique_filename):
    """대용량 데이터프레임 처리 테스트"""
    # 크기가 큰 데이터프레임 생성 (약 10,000행)
    large_df = pd.DataFrame(
        {
            "id": range(10000),
            "value1": [f"test-value-{i}" for i in range(10000)],
            "value2": [i * 1.5 for i in range(10000)],
        }
    )

    key = storage_instance.generate_csv_key_in_datasets(unique_filename)
    print(f"대용량 테스트 키: {key}")

    try:
        # 업로드 테스트
        start_time = time.time()
        upload_result = storage_instance.upload_dataframe(large_df, key)
        upload_time = time.time() - start_time
        assert upload_result is True
        print(f"대용량 업로드 성공: {key}, 소요 시간: {upload_time:.2f}초")

        # 잠시 대기하여 업로드 완료 확인
        time.sleep(2)

        # 읽기 테스트
        start_time = time.time()
        read_df = storage_instance.read_as_dataframe(key)
        read_time = time.time() - start_time
        assert read_df is not None
        assert len(read_df) == len(large_df)
        print(f"대용량 읽기 성공, 소요 시간: {read_time:.2f}초, 행 수: {len(read_df)}")

    finally:
        # 삭제 테스트 (테스트 후 정리)
        delete_result = storage_instance.delete(key)
        assert delete_result is True
        print(f"대용량 파일 삭제 성공: {key}")
