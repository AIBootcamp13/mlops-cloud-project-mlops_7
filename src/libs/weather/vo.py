from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import requests

from src.libs.weather.asosstation import AsosStation
from src.utils import convert_camel_to_snake
from src.utils.log import get_logger


asos_logger = get_logger(__name__)


@dataclass(frozen=True)
class AsosData:
    TM_FORMAT = "%Y-%m-%d"

    stn_id: AsosStation  # 지점 번호(종관기상관측 지점 번호 첨부 참조)
    stn_nm: str  # 지점명(종관기상관측 지점명 첨부 참조)
    tm: datetime  # 시간(일시)

    avg_ta: float | None  # 평균 기온(°C)
    min_ta: float | None  # 최저 기온(°C)
    min_ta_hrmt: int | None  # 최저 기온 시각(hhmi)
    max_ta: float | None  # 최고 기온(°C)
    max_ta_hrmt: int | None  # 최고 기온 시각(hhmi)
    sum_rn_dur: float | None  # 강수 계속시간(hr)
    mi10_max_rn: float | None  # 10분 최다강수량(mm)
    mi10_max_rn_hrmt: int | None  # 10분 최다강수량 시각(hhmi)
    hr1_max_rn: float | None  # 1시간 최다강수량(mm)
    hr1_max_rn_hrmt: int | None  # 1시간 최다 강수량 시각(hhmi)
    sum_rn: float | None  # 일강수량(mm)
    max_ins_ws: float | None  # 최대 순간풍속(m/s)
    max_ins_ws_wd: int | None  # 최대 순간 풍속 풍향(16방위)
    max_ins_ws_hrmt: int | None  # 최대 순간풍속 시각(hhmi)
    max_ws: float | None  # 최대 풍속(m/s)
    max_ws_wd: int | None  # 최대 풍속 풍향(16방위)
    max_ws_hrmt: int | None  # 최대 풍속 시각(hhmi)
    avg_ws: float | None  # 평균 풍속(m/s)
    hr24_sum_rws: int | None  # 풍정합(100m)
    max_wd: int | None  # 최다 풍향(16방위)
    avg_td: float | None  # 평균 이슬점온도(°C)
    min_rhm: int | None  # 최소 상대습도(%)
    min_rhm_hrmt: int | None  # 평균 상대습도 시각(hhmi)
    avg_rhm: int | None  # 평균 상대습도(%)
    avg_pv: float | None  # 평균 증기압(hPa)
    avg_pa: float | None  # 평균 현지기압(hPa)
    max_ps: float | None  # 최고 해면 기압(hPa)
    max_ps_hrmt: int | None  # 최고 해면기압 시각(hhmi)
    min_ps: float | None  # 최저 해면기압(hPa)
    min_ps_hrmt: int | None  # 최저 해면기압 시각(hhmi)
    avg_ps: float | None  # 평균 해면기압(hPa)
    ss_dur: float | None  # 가조시간(hr)
    sum_ss_hr: float | None  # 합계 일조 시간(hr)
    hr1_max_icsr_hrmt: int | None  # 1시간 최다 일사 시각(hhmi)
    hr1_max_icsr: float | None  # 1시간 최다 일사량(MJ/m2)
    sum_gsr: float | None  # 합계 일사량(MJ/m2)
    dd_mefs: float | None  # 일 최심신적설(cm)
    dd_mefs_hrmt: int | None  # 일 최심신적설 시각(hhmi)
    dd_mes: float | None  # 일 최심적설(cm)
    dd_mes_hrmt: int | None  # 일 최심적설 시각(hhmi)
    sum_dpth_fhsc: float | None  # 합계 3시간 신적설(cm)
    avg_tca: float | None  # 평균 전운량(10분위)
    avg_lmac: float | None  # 평균 중하층운량(10분위)
    avg_ts: float | None  # 평균 지면온도(°C)
    min_tg: float | None  # 최저 초상온도(°C)
    avg_cm5_te: float | None  # 평균 5cm 지중온도(°C)
    avg_cm10_te: float | None  # 평균10cm 지중온도(°C)
    avg_cm20_te: float | None  # 평균 20cm지중온도(°C)
    avg_cm30_te: float | None  # 평균 30cm 지중온도(°C)
    avg_m05_te: float | None  # 0.5m 지중온도(°C)
    avg_m10_te: float | None  # 1.0m 지중온도(°C)
    avg_m15_te: float | None  # 1.5m 지중온도(°C)
    avg_m30_te: float | None  # 3.0m 지중온도(°C)
    avg_m50_te: float | None  # 5.0m 지중온도(°C)
    sum_lrg_ev: float | None  # 합계 대형증발량(mm)
    sum_sml_ev: float | None  # 합계 소형증발량(mm)
    n99_rn: float | None  # 9-9강수(mm)
    iscs: str | None  # 일기현상
    sum_fog_dur: float | None  # 안개 계속 시간(hr)

    @classmethod
    def create(cls, item_dict: dict) -> AsosData:
        converted_data = {}
        # 키 변환: camelCase -> snake_case
        for key, value in item_dict.items():
            # 공백 제거 및 스네이크 케이스로 변환
            snake_key = convert_camel_to_snake(key)

            if key == "stnId":
                converted_data[snake_key] = AsosStation(int(value))
                continue

            if key == "tm":
                converted_data[snake_key] = datetime.strptime(value, cls.TM_FORMAT)
                continue

            striped_value = str(value) if value else ""
            if not striped_value:
                converted_data[snake_key] = None
                continue

            try:
                float_value = float(striped_value)
                converted_data[snake_key] = int(float_value) if float_value.is_integer() else float_value
            except ValueError:
                # str type 의 value
                converted_data[snake_key] = value

        return cls(**converted_data)


@dataclass(frozen=True)
class AsosDataResponse:
    class Key(str, Enum):
        RESPONSE = "response"

        HEADER = "header"
        BODY = "body"

        RESULT_CODE = "resultCode"

        ITEMS = "items"
        PAGE_NO = "pageNo"
        NUM_OF_ROWS = "numOfRows"
        TOTAL_COUNT = "totalCount"

        ITEM = "item"

    RESULT_CODE_SUCCESS = "00"

    is_success: bool
    items: list[AsosData]
    page: int
    count: int
    total_count: int

    def __repr__(self):
        display_attrs = {
            "is_success": self.is_success,
            "page": self.page,
            "count": self.count,
            "total_count": self.total_count,
        }
        return json.dumps(display_attrs, ensure_ascii=False, indent=2)

    @classmethod
    def create(cls, response: requests.Response) -> AsosDataResponse:
        fail_response = cls.create_default()

        if not response.ok:  # HTTP 실패
            asos_logger.warning(f"Failed to load ASOS data; {response.text}")
            return AsosDataResponse.create_default()

        try:
            data = response.json()

            # 필요한 키들이 존재하는지 확인하고 데이터 추출
            response_data = data.get(cls.Key.RESPONSE, {})
            header = response_data.get(cls.Key.HEADER, {})
            body = response_data.get(cls.Key.BODY, {})
            items_dict = body.get(cls.Key.ITEMS, {})
            item_list = items_dict.get(cls.Key.ITEM, [])

            if header.get(cls.Key.RESULT_CODE) != cls.RESULT_CODE_SUCCESS:
                asos_logger.warning(f"Failed to load ASOS data; {header}", extra=data)
                return fail_response

            # 필수 데이터가 없으면 실패 응답 반환
            if not item_list:
                asos_logger.warning("Failed to load ASOS data; Empty list", extra=data)
                return fail_response

            # 아이템 리스트 생성
            items = [AsosData.create(item) for item in item_list]
            asos_logger.info("Success to load ASOS data.")
            # 성공 응답 반환
            return cls(
                is_success=True,
                items=items,
                page=body.get(cls.Key.PAGE_NO, 1),
                count=body.get(cls.Key.NUM_OF_ROWS, 1),
                total_count=body.get(cls.Key.TOTAL_COUNT, 0),
            )
        except (ValueError, KeyError, TypeError) as e:
            # JSON 파싱 오류나 기타 예외 발생 시 실패 응답 반환
            asos_logger.warning(f"Failed to parse ASOS data response:\n\t{e!s}", extra={"text": response.text})
            return fail_response

    @classmethod
    def create_default(cls) -> AsosDataResponse:
        return cls(
            is_success=False,
            items=[],
            page=0,
            count=0,
            total_count=0,
        )
