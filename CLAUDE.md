# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

고양시 테니스장(대화문화체육센터) 자동 예약 프로그램. 매월 25일 10시에 오픈되는 예약을 자동으로 처리.

실행 모드:
- **HTTP 모드** (기본): `aiohttp` + `BeautifulSoup`으로 브라우저 없이 직접 HTTP 요청 (asyncio 기반)
- **브라우저 모드**: `selenium`으로 Chrome 브라우저 자동화 (`--browser` 플래그)
- **다중 계정 모드**: `launch.py`로 N개 계정을 tmux/iTerm2 분할 창에서 동시 실행
- **예약 현황 뷰어**: `viewer.py`로 달력 UI에서 예약 확인·편집·저장

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

# 특정 계정 번호로 실행 (다중 계정 모드, launch.py에서 자동 호출)
python3 main.py --account 1

# 주말 예약 가능 시간 검색
python3 main.py --search 3
python3 main.py --search 2026-03

# 전체 날짜 예약 가능 시간 검색
python3 main.py --search2 3

# 다중 계정 tmux 런처 (4개씩 그룹, 각 그룹에 새 터미널 창)
python3 launch.py                  # tmux 세션 + 새 터미널 창 (기본)
python3 launch.py --no-tmux        # iTerm2 native split / Linux 개별 창
python3 launch.py --background     # 백그라운드 subprocess + 로그 파일
python3 launch.py --group-size 2   # 터미널 창당 계정 수 조정
python3 launch.py --test           # 테스트 모드
python3 launch.py --dry-run        # 실행 내용 미리 확인

# 예약 현황 달력 뷰어 (브라우저 UI, 실시간 .env 저장)
python3 viewer.py
python3 viewer.py 2026 7           # 특정 월 지정

# API 서버 실행 (n8n 연동용)
python3 api_server.py
python3 api_server.py --port 8080 --host 0.0.0.0

# Docker 배포
docker-compose up -d
```

## 아키텍처

```
main.py              # 진입점. argparse로 모드 분기, 자격증명 수집
                     # --account N 플래그로 다중 계정 개별 실행 지원
config.py            # 설정 전체 관리. .env 로드, RESERVATION_CONFIG 정의 및 환경변수 오버라이드
                     # load_accounts(): TENNIS_ACCOUNT_N_* 환경변수에서 다중 계정 파싱
reservation_async.py # 핵심 HTTP 예약 로직 (asyncio + aiohttp)
utils.py             # 예약 타이밍 대기 함수 (동기 + 비동기 버전)
reservation_http.py  # 구 HTTP 예약 로직 (requests) — fallback 보존
reservation.py       # Selenium 브라우저 모드 (선택 실행)
api_server.py        # Flask API 서버 (n8n / 외부 호출용)
launch.py            # 다중 계정 tmux 런처 (macOS/Linux 크로스 플랫폼)
viewer.py            # 예약 현황 달력 뷰어 (HTTP 서버 내장, 실시간 .env 저장)
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
- `LOGIN_ADVANCE_MINUTES` / `TENNIS_LOGIN_ADVANCE_MINUTES`: 예약 오픈 N분 전에 로그인 시작 (기본 10분)

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

## 다중 계정 설정 (`launch.py`)

### `.env` 다중 계정 형식

```
# 계정 N: TENNIS_ACCOUNT_N_ID / PW / RESERVATION_M
TENNIS_ACCOUNT_1_ID=user1
TENNIS_ACCOUNT_1_PW=pass1
TENNIS_ACCOUNT_1_RESERVATION_1=2026-06-07:10:1   # 날짜:시간:코트
TENNIS_ACCOUNT_1_RESERVATION_2=2026-06-14:08:2

TENNIS_ACCOUNT_2_ID=user2
TENNIS_ACCOUNT_2_PW=pass2
TENNIS_ACCOUNT_2_RESERVATION_1=2026-06-07:08:3
```

예약 조건은 단일 계정과 동일하게 방법 1/2/3 모두 지원 (`TENNIS_ACCOUNT_N_DATES` 등).

### `launch.py` 동작 방식

계정을 `--group-size`(기본 4)개씩 그룹화 → 그룹마다 새 터미널 창에서 tmux 세션 생성:

```
python3 launch.py 실행 (13개 계정)
  그룹 1 (계정 1~4)  → iTerm2 새 창 → tmux tennis_1 → 2×2 pane
  그룹 2 (계정 5~8)  → iTerm2 새 창 → tmux tennis_2 → 2×2 pane
  그룹 3 (계정 9~12) → iTerm2 새 창 → tmux tennis_3 → 2×2 pane
  그룹 4 (계정 13)   → iTerm2 새 창 → tmux tennis_4 → 1 pane
```

플랫폼별 동작:

| 플래그 | macOS (iTerm2) | Linux |
|--------|---------------|-------|
| (없음) | tmux + 새 터미널 창 | tmux + 감지된 에뮬레이터 |
| `--no-tmux` | iTerm2 native split pane | 계정당 개별 창 |
| `--background` | subprocess + 로그 파일 | 동일 |

tmux 그룹 스크립트는 `/tmp/tennis_group_N.sh`에 생성되며, tmux 절대 경로
(`TMUX="/opt/homebrew/bin/tmux"`)를 하드코딩해 non-login shell PATH 문제를 회피한다.

## 예약 현황 뷰어 (`viewer.py`)

```bash
python3 viewer.py          # 브라우저에서 http://127.0.0.1:8765/ 열기
python3 viewer.py 2026 7   # 특정 월 지정
# Ctrl+C로 종료
```

### 주요 기능

- **달력 뷰**: 월별 날짜 셀 × 코트(C1~C4) × 시간(06~20) 미니 그리드
- **계정 포커스**: 왼쪽 ID 카드 클릭 → 반전 표시 + 해당 계정 예약 체크 상태로 로드
- **실시간 저장**: 슬롯 클릭 → 즉시 `POST /api/save-slots` → `.env` 업데이트
- **중복 표시**: 같은 슬롯에 여러 계정 예약 시 황색 ⚠ 표시 + 툴팁
- **PW 마스킹**: 👁 버튼으로 토글

### 내장 HTTP 서버

`viewer.py`는 Python 내장 `http.server`로 로컬 HTTP 서버를 실행한다.

- `GET /` → HTML 페이지 서빙 (same-origin, CORS 없음)
- `POST /api/save-slots` → `.env` 예약 라인 교체 (날짜→시간→코트 정렬)
  - 저장 전 `.env.bak` 자동 백업
  - 저장 후 최신 accounts JSON 반환 → 브라우저 `ACCOUNTS` in-place 갱신

포트: 8765~8799 범위에서 사용 가능한 포트 자동 탐색.
