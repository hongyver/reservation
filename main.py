#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고양시 테니스장 자동 예약 프로그램
매월 25일 10시 예약용 (HTTP 기반 - 브라우저 불필요)

사용법:
    python3 main.py --check       # 로그인 테스트
    python3 main.py --test        # 테스트 모드 (대관신청 전 멈춤)
    python3 main.py               # 실제 예약 (대관신청까지 진행)
    python3 main.py --browser     # 브라우저 모드로 실행 (Selenium)
    python3 main.py --search 2    # 2월 주말 예약 가능 시간 검색
    python3 main.py --search 2026-02  # 2026년 2월 검색
"""

import sys
import argparse
from datetime import datetime
import urllib3
import getpass
import os

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import config
from reservation_http import (
    TennisReservationHTTP,
    run_reservation_http,
    search_available_slots,
    search_all_slots,
    MAX_RETRIES,
    REQUEST_TIMEOUT
)


def get_credentials():
    """로그인 정보 가져오기 (환경변수 또는 입력)

    Returns:
        tuple: (user_id, user_pw)
    """
    user_id = config.USER_ID
    user_pw = config.USER_PW

    # ID/PW가 없으면 입력받기
    if not user_id or not user_pw:
        print()
        print("=" * 60)
        print("로그인 정보 입력")
        print("=" * 60)
        print()
        print("[INFO] 환경변수나 .env 파일에 로그인 정보가 없습니다.")
        print("[INFO] 직접 입력하시거나, .env 파일을 생성하세요.")
        print()

        if not user_id:
            user_id = input("아이디: ").strip()

        if not user_pw:
            user_pw = getpass.getpass("비밀번호: ")

        print()

    if not user_id or not user_pw:
        print("[ERROR] 아이디 또는 비밀번호가 입력되지 않았습니다.")
        return None, None

    return user_id, user_pw


def print_config():
    """설정 출력"""
    print("=" * 60)
    print("고양시 테니스장 자동 예약 프로그램 (HTTP)")
    print("=" * 60)
    print()

    cfg = config.RESERVATION_CONFIG

    # 로그인 정보 마스킹
    user_id = config.USER_ID
    if user_id and len(user_id) > 2:
        masked_id = user_id[0] + "*" * (len(user_id) - 2) + user_id[-1]
    elif user_id:
        masked_id = user_id[0] + "*"
    else:
        masked_id = "(입력 필요)"

    print("[설정 확인]")
    print(f"  사이트: {config.MAIN_URL}")
    print(f"  로그인 ID: {masked_id}")
    print()

    # 방법 2: reservations 직접 지정
    if "reservations" in cfg:
        print("  예약 방식: 직접 지정 (코트별 다른 시간)")
        print(f"  총 {len(cfg['reservations'])}건:")
        for i, res in enumerate(cfg["reservations"], 1):
            print(f"    [{i}] {res['date']} {res['hour']:02d}:00~{res['hour']+2:02d}:00 / {res['court']}번 코트")
        task_count = len(cfg["reservations"])

    # 방법 3: court_schedules로 코트별 시간 지정
    elif "court_schedules" in cfg:
        print("  예약 방식: 코트별 시간대 지정")
        print(f"  예약 날짜:")
        for date in cfg["dates"]:
            print(f"    - {date}")
        print()
        print("  코트별 시간:")
        task_count = 0
        for schedule in cfg["court_schedules"]:
            court = schedule["court"]
            hours = schedule["hours"]
            hours_str = [f"{h:02d}:00~{h+2:02d}:00" for h in hours]
            print(f"    {court}번 코트: {', '.join(hours_str)}")
            task_count += len(cfg["dates"]) * len(hours)

    # 방법 1: 기본 방식 (모든 코트에 같은 시간)
    else:
        print("  예약 방식: 기본 (모든 코트에 같은 시간)")
        print(f"  예약 날짜:")
        for date in cfg["dates"]:
            print(f"    - {date}")
        print()
        hours_str = [f"{h:02d}:00~{h+2:02d}:00" for h in cfg["hours"]]
        print(f"  예약 시간: {', '.join(hours_str)}")

        # court_number 또는 courts 처리
        if "courts" in cfg:
            print(f"  코트: {cfg['courts']}")
            task_count = len(cfg["dates"]) * len(cfg["hours"]) * len(cfg["courts"])
        else:
            print(f"  코트: {cfg['court_number']}번 코트")
            task_count = len(cfg["dates"]) * len(cfg["hours"])

    print()
    if task_count > 1:
        print(f"  → 총 {task_count}개 병렬 실행 (동시 접속 제한: {config.MAX_CONCURRENT}개)")
    print()

    if config.RESERVATION_DAY == 0:
        print("  예약 오픈: 즉시 실행")
    else:
        print(f"  예약 오픈: 매월 {config.RESERVATION_DAY}일 {config.RESERVATION_HOUR}시 {config.RESERVATION_MINUTE}분")
        print("  → 로그인 후 해당 시간까지 대기")
    print()

    print("[접속 폭주 대응 설정]")
    print(f"  최대 재시도: {MAX_RETRIES}회")
    print(f"  타임아웃: 연결 {REQUEST_TIMEOUT[0]}초, 읽기 {REQUEST_TIMEOUT[1]}초")
    print()

    return True


def test_login(user_id, user_pw):
    """로그인 테스트 (HTTP)"""
    print("[TEST] 로그인 테스트 (HTTP)")
    print()

    bot = TennisReservationHTTP()

    if not bot.login(user_id, user_pw):
        print("[FAIL] 로그인 실패")
        return False

    print()

    # 예약 페이지 접근 테스트
    cfg = config.RESERVATION_CONFIG
    court = cfg["court_number"]
    date = cfg["dates"][0] if cfg["dates"] else "2026-02-01"

    dt = datetime.strptime(date, "%Y-%m-%d")
    html = bot.get_reservation_page(court, dt.year, dt.month, dt.day)

    if not html:
        print("[FAIL] 예약 페이지 접근 실패")
        return False

    slots = bot.get_available_slots(html)
    print(f"[INFO] 예약 가능 시간대: {[s['start'] for s in slots]}")
    print()

    print("[SUCCESS] 모든 테스트 통과!")
    bot.close()
    return True


def test_login_browser(user_id, user_pw):
    """로그인 테스트 (브라우저)"""
    try:
        from reservation import TennisReservationBot
    except ImportError:
        print("[ERROR] Selenium 모듈이 없습니다.")
        print("[INFO] pip3 install selenium webdriver-manager")
        return False

    print("[TEST] 로그인 및 페이지 접근 테스트 (브라우저)")
    print()

    bot = TennisReservationBot()
    try:
        bot.setup_browser()

        if not bot.login(user_id, user_pw):
            print("[FAIL] 로그인 실패")
            return False

        print()
        if not bot.go_to_reservation_page():
            print("[FAIL] 예약 페이지 접근 실패")
            return False

        court = config.RESERVATION_CONFIG["court_number"]
        if not bot.select_court(court):
            print(f"[FAIL] {court}번 코트 선택 실패")
            return False

        print()
        print("[SUCCESS] 모든 테스트 통과!")
        print("[INFO] 브라우저를 확인하세요. (30초 후 종료)")

        import time
        time.sleep(30)

        return True

    finally:
        bot.close()


def check_reservation_day():
    """예약 가능한 날인지 확인

    RESERVATION_DAY가 0이면 바로 실행
    0이 아니면 해당 날짜에만 실행
    """
    # RESERVATION_DAY가 0이면 바로 실행
    if config.RESERVATION_DAY == 0:
        return True

    today = datetime.now()

    if today.day != config.RESERVATION_DAY:
        print(f"[INFO] 오늘은 {today.month}월 {today.day}일입니다.")
        print(f"[INFO] 예약 오픈은 매월 {config.RESERVATION_DAY}일입니다.")
        print("[INFO] 예약일이 아니므로 프로그램을 종료합니다.")
        return False

    return True


def run_browser_mode(test_mode=False, user_id=None, user_pw=None):
    """브라우저 모드 실행"""
    try:
        from reservation import run_reservation
    except ImportError:
        print("[ERROR] Selenium 모듈이 없습니다.")
        print("[INFO] pip3 install selenium webdriver-manager")
        return False

    return run_reservation(test_mode=test_mode, user_id=user_id, user_pw=user_pw)


def parse_search_month(search_arg):
    """검색 월 파싱

    Args:
        search_arg: "2" (현재 연도 2월) 또는 "2026-02" (2026년 2월)

    Returns:
        tuple: (year, month)
    """
    now = datetime.now()

    if "-" in search_arg:
        # 2026-02 형식
        parts = search_arg.split("-")
        year = int(parts[0])
        month = int(parts[1])
    else:
        # 2 형식 (현재 연도)
        month = int(search_arg)
        year = now.year

        # 이미 지난 달이면 다음 연도로
        if month < now.month:
            year += 1

    return year, month


def main():
    parser = argparse.ArgumentParser(description="고양시 테니스장 자동 예약")
    parser.add_argument("--test", action="store_true",
                        help="테스트 모드 (대관신청 전 멈춤)")
    parser.add_argument("--check", action="store_true",
                        help="로그인 테스트")
    parser.add_argument("--browser", action="store_true",
                        help="브라우저 모드로 실행 (Selenium)")
    parser.add_argument("--search", metavar="MONTH",
                        help="주말 예약 가능 시간 검색 (예: 2 또는 2026-02)")
    parser.add_argument("--search2", metavar="MONTH",
                        help="전체 날짜/시간 예약 가능 시간 검색 (예: 2 또는 2026-02)")
    args = parser.parse_args()

    # 검색 모드는 설정 출력 생략하지만 로그인 정보는 필요
    if args.search or args.search2:
        # 로그인 정보 가져오기
        user_id, user_pw = get_credentials()
        if not user_id or not user_pw:
            sys.exit(1)

    # 주말 검색 모드
    if args.search:
        try:
            year, month = parse_search_month(args.search)
            result = search_available_slots(year, month, user_id=user_id, user_pw=user_pw)
            sys.exit(0 if result.get("total", 0) > 0 else 1)
        except ValueError as e:
            print(f"[ERROR] 잘못된 월 형식: {args.search}")
            print("[INFO] 사용법: --search 2 또는 --search 2026-02")
            sys.exit(1)

    # 전체 검색 모드
    if args.search2:
        try:
            year, month = parse_search_month(args.search2)
            result = search_all_slots(year, month, user_id=user_id, user_pw=user_pw)
            sys.exit(0 if result.get("total", 0) > 0 else 1)
        except ValueError as e:
            print(f"[ERROR] 잘못된 월 형식: {args.search2}")
            print("[INFO] 사용법: --search2 2 또는 --search2 2026-02")
            sys.exit(1)

    if not print_config():
        sys.exit(1)

    # 로그인 정보 가져오기
    user_id, user_pw = get_credentials()
    if not user_id or not user_pw:
        sys.exit(1)

    # 환경변수에 설정 (하위 함수들이 사용)
    os.environ["TENNIS_USER_ID"] = user_id
    os.environ["TENNIS_USER_PW"] = user_pw
    config.USER_ID = user_id
    config.USER_PW = user_pw

    # 로그인 테스트
    if args.check:
        if args.browser:
            success = test_login_browser(user_id, user_pw)
        else:
            success = test_login(user_id, user_pw)
        sys.exit(0 if success else 1)

    # 테스트 모드
    if args.test:
        print("[TEST MODE] 테스트 모드로 실행합니다.")
        print("[TEST MODE] 최종 대관신청 버튼 클릭 전에 멈춥니다.")
        print()

        if args.browser:
            success = run_browser_mode(test_mode=True, user_id=user_id, user_pw=user_pw)
        else:
            result = run_reservation_http(test_mode=True, user_id=user_id, user_pw=user_pw)
            success = result.get("success", False)

        sys.exit(0 if success else 1)

    # 일반 실행
    if not check_reservation_day():
        sys.exit(0)

    print("[INFO] 예약 프로그램을 시작합니다.")
    print("[INFO] 최종 대관신청까지 자동 진행됩니다.")
    print("[INFO] Ctrl+C를 눌러 중단할 수 있습니다.")
    print()

    if args.browser:
        success = run_browser_mode(test_mode=False, user_id=user_id, user_pw=user_pw)
    else:
        result = run_reservation_http(test_mode=False, user_id=user_id, user_pw=user_pw)
        success = result.get("success", False)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
