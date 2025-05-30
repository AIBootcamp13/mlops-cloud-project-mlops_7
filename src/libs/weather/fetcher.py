from __future__ import annotations

import datetime

import requests

from src.libs.weather.asosstation import AsosStation
from src.libs.weather.vo import AsosDataResponse
from src.utils import config
from src.utils.log import get_logger


_logger = get_logger(__name__)


class AsosDataFetcher:
    """
    ASOS(Automated Synoptic Observing System, 자동기상관측장비) 로
    측정된 기상 데이터를 가져오는 클래스
    """

    FORMAT_DATE = "%Y%m%d"
    MAX_COUNT_PER_PAGE = 999  # 한 페이지당 가져올 아이템 수

    def __init__(self, service_key: str):
        self.service_key = service_key
        self.endpoint = config.WEATHER_API_URL

    def fetch(
        self,
        asos_station: AsosStation,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        page: int,
        count: int,
    ) -> AsosDataResponse:
        params = {
            "serviceKey": self.service_key,
            "pageNo": page,
            "numOfRows": count,
            "dataType": "JSON",
            "dataCd": "ASOS",
            "dateCd": "DAY",
            "startDt": start_date.strftime(self.FORMAT_DATE),
            "endDt": end_date.strftime(self.FORMAT_DATE),
            "stnIds": asos_station.value,
        }

        try:
            response = requests.get(self.endpoint, params=params)
        except requests.RequestException as e:
            _logger.warning(f"Failed to load ASOS data; {e}", extra=params)
            return AsosDataResponse.create_default()

        return AsosDataResponse.create(response)

    def fetch_all(
        self, asos_station: AsosStation, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> AsosDataResponse:
        all_items = []
        page = 1
        total_count = None

        while True:
            # 현재 페이지의 데이터 가져오기
            response = self.fetch(
                asos_station=asos_station,
                start_date=start_date,
                end_date=end_date,
                page=page,
                count=self.MAX_COUNT_PER_PAGE,
            )

            # 요청이 실패했거나 아이템이 없는 경우 중단
            if not response.is_success:
                if page == 1:  # 첫 페이지부터 실패했다면 실패 응답 반환
                    return response
                break

            # 아이템 누적
            all_items.extend(response.items)

            # 첫 응답에서 total_count 확인
            if total_count is None:
                total_count = response.total_count

            # 모든 데이터를 가져왔는지 확인
            if len(all_items) >= response.total_count or len(response.items) < self.MAX_COUNT_PER_PAGE:
                break

            # 다음 페이지로 이동
            page += 1

        # 수집된 모든 데이터로 새로운 AsosDataResponse 생성
        return AsosDataResponse(
            is_success=True,
            items=all_items,
            page=1,  # 모든 페이지를 가져왔으므로 페이지 번호는 의미가 없음
            count=len(all_items),
            total_count=total_count or len(all_items),
        )

    @staticmethod
    def create() -> AsosDataFetcher:
        return AsosDataFetcher(service_key=config.WEATHER_API_KEY)
