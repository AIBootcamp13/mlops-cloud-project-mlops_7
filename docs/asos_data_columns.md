## 기상 데이터 컬럼 설명

### 기본 관측 정보
- stn_id: 종관기상관측 지점 번호
- stn_nm: 종관기상관측 지점명
- tm: 시간(일시)

### 기온 관련 데이터
- avg_ta: 평균 기온(°C)
- min_ta: 최저 기온(°C)
- min_ta_hrmt: 최저 기온 시각(hhmi)
- max_ta: 최고 기온(°C)
- max_ta_hrmt: 최고 기온 시각(hhmi)
- avg_ts: 평균 지면온도(°C)
- min_tg: 최저 초상온도(°C)

### 지중온도 데이터
- avg_cm5_te: 평균 5cm 지중온도(°C)
- avg_cm10_te: 평균 10cm 지중온도(°C)
- avg_cm20_te: 평균 20cm 지중온도(°C)
- avg_cm30_te: 평균 30cm 지중온도(°C)
- avg_m05_te: 0.5m 지중온도(°C)
- avg_m10_te: 1.0m 지중온도(°C)
- avg_m15_te: 1.5m 지중온도(°C)
- avg_m30_te: 3.0m 지중온도(°C)
- avg_m50_te: 5.0m 지중온도(°C)

### 강수 관련 데이터
- sum_rn_dur: 강수 계속시간(hr)
- mi10_max_rn: 10분 최다강수량(mm)
- mi10_max_rn_hrmt: 10분 최다강수량 시각(hhmi)
- hr1_max_rn: 1시간 최다강수량(mm)
- hr1_max_rn_hrmt: 1시간 최다 강수량 시각(hhmi)
- sum_rn: 일강수량(mm)
- n99_rn: 9-9강수(mm)

### 적설 관련 데이터
- dd_mefs: 일 최심신적설(cm)
- dd_mefs_hrmt: 일 최심신적설 시각(hhmi)
- dd_mes: 일 최심적설(cm)
- dd_mes_hrmt: 일 최심적설 시각(hhmi)
- sum_dpth_fhsc: 합계 3시간 신적설(cm)

### 바람 관련 데이터
- max_ins_ws: 최대 순간풍속(m/s)
- max_ins_ws_wd: 최대 순간 풍속 풍향(16방위)
- max_ins_ws_hrmt: 최대 순간풍속 시각(hhmi)
- max_ws: 최대 풍속(m/s)
- max_ws_wd: 최대 풍속 풍향(16방위)
- max_ws_hrmt: 최대 풍속 시각(hhmi)
- avg_ws: 평균 풍속(m/s)
- hr24_sum_rws: 풍정합(100m)
- max_wd: 최다 풍향(16방위)

### 습도 및 기압 관련 데이터
- avg_td: 평균 이슬점온도(°C)
- min_rhm: 최소 상대습도(%)
- min_rhm_hrmt: 평균 상대습도 시각(hhmi)
- avg_rhm: 평균 상대습도(%)
- avg_pv: 평균 증기압(hPa)
- avg_pa: 평균 현지기압(hPa)
- max_ps: 최고 해면 기압(hPa)
- max_ps_hrmt: 최고 해면기압 시각(hhmi)
- min_ps: 최저 해면기압(hPa)
- min_ps_hrmt: 최저 해면기압 시각(hhmi)
- avg_ps: 평균 해면기압(hPa)

### 일조 및 일사 관련 데이터
- ss_dur: 가조시간(hr)
- sum_ss_hr: 합계 일조 시간(hr)
- hr1_max_icsr_hrmt: 1시간 최다 일사 시각(hhmi)
- hr1_max_icsr: 1시간 최다 일사량(MJ/m2)
- sum_gsr: 합계 일사량(MJ/m2)

### 구름 및 기타 기상 현상
- avg_tca: 평균 전운량(10분위)
- avg_lmac: 평균 중하층운량(10분위)
- iscs: 일기현상
- sum_fog_dur: 안개 계속 시간(hr)

### 증발 관련 데이터
- sum_lrg_ev: 합계 대형증발량(mm)
- sum_sml_ev: 합계 소형증발량(mm)
