# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

고양시 테니스장(대화문화체육센터) 자동 예약 프로그램. 매월 25일 10시에 오픈되는 예약을 자동으로 처리.

실행 모드는 두 가지:
- **HTTP 모드** (기본): `aiohttp` + `BeautifulSoup`으로 브라우저 없이 직접 HTTP 요청 (asyncio 기반)
- **브라우저 모드**: `selenium`으로 Chrome 브라우저 자동화 (`--browser` 플래그)

## 실행 명령어

```bash
# 의존성 설치
pip3 install -r requirements.txt

# 로그인 테스트
python3 main.py --check

# 테스트 모드 (대관신청 직전에 중단)
python3 main.py --test

# 실제 예약 실행
python3 main.py

# 브라우저 모드로 실행
python3 main.py --browser

# 주말 예약 가능 시간 검색
python3 main.py --search 3
python3 main.py --search 2026-03

# 전체 날짜 예약 가능 시간 검색
python3 main.py --search2 3

# API 서버 실행 (n8n 연동용)
python3 api_server.py
python3 api_server.py --port 8080 --host 0.0.0.0

# Docker 배포
docker-compose up -d
```

## 아키텍처

```
main.py              # 진입점. argparse로 모드 분기, 자격증명 수집
config.py            # 설정 전체 관리. .env 로드, RESERVATION_CONFIG 정의 및 환경변수 오버라이드
reservation_async.py # 핵심 HTTP 예약 로직 (asyncio + aiohttp)
utils.py             # 예약 타이밍 대기 함수 (동기 + 비동기 버전)
reservation_http.py  # 구 HTTP 예약 로직 (requests) — fallback 보존
reservation.py       # Selenium 브라우저 모드 (선택 실행)
api_server.py        # Flask API 서버 (n8n / 외부 호출용)
```

### 예약 실행 흐름 (`reservation_async.py`)

1. `_build_tasks()` → `.env` 또는 `config.RESERVATION_CONFIG`에서 예약 작업 목록 조립
2. **Phase 1** — 로그인 전 대기 (`wait_before_login_async`): 오픈 10분 전까지 asyncio.sleep
3. **Phase 2** — N개 봇 병렬 로그인 (`asyncio.gather`): 각 예약 건마다 독립 세션(PHPSESSID) 생성
4. **Phase 3** — 오픈 시간 정밀 대기 (`wait_for_reservation_open_async`): 마지막 10초는 10ms 단위
5. **Phase 4** — `asyncio.gather` + `Semaphore(MAX_CONCURRENT)`로 동시 예약 실행

각 예약 봇의 내부 흐름:
1. `get_reservation_page()` → 대상 코트/날짜 페이지 HTML 조회
2. `get_available_slots()` → BeautifulSoup으로 가능 슬롯 파싱
3. `submit_reservation()` → 3단계 제출:
   - POST `rent_period_apply.php` → `DocumentForm` + `useForm` 필드 수집
   - POST `rent_period_proc.php` → 최종 대관신청

### 왜 예약 1건 = 독립 세션인가

같은 PHPSESSID로 `apply.php`를 병렬 호출하면 PHP 세션 상태가 덮어쓰여져
`proc.php`에서 `"정상적인 방법으로 신청해주세요. (1-1)"` 오류가 발생한다.
각 예약 봇이 독립 로그인으로 별도 PHPSESSID를 확보하므로 세션 충돌이 없다.
로그인은 `asyncio.gather`로 병렬화하여 O(1) 시간에 완료된다.

### 코트 번호 매핑

`config.py`의 `COURT_VALUE_MAP`에서 코트 번호(1~4)를 사이트 내부 value로 변환:

```python
COURT_VALUE_MAP = {1: "2", 2: "7", 3: "8", 4: "9"}
```

### 실제 서버 응답 (proc.php)

| 상황 | 응답 내용 | 판정 |
|------|----------|------|
| 성공 | `alert("대관접수가 정상적으로 완료되었습니다..")` | True |
| 중복 예약 | `alert("예약이 완료된 시간입니다.(3)")` | False |
| 1일 1건 초과 | `alert("한 건 이상 예약이 완료되어 있습니다.")` | False |
| 세션 불일치 | `alert("정상적인 방법으로 신청해주세요. (1-1)")` | False |

판단 로직은 **실패 조건을 먼저** 검사한다. `"완료"`는 실패 메시지에도 등장하므로
광역 매칭 없이 `"정상적으로 완료"`만 성공으로 인정한다.

### 인코딩 처리

서버가 `Content-Type: charset=EUC-KR`을 선언하지만 일부 응답(apply.php)은
실제로 UTF-8 바이트를 포함한다. `_request_with_retry`에서 바이트를 직접 읽어
`euc-kr → cp949 → utf-8 → replace` 순으로 폴백 디코딩한다.

## 설정 (`config.py` + `.env`)

### 인증 정보

`.env` 파일 또는 환경변수로 제공:

```
TENNIS_USER_ID=아이디
TENNIS_USER_PW=비밀번호
```

### 예약 조건 설정 — `.env` 방식 (권장)

우선순위: 방법2(RESERVATION_N) > 방법3(COURT_N_HOURS) > 방법1(DATES+HOURS) > config.py 하드코딩

| 방법 | 환경변수 | 예시 |
|------|----------|------|
| 방법 2 | `TENNIS_RESERVATION_N=날짜:시간:코트` | `TENNIS_RESERVATION_1=2026-06-07:10:1` |
| 방법 1 | `TENNIS_DATES`, `TENNIS_HOURS`, `TENNIS_COURT(S)` | `TENNIS_DATES=2026-06-07` |
| 방법 3 | `TENNIS_DATES`, `TENNIS_COURT_N_HOURS` | `TENNIS_COURT_1_HOURS=8,10` |

### RESERVATION_CONFIG 방법 세 가지 (config.py 직접 편집)

| 방법 | 키 | 용도 |
|------|-----|------|
| 방법 1 | `dates`, `hours`, `court_number` | 모든 코트에 동일 시간 |
| 방법 2 | `reservations` | 코트별 날짜/시간 개별 지정 |
| 방법 3 | `dates`, `court_schedules` | 코트별 시간대 묶음 지정 |

`RESERVATION_DAY = 0`으로 설정하면 날짜 무관 즉시 실행.

### 주요 실행 설정

- `RESERVATION_DAY` / `TENNIS_RESERVATION_DAY`: 매월 오픈 일 (0 = 즉시 실행)
- `MAX_CONCURRENT`: 병렬 예약 동시 세션 수
- `MAX_RETRIES`: 접속 폭주 시 재시도 횟수 (기본 10)
- `LOGIN_ADVANCE_MINUTES`: 예약 오픈 N분 전에 로그인 시작 (기본 10분)

## API 서버 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스 체크 |
| GET | `/config` | 현재 설정 조회 |
| POST | `/check-login` | 로그인 테스트 |
| POST | `/check-slots` | 특정 날짜/코트 빈자리 확인 |
| POST | `/reserve` | 예약 실행 (복수, 방법 1/2/3) |
| POST | `/reserve-single` | 단건 예약 |
| POST | `/search-weekend` | 주말 빈자리 검색 |
| POST | `/search-all` | 전체 날짜 빈자리 검색 |

Docker 배포 시 포트 `3100`으로 노출. `.env` 환경변수 또는 `docker-compose.yml` volume 마운트로 `config.py`를 교체 가능.
