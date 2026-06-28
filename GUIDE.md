# 고양시 테니스장 자동 예약 - 사용 가이드

## 목차

1. [인증 설정](#1-인증-설정)
2. [예약 조건 설정](#2-예약-조건-설정)
3. [CLI 실행](#3-cli-실행)
4. [API 서버](#4-api-서버)
5. [브라우저 모드 문제 해결](#5-브라우저-모드-문제-해결)

---

## 1. 인증 설정

인증 정보는 아래 순서로 확인합니다:

1. API 요청 파라미터 (`user_id`, `user_pw` 필드) — API 서버만 해당
2. 환경변수 (`TENNIS_USER_ID`, `TENNIS_USER_PW`)
3. `.env` 파일
4. 실행 시 직접 입력 — CLI만 해당

> config.py에 ID/PW를 직접 입력하지 마세요. Git에 업로드될 수 있습니다.

### .env 파일 (권장)

```
TENNIS_USER_ID=your_id
TENNIS_USER_PW=your_password
```

### 환경변수

```bash
export TENNIS_USER_ID=your_id
export TENNIS_USER_PW=your_password
```

Docker 사용 시 → [Docker 배포 가이드](DOCKER.md) 참조

---

## 2. 예약 조건 설정

예약 조건은 **`.env` 파일** (권장) 또는 `config.py` 직접 편집으로 설정합니다.

우선순위: `.env` 환경변수 > `config.py` 하드코딩

### `.env` 파일로 설정 (권장)

세 가지 방법 중 하나를 활성화합니다. 나머지는 주석 처리하세요.

#### 방법 2: 예약 목록 직접 지정 ← 가장 유연, 권장

```env
# 형식: TENNIS_RESERVATION_N=날짜:시작시각:코트번호
# 번호(N)는 1부터. 중간 번호를 주석 처리해도 나머지는 유효.
TENNIS_RESERVATION_1=2026-06-07:10:1
TENNIS_RESERVATION_2=2026-06-14:08:2
# TENNIS_RESERVATION_3=2026-06-21:10:3   ← 이번 달 제외 시 주석만 추가
TENNIS_RESERVATION_4=2026-06-28:08:1
```

| 필드 | 형식 | 가능한 값 |
|------|------|----------|
| 날짜 | `YYYY-MM-DD` | — |
| 시작시각 | 숫자 | `6`, `8`, `10`, `12`, `14`, `16`, `18`, `20` |
| 코트번호 | 숫자 | `1`, `2`, `3`, `4` |

#### 방법 1: 날짜 × 시간 × 코트 조합

```env
TENNIS_DATES=2026-06-07,2026-06-14
TENNIS_HOURS=8,10
TENNIS_COURT=1           # 단일 코트
# TENNIS_COURTS=1,2,3   # 복수 코트 (TENNIS_COURT 대신)
```

#### 방법 3: 코트별 시간대 지정

```env
TENNIS_DATES=2026-06-07,2026-06-14
TENNIS_COURT_1_HOURS=8,10
TENNIS_COURT_2_HOURS=6,8
TENNIS_COURT_3_HOURS=10,12,14
```

#### 예약 오픈 시간

```env
TENNIS_RESERVATION_DAY=25    # 매월 25일 (0이면 즉시 실행)
TENNIS_RESERVATION_HOUR=10   # 10시
TENNIS_RESERVATION_MINUTE=0  # 0분
```

### `config.py` 직접 편집 (대안)

`.env`에 예약 변수가 없으면 `config.py`의 `RESERVATION_CONFIG`가 사용됩니다.

#### 방법 1: 기본 방식

```python
RESERVATION_CONFIG = {
    "dates": ["2026-02-09"],
    "hours": [8, 10],
    "court_number": 3,
}
```

여러 코트:

```python
RESERVATION_CONFIG = {
    "dates": ["2026-02-09"],
    "hours": [8, 10],
    "courts": [1, 2, 3],
}
```

#### 방법 2: 직접 지정

```python
RESERVATION_CONFIG = {
    "reservations": [
        {"date": "2026-02-09", "hour": 8,  "court": 1},
        {"date": "2026-02-09", "hour": 10, "court": 1},
        {"date": "2026-02-09", "hour": 6,  "court": 2},
    ]
}
```

#### 방법 3: 코트별 시간대

```python
RESERVATION_CONFIG = {
    "dates": ["2026-02-09", "2026-02-16"],
    "court_schedules": [
        {"court": 1, "hours": [8, 10]},
        {"court": 2, "hours": [6, 8]},
        {"court": 3, "hours": [10, 12, 14]},
    ]
}
```

### 시작 시각 표

| 값 | 예약 시간 |
|----|----------|
| 6  | 06:00~08:00 |
| 8  | 08:00~10:00 |
| 10 | 10:00~12:00 |
| 12 | 12:00~14:00 |
| 14 | 14:00~16:00 |
| 16 | 16:00~18:00 |
| 18 | 18:00~20:00 |
| 20 | 20:00~22:00 |

### 예약 오픈 시간 동작

| 상황 | 동작 |
|------|------|
| `RESERVATION_DAY = 0` | 즉시 실행 |
| 오늘 = 예약일, 오픈 시간 **이전** | 오픈 10분 전까지 대기 → 로그인 → 정각에 제출 |
| 오늘 = 예약일, 오픈 시간 **이후** | 즉시 실행 |
| 오늘 ≠ 예약일 | 에러 종료 |

**10분 전 대기**: 오픈 10분 이상 전에 시작하면 로그인 없이 기다리다가, 10분 전에 로그인을 시작합니다.

### 동시 접속 제한

```python
MAX_CONCURRENT = 10  # 최대 동시 예약 수 (config.py)
```

---

## 3. CLI 실행

```bash
# 의존성 설치
pip3 install -r requirements.txt

# 설정 확인 + 로그인 테스트
python3 main.py --check

# 테스트 모드 (대관신청 직전에 중단)
python3 main.py --test

# 실제 예약 실행
python3 main.py

# 브라우저 모드 (Selenium)
python3 main.py --browser
python3 main.py --browser --test

# 주말 빈자리 검색
python3 main.py --search 3        # 3월
python3 main.py --search 2026-03  # 2026년 3월

# 전체 날짜 빈자리 검색
python3 main.py --search2 3
```

---

## 4. API 서버

n8n, cron 등 외부 시스템에서 HTTP로 예약을 자동화할 때 사용합니다.

```bash
# 기본 포트 5000으로 시작
python3 api_server.py

# 포트/호스트 지정
python3 api_server.py --port 8080 --host 0.0.0.0
```

Docker 배포 → [Docker 배포 가이드](DOCKER.md) 참조

### 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스 체크 |
| GET | `/config` | 현재 설정 조회 |
| POST | `/check-login` | 로그인 테스트 |
| POST | `/check-slots` | 특정 날짜/코트 빈자리 확인 |
| POST | `/reserve` | 예약 실행 (복수) |
| POST | `/reserve-single` | 단건 예약 |
| POST | `/search-weekend` | 주말 빈자리 검색 |
| POST | `/search-all` | 전체 날짜 빈자리 검색 |

### POST /reserve — 복수 예약

모든 요청에 `user_id`/`user_pw`를 생략하면 서버 환경변수를 사용합니다.

**방법 2: 직접 지정 (권장)**

```bash
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "reservations": [
      {"date": "2026-02-09", "hour": 8,  "court": 1},
      {"date": "2026-02-09", "hour": 6,  "court": 2},
      {"date": "2026-02-16", "hour": 10, "court": 3}
    ],
    "test_mode": true
  }'
```

**방법 1: 기본 방식**

```bash
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "dates": ["2026-02-09"],
    "hours": [8, 10],
    "courts": [1, 2, 3],
    "test_mode": true
  }'
```

**방법 3: 코트별 시간대**

```bash
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "dates": ["2026-02-09", "2026-02-16"],
    "court_schedules": [
      {"court": 1, "hours": [8, 10]},
      {"court": 2, "hours": [6, 8]},
      {"court": 3, "hours": [10, 12]}
    ],
    "test_mode": true
  }'
```

### POST /reserve-single — 단건 예약

```bash
curl -X POST http://localhost:5000/reserve-single \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-02-09",
    "hour": 8,
    "court": 1,
    "test_mode": true
  }'
```

### POST /check-slots — 빈자리 확인

```bash
curl -X POST http://localhost:5000/check-slots \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-09", "court": 3}'
```

### POST /search-weekend — 주말 빈자리 검색

```bash
# 기본 (모든 코트, 6/8/10시)
curl -X POST http://localhost:5000/search-weekend \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 2}'

# 코트/시간 지정
curl -X POST http://localhost:5000/search-weekend \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 2, "courts": [1, 2], "hours": [8, 10]}'
```

응답:
```json
{
  "year": 2026,
  "month": 2,
  "total": 15,
  "results": [
    {"date": "2026-02-01", "day": "토", "court": 1, "hour": 6, "time": "06:00~08:00"},
    ...
  ]
}
```

### POST /search-all — 전체 날짜 검색

```bash
curl -X POST http://localhost:5000/search-all \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 2}'
```

응답에는 `is_weekend` (주말 여부)와 `skipped_dates` (휴장 추정일 목록)가 추가됩니다.

### /search-weekend vs /search-all 비교

| 항목 | search-weekend | search-all |
|------|----------------|------------|
| 검색 날짜 | 주말만 (토/일) | 모든 날짜 |
| 검색 시간 | 지정 가능 (기본: 6,8,10시) | 전체 (6~20시) |
| 속도 | 빠름 | 느림 |
| `is_weekend` 필드 | 없음 | 있음 |
| `skipped_dates` 필드 | 없음 | 있음 |

### 응답 형식 (예약)

```json
{
  "success": true,
  "summary": "3/4건 성공",
  "results": [
    {
      "date": "2026-02-09",
      "hour": 8,
      "court": 1,
      "success": true,
      "message": "대관접수 완료"
    },
    {
      "date": "2026-02-09",
      "hour": 10,
      "court": 1,
      "success": false,
      "message": "이미 예약된 시간"
    }
  ]
}
```

### 서버 응답 메시지 목록

| message | 의미 |
|---------|------|
| `대관접수 완료` | 예약 성공 |
| `이미 예약 있음 (1일 1건 제한)` | 해당 날짜에 이미 1건 예약됨 |
| `이미 예약된 시간` | 해당 시간대 이미 마감 |
| `예약 마감` | 해당 날짜 예약 마감 |
| `시간 데이터 오류` | 잘못된 슬롯 값 |
| `알 수 없는 서버 응답` | 로그에서 proc.php 응답 내용 확인 |

### API 예약 오픈 시간 자동화

API 서버는 `wait_for_open=False`로 동작하므로 즉시 실행됩니다. 정확한 시간에 맞추려면 외부 cron으로 호출하세요.

```bash
# 매월 25일 10:00에 호출
0 10 25 * * curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{"reservations":[{"date":"2026-03-01","hour":8,"court":1}],"test_mode":false}'
```

---

## 5. 브라우저 모드 문제 해결

`python3 main.py --browser` 사용 시 ChromeDriver 오류가 발생하는 경우.

### 빠른 해결

```bash
# 1. ChromeDriver 캐시 삭제
rm -rf ~/.wdm

# 2. 패키지 재설치
pip3 install --upgrade selenium webdriver-manager

# 3. 테스트
python3 main.py --check --browser
```

### 자주 발생하는 에러

**"chromedriver not found"**
```bash
brew install chromedriver
xattr -d com.apple.quarantine $(which chromedriver)
```

**"This version of ChromeDriver only supports Chrome version XX"**
```bash
rm -rf ~/.wdm
python3 main.py --check --browser  # 자동으로 맞는 버전 다운로드
```

**"developer cannot be verified" (macOS 보안)**
```bash
CHROMEDRIVER_PATH=$(python3 -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())")
xattr -d com.apple.quarantine "$CHROMEDRIVER_PATH"
```

**Segmentation fault**
```python
# config.py
HEADLESS = False  # True → False로 변경
```

### HTTP 모드 전환 (권장)

브라우저 모드 문제가 지속된다면 HTTP 모드를 사용하세요. 더 빠르고 안정적입니다.

```bash
python3 main.py --test   # HTTP 모드 (브라우저 불필요)
python3 main.py --check  # HTTP 로그인 테스트
```
