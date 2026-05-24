#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
공통 유틸리티: 예약 타이밍 대기 함수 (동기 + 비동기)
"""

import asyncio
import time
import config
from datetime import datetime, timedelta


def wait_before_login():
    """예약 오픈 10분 전까지 로그인 없이 대기.

    - RESERVATION_DAY == 0: 즉시 통과
    - 오늘이 예약일이 아닌 경우: 즉시 통과 (기존 검증 함수가 처리)
    - 남은 시간 > 10분: 10분 전 시각까지 슬립 대기
    - 남은 시간 <= 10분: 즉시 통과
    """
    if config.RESERVATION_DAY == 0:
        return

    now = datetime.now()
    if now.day != config.RESERVATION_DAY:
        return

    target = now.replace(
        hour=config.RESERVATION_HOUR,
        minute=config.RESERVATION_MINUTE,
        second=0,
        microsecond=0
    )
    login_time = target - timedelta(minutes=config.LOGIN_ADVANCE_MINUTES)
    remaining = (login_time - now).total_seconds()

    if remaining <= 0:
        return

    print(f"[PRE-WAIT] 예약 오픈({target.strftime('%H:%M')})까지 {(target - now).total_seconds():.0f}초 남았습니다.")
    print(f"[PRE-WAIT] 로그인은 {config.LOGIN_ADVANCE_MINUTES}분 전({login_time.strftime('%H:%M:%S')})부터 시작합니다.")

    while True:
        now = datetime.now()
        remaining = (login_time - now).total_seconds()
        if remaining <= 0:
            break
        if remaining > 60:
            print(f"\r[PRE-WAIT] 로그인까지 {remaining:.0f}초 남음 (슬립 중)", end="", flush=True)
            time.sleep(30)
        else:
            print(f"\r[PRE-WAIT] 로그인까지 {remaining:.0f}초 남음", end="", flush=True)
            time.sleep(1)

    print()
    print("[INFO] 10분 전 도달. 로그인을 시작합니다.")


def wait_for_reservation_open():
    """예약 오픈 시간까지 대기.

    RESERVATION_DAY = 0이면 바로 실행
    RESERVATION_DAY != 0이면:
      - 오늘이 예약일과 같으면: 예약 시간까지 대기
      - 오늘이 예약일보다 크면: 에러 (이미 지남)
      - 오늘이 예약일보다 작으면: 에러 (아직 예약일이 아님)

    Returns:
        bool: 성공 시 True, 실행 불가 시 False
    """
    if config.RESERVATION_DAY == 0:
        print("[INFO] 즉시 실행 모드")
        return True

    now = datetime.now()

    if now.day != config.RESERVATION_DAY:
        if now.day > config.RESERVATION_DAY:
            print(f"[ERROR] 이번 달 예약일({config.RESERVATION_DAY}일)이 이미 지났습니다.")
            print(f"[ERROR] 오늘은 {now.month}월 {now.day}일입니다.")
            return False
        else:
            print(f"[ERROR] 아직 예약일이 아닙니다.")
            print(f"[ERROR] 오늘은 {now.month}월 {now.day}일이고, 예약일은 매월 {config.RESERVATION_DAY}일입니다.")
            return False

    target = now.replace(
        hour=config.RESERVATION_HOUR,
        minute=config.RESERVATION_MINUTE,
        second=0,
        microsecond=0
    )

    if now >= target:
        print(f"[INFO] 예약 시간({config.RESERVATION_HOUR}:{config.RESERVATION_MINUTE:02d})이 지났습니다. 바로 진행합니다.")
        return True

    wait_seconds = (target - now).total_seconds()
    print(f"[INFO] 예약 오픈까지 {wait_seconds:.0f}초 남았습니다.")
    print(f"[INFO] 목표 시간: {target.strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        now = datetime.now()
        remaining = (target - now).total_seconds()

        if remaining <= 0:
            break

        if remaining > 10:
            print(f"\r[WAIT] 남은 시간: {remaining:.0f}초", end="", flush=True)
            time.sleep(1)
        else:
            print(f"\r[READY] {remaining:.1f}초 후 시작!", end="", flush=True)
            time.sleep(0.05)

    print("[GO!] 예약을 시작합니다!")
    return True


# ============================================================
# 비동기 버전 (asyncio + aiohttp 모드용)
# ============================================================

async def wait_before_login_async():
    """예약 오픈 전 10분까지 비동기 대기 (이벤트 루프 블로킹 없음).

    - RESERVATION_DAY == 0: 즉시 통과
    - 오늘이 예약일이 아닌 경우: 즉시 통과
    - 남은 시간 > 10분: 30초 단위 asyncio.sleep
    - 남은 시간 <= 10분: 1초 단위 asyncio.sleep
    """
    if config.RESERVATION_DAY == 0:
        return

    now = datetime.now()
    if now.day != config.RESERVATION_DAY:
        return

    target = now.replace(
        hour=config.RESERVATION_HOUR,
        minute=config.RESERVATION_MINUTE,
        second=0,
        microsecond=0
    )
    login_time = target - timedelta(minutes=config.LOGIN_ADVANCE_MINUTES)
    remaining = (login_time - now).total_seconds()

    if remaining <= 0:
        return

    print(f"[PRE-WAIT] 예약 오픈({target.strftime('%H:%M')})까지 {(target - now).total_seconds():.0f}초 남았습니다.")
    print(f"[PRE-WAIT] 로그인은 {config.LOGIN_ADVANCE_MINUTES}분 전({login_time.strftime('%H:%M:%S')})부터 시작합니다.")

    while True:
        now = datetime.now()
        remaining = (login_time - now).total_seconds()
        if remaining <= 0:
            break
        if remaining > 60:
            print(f"\r[PRE-WAIT] 로그인까지 {remaining:.0f}초 남음 (대기 중)", end="", flush=True)
            await asyncio.sleep(min(remaining - 60, 30))
        else:
            print(f"\r[PRE-WAIT] 로그인까지 {remaining:.0f}초 남음", end="", flush=True)
            await asyncio.sleep(1)

    print()
    print("[INFO] 10분 전 도달. 로그인을 시작합니다.")


async def wait_for_reservation_open_async():
    """예약 오픈 시간까지 비동기 정밀 대기.

    RESERVATION_DAY = 0이면 바로 실행
    RESERVATION_DAY != 0이면:
      - 오늘이 예약일과 같으면: 예약 시간까지 대기 (10ms 정밀도)
      - 그 외: False 반환

    Returns:
        bool: 성공 시 True, 실행 불가 시 False
    """
    if config.RESERVATION_DAY == 0:
        print("[INFO] 즉시 실행 모드")
        return True

    now = datetime.now()

    if now.day != config.RESERVATION_DAY:
        if now.day > config.RESERVATION_DAY:
            print(f"[ERROR] 이번 달 예약일({config.RESERVATION_DAY}일)이 이미 지났습니다.")
            print(f"[ERROR] 오늘은 {now.month}월 {now.day}일입니다.")
        else:
            print(f"[ERROR] 아직 예약일이 아닙니다.")
            print(f"[ERROR] 오늘은 {now.month}월 {now.day}일이고, 예약일은 매월 {config.RESERVATION_DAY}일입니다.")
        return False

    target = now.replace(
        hour=config.RESERVATION_HOUR,
        minute=config.RESERVATION_MINUTE,
        second=0,
        microsecond=0
    )

    if now >= target:
        print(f"[INFO] 예약 시간({config.RESERVATION_HOUR}:{config.RESERVATION_MINUTE:02d})이 지났습니다. 바로 진행합니다.")
        return True

    wait_seconds = (target - now).total_seconds()
    print(f"[INFO] 예약 오픈까지 {wait_seconds:.0f}초 남았습니다.")
    print(f"[INFO] 목표 시간: {target.strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        now = datetime.now()
        remaining = (target - now).total_seconds()

        if remaining <= 0:
            break

        if remaining > 10:
            print(f"\r[WAIT] 남은 시간: {remaining:.0f}초", end="", flush=True)
            await asyncio.sleep(1)
        else:
            # 마지막 10초: 10ms 정밀도로 대기
            print(f"\r[READY] {remaining:.3f}초 후 시작!", end="", flush=True)
            await asyncio.sleep(0.01)

    print("\n[GO!] 예약을 시작합니다!")
    return True
