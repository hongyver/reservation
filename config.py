# -*- coding: utf-8 -*-
"""
고양시 체육시설 예약 프로그램 설정
사용 전 아래 설정을 수정하세요.
"""

import os
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

# 시설 종류: 테니스장
FACILITY_TYPE = "테니스장"

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
        {"date": "2026-02-09", "hour": 8, "court": 1},
        {"date": "2026-02-09", "hour": 10, "court": 1},
        {"date": "2026-02-09", "hour": 6, "court": 2},
        {"date": "2026-02-16", "hour": 10, "court": 3},
        {"date": "2026-02-18", "hour": 10, "court": 4},
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
RESERVATION_DAY = 25
RESERVATION_HOUR = 10
RESERVATION_MINUTE = 00

# 재시도 횟수
MAX_RETRY = 3

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
