# -*- coding: utf-8 -*-
"""
고양시 체육시설 예약 프로그램 설정
사용 전 아래 설정을 수정하세요.
"""

import os
from datetime import datetime as _dt
from pathlib import Path

# ============================================
# 로그인 정보
# ============================================
# 환경변수 또는 .env 파일에서 읽기
# 우선순위: 1) 환경변수 2) .env 파일 3) None (실행 시 입력)

def load_env_file():
    """Load .env file if exists"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # 환경변수에 없을 때만 설정
                    if key not in os.environ:
                        os.environ[key] = value

# .env 파일 로드
load_env_file()

# 환경변수에서 읽기 (없으면 None)
USER_ID = os.environ.get("TENNIS_USER_ID")
USER_PW = os.environ.get("TENNIS_USER_PW")

# ============================================
# 예약 대상 설정
# ============================================
# 사이트 URL
MAIN_URL = "https://daehwa.gys.or.kr:451"
TENNIS_RESERVATION_URL = "https://daehwa.gys.or.kr:451/rent/tennis_rent.php"


# ============================================
# 예약 조건 설정 방법
# ============================================
#
# 방법 1: 기본 방식 (모든 코트에 같은 시간)
# → dates, hours, court_number 사용
#
# 방법 2: 예약 목록 직접 지정 (코트별 다른 시간)
# → reservations 사용
#
# 방법 3: 코트별 시간대 지정
# → dates, court_schedules 사용
#
# ※ 방법 1, 2, 3 중 하나만 사용하세요!
# ============================================

# ============================================
# 방법 1: 기본 방식 (현재 활성화됨)
# ============================================
# RESERVATION_CONFIG = {
#     "dates": [
#         "2026-02-09",  # 토
#         # "2026-02-08",  # 일
#     ],
#     "hours": [8,],
#     "court_number": 3,
# }

# ============================================
# 방법 2: 예약 목록 직접 지정 (코트별 다른 시간)
# ============================================
# 사용하려면 위의 RESERVATION_CONFIG를 주석 처리하고 아래 주석 해제
#
RESERVATION_CONFIG = {
    "reservations": [
        {"date": "2026-04-27", "hour": 10, "court": 1}
    ]
}

# ============================================
# 방법 3: 코트별 시간대 지정
# ============================================
# 사용하려면 위의 RESERVATION_CONFIG를 주석 처리하고 아래 주석 해제
#
# RESERVATION_CONFIG = {
#     "dates": [
#         "2026-02-09",  # 토
#         "2026-02-16",  # 토
#     ],
#     "court_schedules": [
#         {"court": 1, "hours": [8, 10]},      # 1번 코트: 아침
#         {"court": 2, "hours": [6, 8]},       # 2번 코트: 이른 아침
#         {"court": 3, "hours": [10, 12, 14]}, # 3번 코트: 오전~오후
#     ]
# }

# ============================================
# 실행 설정
# ============================================
# 예약 오픈 시간
# RESERVATION_DAY = 0: 즉시 실행
# RESERVATION_DAY = 25: 매월 25일에만 실행 (날짜가 지났거나 다른 날이면 실행 안됨)
# 환경변수(TENNIS_RESERVATION_DAY/HOUR/MINUTE)로 재정의 가능
RESERVATION_DAY    = int(os.environ.get("TENNIS_RESERVATION_DAY",    25))
RESERVATION_HOUR   = int(os.environ.get("TENNIS_RESERVATION_HOUR",   10))
RESERVATION_MINUTE = int(os.environ.get("TENNIS_RESERVATION_MINUTE", 00))


# 동시 접속 개수 (여러 건 예약 시 동시에 실행할 개수)
# 예: 3으로 설정하면 최대 3개씩 동시 예약 시도
MAX_CONCURRENT = 10

# ============================================
# 브라우저 설정
# ============================================
# 브라우저 표시 여부 (False: 백그라운드 실행)
HEADLESS = False  # 예약 확인을 위해 브라우저 표시 권장

# 브라우저 타임아웃 (초)
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 10

# ============================================
# 코트 번호 → 사이트 내부 value 매핑
# ============================================
COURT_VALUE_MAP = {
    1: "2",   # 1코트
    2: "7",   # 2코트
    3: "8",   # 3코트
    4: "9",   # 4코트
}

# ============================================
# HTTP/네트워크 설정
# ============================================
MAX_RETRIES            = 10   # 최대 재시도 횟수
RETRY_DELAY_MIN        = 0.1  # 최소 재시도 대기 (초)
RETRY_DELAY_MAX        = 1.0  # 최대 재시도 대기 (초)
CONNECTION_TIMEOUT     = 5    # 연결 타임아웃 (초)
READ_TIMEOUT           = 30   # 읽기 타임아웃 (초)
SESSION_RETRY_TOTAL    = 3    # urllib3 소켓 레벨 재시도 횟수
SESSION_RETRY_BACKOFF  = 0.5  # urllib3 재시도 백오프 계수
SESSION_POOL_SIZE      = 10   # 연결 풀 크기

# ============================================
# 예약/검색 상수
# ============================================
ALL_COURTS            = [1, 2, 3, 4]
AVAILABLE_HOURS       = [6, 8, 10, 12, 14, 16, 18, 20]
SEARCH_DEFAULT_HOURS  = [6, 8, 10]
LOGIN_ADVANCE_MINUTES = 10  # 예약 오픈 N분 전에 로그인 시작

# ============================================
# API 서버 설정
# ============================================
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", 5000))


# ============================================
# 환경변수로 예약 조건 오버라이드
# ============================================
# .env의 TENNIS_RESERVATION_N 변수가 있으면 RESERVATION_CONFIG를 대체.
# 없으면 위의 하드코딩 RESERVATION_CONFIG를 그대로 사용.

def _build_reservation_config():
    """환경변수에서 예약 조건을 조립한다.

    우선순위: 방법2(RESERVATION_N) > 방법3(COURT_N_HOURS) > 방법1(DATES+HOURS)
    해당하는 환경변수가 없으면 None 반환 → 하드코딩 RESERVATION_CONFIG 유지.
    """

    def _validate_date(s, key):
        try:
            _dt.strptime(s, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"[설정 오류] {key}: 날짜 형식 오류 '{s}'\n"
                f"  → 올바른 형식: YYYY-MM-DD  (예: 2026-06-07)"
            )

    def _validate_hour(h, key):
        if h not in AVAILABLE_HOURS:
            raise ValueError(
                f"[설정 오류] {key}: 잘못된 시간 '{h}'\n"
                f"  → 가능한 시작 시각: {AVAILABLE_HOURS}"
            )

    def _validate_court(c, key):
        if c not in ALL_COURTS:
            raise ValueError(
                f"[설정 오류] {key}: 잘못된 코트번호 '{c}'\n"
                f"  → 가능한 코트: {ALL_COURTS}"
            )

    # ── 방법 2: TENNIS_RESERVATION_N (번호 인덱스, 1건 = 1줄) ──────────────
    # 형식: YYYY-MM-DD:시간:코트번호
    # 예:   TENNIS_RESERVATION_1=2026-06-07:10:1
    #       TENNIS_RESERVATION_2=2026-06-14:08:2
    reservations = []
    for i in range(1, 100):
        key = f"TENNIS_RESERVATION_{i}"
        raw = os.environ.get(key, "").strip()
        if not raw:
            continue  # 번호 공백 허용 — 다음 번호도 계속 확인

        parts = raw.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"[설정 오류] {key}='{raw}'\n"
                f"  → 올바른 형식: 날짜:시간:코트번호  (예: 2026-06-07:10:1)"
            )

        date_str, hour_str, court_str = [p.strip() for p in parts]
        _validate_date(date_str, key)
        hour, court = int(hour_str), int(court_str)
        _validate_hour(hour, key)
        _validate_court(court, key)
        reservations.append({"date": date_str, "hour": hour, "court": court})

    if reservations:
        return {"reservations": reservations}

    # ── 방법 3: TENNIS_DATES + TENNIS_COURT_N_HOURS ──────────────────────────
    # 예: TENNIS_DATES=2026-06-07,2026-06-14
    #     TENNIS_COURT_1_HOURS=8,10
    #     TENNIS_COURT_2_HOURS=6,8
    dates_raw = os.environ.get("TENNIS_DATES", "").strip()
    court_schedules = []
    for n in ALL_COURTS:
        h_raw = os.environ.get(f"TENNIS_COURT_{n}_HOURS", "").strip()
        if not h_raw:
            continue
        key = f"TENNIS_COURT_{n}_HOURS"
        hours = [int(h.strip()) for h in h_raw.split(",") if h.strip()]
        for h in hours:
            _validate_hour(h, key)
        court_schedules.append({"court": n, "hours": hours})

    if dates_raw and court_schedules:
        dates = [d.strip() for d in dates_raw.split(",") if d.strip()]
        for d in dates:
            _validate_date(d, "TENNIS_DATES")
        return {"dates": dates, "court_schedules": court_schedules}

    # ── 방법 1: TENNIS_DATES + TENNIS_HOURS [+ TENNIS_COURT(S)] ─────────────
    # 예: TENNIS_DATES=2026-06-07,2026-06-14
    #     TENNIS_HOURS=8,10
    #     TENNIS_COURT=1          (단일 코트)
    #     TENNIS_COURTS=1,2,3     (복수 코트 — TENNIS_COURT 대신 사용)
    hours_raw = os.environ.get("TENNIS_HOURS", "").strip()
    if dates_raw and hours_raw:
        dates = [d.strip() for d in dates_raw.split(",") if d.strip()]
        hours = [int(h.strip()) for h in hours_raw.split(",") if h.strip()]
        for d in dates:
            _validate_date(d, "TENNIS_DATES")
        for h in hours:
            _validate_hour(h, "TENNIS_HOURS")

        courts_raw = os.environ.get("TENNIS_COURTS", "").strip()
        court_raw  = os.environ.get("TENNIS_COURT",  "").strip()
        if courts_raw:
            courts = [int(c.strip()) for c in courts_raw.split(",") if c.strip()]
            for c in courts:
                _validate_court(c, "TENNIS_COURTS")
            return {"dates": dates, "hours": hours, "courts": courts}
        elif court_raw:
            court = int(court_raw)
            _validate_court(court, "TENNIS_COURT")
            return {"dates": dates, "hours": hours, "court_number": court}
        else:
            return {"dates": dates, "hours": hours, "court_number": 1}

    return None  # 환경변수 없음 → 하드코딩 RESERVATION_CONFIG 유지


_env_config = _build_reservation_config()
if _env_config is not None:
    RESERVATION_CONFIG = _env_config
