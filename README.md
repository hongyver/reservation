# 고양시 테니스장 자동 예약

고양시 대화문화체육센터 테니스장 예약을 자동화하는 프로그램.
매월 25일 10시 오픈되는 예약을 asyncio 기반 HTTP 요청으로 처리한다.

## 빠른 시작

```bash
pip3 install -r requirements.txt

# 1. .env 설정
cp .env.example .env
# TENNIS_USER_ID, TENNIS_USER_PW 입력

# 2. 로그인 테스트
python3 main.py --check

# 3. 예약 실행
python3 main.py
```

## 주요 기능

| 기능 | 명령 | 설명 |
|------|------|------|
| 단일 계정 예약 | `python3 main.py` | HTTP 모드 (기본) |
| 브라우저 모드 | `python3 main.py --browser` | Selenium Chrome 자동화 |
| 빈자리 검색 | `python3 main.py --search 2026-06` | 주말 예약 가능 시간 조회 |
| 다중 계정 실행 | `python3 launch.py` | tmux/iTerm2 분할 창 동시 실행 |
| 예약 현황 뷰어 | `python3 viewer.py` | 달력 UI에서 시각적 확인·편집 |
| API 서버 | `python3 api_server.py` | n8n 등 외부 연동용 REST API |

## 다중 계정 모드

`.env`에 `TENNIS_ACCOUNT_N_*` 형식으로 계정을 등록하면 `launch.py`가
계정을 4개씩 그룹화해 각 그룹마다 새 터미널 창(tmux)에서 동시 실행한다.

```env
TENNIS_ACCOUNT_1_ID=user1
TENNIS_ACCOUNT_1_PW=pass1
TENNIS_ACCOUNT_1_RESERVATION_1=2026-06-07:10:1   # 날짜:시간:코트

TENNIS_ACCOUNT_2_ID=user2
TENNIS_ACCOUNT_2_PW=pass2
TENNIS_ACCOUNT_2_RESERVATION_1=2026-06-14:08:2
```

```bash
python3 launch.py              # tmux 분할 창 실행 (기본)
python3 launch.py --no-tmux    # iTerm2 native split (macOS)
python3 launch.py --test       # 테스트 모드
python3 launch.py --dry-run    # 실행 내용 미리 확인
```

## 예약 현황 뷰어

```bash
python3 viewer.py   # http://127.0.0.1:8765/ 브라우저에서 열림
```

- 월별 달력: 날짜 × 코트(C1~C4) × 시간(06~20) 미니 그리드
- ID 클릭 → 반전 포커스 → 해당 계정 예약 표시
- 슬롯 클릭 → 즉시 `.env` 저장 (토스트 확인)
- 중복 예약 황색 ⚠ 표시 + 툴팁

## 문서

- [사용 가이드](GUIDE.md) — 인증, 예약 설정, CLI 실행, API 서버
- [Docker 배포](DOCKER.md) — Docker 빌드, 환경변수, 볼륨 마운트
- [CLAUDE.md](CLAUDE.md) — 아키텍처 상세, 다중 계정·뷰어 설계
