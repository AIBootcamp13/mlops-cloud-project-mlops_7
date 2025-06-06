from config.keys import KEY_LAST_FETCHING_DATE

from airflow.decorators import task
from airflow.models import Variable


FIRST_COLLECTING_DURATION = 5  # 연단위


@task
def get_last_fetching_date() -> str:
    """Variable 에서 마지막 수집 날짜 문자열(%Y%m%d)조회. 없으면 5년 전으로 초기화"""
    from datetime import datetime

    from dateutil.relativedelta import relativedelta

    from src.utils.config import DEFAULT_DATE_FORMAT

    fetching_date_str = Variable.get(KEY_LAST_FETCHING_DATE, default_var=None)
    if fetching_date_str is None:
        fetching_date = datetime.now() - relativedelta(years=FIRST_COLLECTING_DURATION)
        return fetching_date.strftime(DEFAULT_DATE_FORMAT)
    return fetching_date_str


@task
def fetch_and_upload_asos_data(_: str) -> str:
    """기상청 API 로 데이터 수집 후 S3 업로드"""
    from datetime import datetime

    from src.utils.config import DEFAULT_DATE_FORMAT

    # TODO 나중에 배포시에 변경될 예정입니다.
    # end_date = datetime(2025, 5, 31)
    # end_date = datetime.now() - timedelta(days=1)
    # collector = Collector(storage=storage, fetcher=AsosDataFetcher.create())
    # collector.collect_all_asos_data(start_date=start_date, end_date=end_date)
    # collector.upload_all_asos_data(with_index=False)
    return datetime(2025, 5, 31).strftime(DEFAULT_DATE_FORMAT)


@task
def update_last_fetching_date(new_end_date_str: str) -> str:
    """Variable 에 새로운 수집 날짜 저장"""
    Variable.set(KEY_LAST_FETCHING_DATE, new_end_date_str)
    return new_end_date_str
