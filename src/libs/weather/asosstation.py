from enum import Enum


class AsosStation(int, Enum):
    """공공 데이터 포털의 기상청 종관 데이터의 종관 지점을 나타내는 enum"""

    SOKCHO = 90  # 속초
    NORTH_CHUNCHEON = 93  # 북춘천
    CHEORWON = 95  # 철원
    DONGDUCHEON = 98  # 동두천
    PAJU = 99  # 파주
    DAEGWALLYEONG = 100  # 대관령
    CHUNCHEON = 101  # 춘천
    BAENGNYEONGDO = 102  # 백령도
    NORTH_GANGNEUNG = 104  # 북강릉
    GANGNEUNG = 105  # 강릉
    DONGHAE = 106  # 동해
    SEOUL = 108  # 서울
    INCHEON = 112  # 인천
    WONJU = 114  # 원주
    ULLEUNGDO = 115  # 울릉도
    SUWON = 119  # 수원
    YEONGWOL = 121  # 영월
    CHUNGJU = 127  # 충주
    SEOSAN = 129  # 서산
    ULJIN = 130  # 울진
    CHEONGJU = 131  # 청주
    DAEJEON = 133  # 대전
    CHUPUNGNYEONG = 135  # 추풍령
    ANDONG = 136  # 안동
    SANGJU = 137  # 상주
    POHANG = 138  # 포항
    GUNSAN = 140  # 군산
    DAEGU = 143  # 대구
    JEONJU = 146  # 전주
    ULSAN = 152  # 울산
    CHANGWON = 155  # 창원
    GWANGJU = 156  # 광주
    BUSAN = 159  # 부산
    TONGYEONG = 162  # 통영
    MOKPO = 165  # 목포
    YEOSU = 168  # 여수
    HEUKSANDO = 169  # 흑산도
    WANDO = 170  # 완도
    GOCHANG = 172  # 고창
    SUNCHEON = 174  # 순천
    HONGSEONG = 177  # 홍성
    JEJU = 184  # 제주
    GOSAN = 185  # 고산
    SEONGSAN = 188  # 성산
    SEOGWIPO = 189  # 서귀포
    JINJU = 192  # 진주
    GANGHWA = 201  # 강화
    YANGPYEONG = 202  # 양평
    ICHEON = 203  # 이천
    INJE = 211  # 인제
    HONGCHEON = 212  # 홍천
    TAEBAEK = 216  # 태백
    JEONGSEON = 217  # 정선군
    JECHEON = 221  # 제천
    BOEUN = 226  # 보은
    CHEONAN = 232  # 천안
    BORYEONG = 235  # 보령
    BUYEO = 236  # 부여
    GEUMSAN = 238  # 금산
    SEJONG = 239  # 세종
    BUAN = 243  # 부안
    IMSIL = 244  # 임실
    JEONGEUP = 245  # 정읍
    NAMWON = 247  # 남원
    JANGSU = 248  # 장수
    GOCHANG_COUNTY = 251  # 고창군
    YEONGGWANG = 252  # 영광군
    GIMHAE = 253  # 김해시
    SUNCHANG = 254  # 순창군
    NORTH_CHANGWON = 255  # 북창원
    YANGSAN = 257  # 양산시
    BOSEONG = 258  # 보성군
    GANGJIN = 259  # 강진군
    JANGHEUNG = 260  # 장흥
    HAENAM = 261  # 해남
    GOHEUNG = 262  # 고흥
    UIRYEONG = 263  # 의령군
    HAMYANG = 264  # 함양군
    GWANGYANG = 266  # 광양시
    JINDO = 268  # 진도군
    BONGHWA = 271  # 봉화
    YEONGJU = 272  # 영주
    MUNGYEONG = 273  # 문경
    CHEONGSONG = 276  # 청송군
    YEONGDEOK = 277  # 영덕
    UISEONG = 278  # 의성
    GUMI = 279  # 구미
    YEONGCHEON = 281  # 영천
    GYEONGJU = 283  # 경주시
    GEOCHANG = 284  # 거창
    HAPCHEON = 285  # 합천
    MIRYANG = 288  # 밀양
    SANCHEONG = 289  # 산청
    GEOJE = 294  # 거제
    NAMHAE = 295  # 남해


KOR_TO_ENUM = {
    "속초": AsosStation.SOKCHO,
    "북춘천": AsosStation.NORTH_CHUNCHEON,
    "철원": AsosStation.CHEORWON,
    "동두천": AsosStation.DONGDUCHEON,
    "파주": AsosStation.PAJU,
    "대관령": AsosStation.DAEGWALLYEONG,
    "춘천": AsosStation.CHUNCHEON,
    "백령도": AsosStation.BAENGNYEONGDO,
    "북강릉": AsosStation.NORTH_GANGNEUNG,
    "강릉": AsosStation.GANGNEUNG,
    "동해": AsosStation.DONGHAE,
    "서울": AsosStation.SEOUL,
    "인천": AsosStation.INCHEON,
    "원주": AsosStation.WONJU,
    "울릉도": AsosStation.ULLEUNGDO,
    "수원": AsosStation.SUWON,
    "영월": AsosStation.YEONGWOL,
    "충주": AsosStation.CHUNGJU,
    "서산": AsosStation.SEOSAN,
    "울진": AsosStation.ULJIN,
    "청주": AsosStation.CHEONGJU,
    "대전": AsosStation.DAEJEON,
    "추풍령": AsosStation.CHUPUNGNYEONG,
    "안동": AsosStation.ANDONG,
    "상주": AsosStation.SANGJU,
    "포항": AsosStation.POHANG,
    "군산": AsosStation.GUNSAN,
    "대구": AsosStation.DAEGU,
    "전주": AsosStation.JEONJU,
    "울산": AsosStation.ULSAN,
    "창원": AsosStation.CHANGWON,
    "광주": AsosStation.GWANGJU,
    "부산": AsosStation.BUSAN,
    "통영": AsosStation.TONGYEONG,
    "목포": AsosStation.MOKPO,
    "여수": AsosStation.YEOSU,
    "흑산도": AsosStation.HEUKSANDO,
    "완도": AsosStation.WANDO,
    "고창": AsosStation.GOCHANG,
    "순천": AsosStation.SUNCHEON,
    "홍성": AsosStation.HONGSEONG,
    "제주": AsosStation.JEJU,
    "고산": AsosStation.GOSAN,
    "성산": AsosStation.SEONGSAN,
    "서귀포": AsosStation.SEOGWIPO,
    "진주": AsosStation.JINJU,
    "강화": AsosStation.GANGHWA,
    "양평": AsosStation.YANGPYEONG,
    "이천": AsosStation.ICHEON,
    "인제": AsosStation.INJE,
    "홍천": AsosStation.HONGCHEON,
    "태백": AsosStation.TAEBAEK,
    "정선군": AsosStation.JEONGSEON,
    "제천": AsosStation.JECHEON,
    "보은": AsosStation.BOEUN,
    "천안": AsosStation.CHEONAN,
    "보령": AsosStation.BORYEONG,
    "부여": AsosStation.BUYEO,
    "금산": AsosStation.GEUMSAN,
    "세종": AsosStation.SEJONG,
    "부안": AsosStation.BUAN,
    "임실": AsosStation.IMSIL,
    "정읍": AsosStation.JEONGEUP,
    "남원": AsosStation.NAMWON,
    "장수": AsosStation.JANGSU,
    "고창군": AsosStation.GOCHANG_COUNTY,
    "영광군": AsosStation.YEONGGWANG,
    "김해시": AsosStation.GIMHAE,
    "순창군": AsosStation.SUNCHANG,
    "북창원": AsosStation.NORTH_CHANGWON,
    "양산시": AsosStation.YANGSAN,
    "보성군": AsosStation.BOSEONG,
    "강진군": AsosStation.GANGJIN,
    "장흥": AsosStation.JANGHEUNG,
    "해남": AsosStation.HAENAM,
    "고흥": AsosStation.GOHEUNG,
    "의령군": AsosStation.UIRYEONG,
    "함양군": AsosStation.HAMYANG,
    "광양시": AsosStation.GWANGYANG,
    "진도군": AsosStation.JINDO,
    "봉화": AsosStation.BONGHWA,
    "영주": AsosStation.YEONGJU,
    "문경": AsosStation.MUNGYEONG,
    "청송군": AsosStation.CHEONGSONG,
    "영덕": AsosStation.YEONGDEOK,
    "의성": AsosStation.UISEONG,
    "구미": AsosStation.GUMI,
    "영천": AsosStation.YEONGCHEON,
    "경주시": AsosStation.GYEONGJU,
    "거창": AsosStation.GEOCHANG,
    "합천": AsosStation.HAPCHEON,
    "밀양": AsosStation.MIRYANG,
    "산청": AsosStation.SANCHEONG,
    "거제": AsosStation.GEOJE,
    "남해": AsosStation.NAMHAE,
}


def get_station_id(korean_name: str) -> int:
    """한글 지점명을 코드(숫자)로 변환"""
    return KOR_TO_ENUM[korean_name].value