# Docker 배포 가이드

Docker로 API 서버를 배포합니다. 컨테이너는 포트 `3100`으로 서비스됩니다.

## 목차

1. [빌드 및 실행](#1-빌드-및-실행)
2. [인증/환경변수 설정](#2-인증환경변수-설정)
3. [config.py 볼륨 마운트](#3-configpy-볼륨-마운트)
4. [API 테스트](#4-api-테스트)
5. [유용한 명령어](#5-유용한-명령어)
6. [n8n 연동](#6-n8n-연동)
7. [트러블슈팅](#7-트러블슈팅)

---

## 1. 빌드 및 실행

### Docker Compose (권장)

```bash
# 백그라운드 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 설정 변경 후 재시작
docker-compose restart

# 중지
docker-compose down

# Dockerfile 변경 시 재빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Docker 직접 실행

```bash
# 이미지 빌드
docker build -t tennis-reservation .

# 실행
docker run -d \
  --name tennis-reservation \
  -p 3100:3100 \
  -e TZ=Asia/Seoul \
  -e TENNIS_USER_ID=your_id \
  -e TENNIS_USER_PW=your_password \
  tennis-reservation
```

---

## 2. 인증/환경변수 설정

### 방법 1: docker-compose.yml 환경변수 (권장)

`docker-compose.yml` 수정:

```yaml
services:
  tennis-reservation:
    environment:
      - TZ=Asia/Seoul
      - TENNIS_USER_ID=your_id
      - TENNIS_USER_PW=your_password
```

변경 후 재시작:
```bash
docker-compose restart
```

### 방법 2: .env 파일

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 내용:
```
TENNIS_USER_ID=your_id
TENNIS_USER_PW=your_password
```

`docker-compose.yml`에서 참조:
```yaml
services:
  tennis-reservation:
    env_file:
      - .env
```

### 환경변수 우선순위

1. `docker-compose.yml`의 `environment` 또는 `-e` 플래그
2. `.env` 파일
3. `config.py` 기본값

---

## 3. 예약 조건 설정

예약 조건은 **환경변수** (권장) 또는 **config.py 볼륨 마운트** 두 가지 방법으로 설정합니다.

### 방법 A: 환경변수로 설정 (권장)

`docker-compose.yml`에 예약 환경변수를 직접 추가합니다. 재배포 없이 값만 바꾸고 재시작하면 됩니다.

```yaml
services:
  tennis-reservation:
    environment:
      - TZ=Asia/Seoul
      - TENNIS_USER_ID=your_id
      - TENNIS_USER_PW=your_password
      # 예약 오픈 시간
      - TENNIS_RESERVATION_DAY=25
      - TENNIS_RESERVATION_HOUR=10
      - TENNIS_RESERVATION_MINUTE=0
      # 예약 조건 (방법 2: 1건 = 1줄, 형식: 날짜:시작시각:코트번호)
      - TENNIS_RESERVATION_1=2026-06-07:10:1
      - TENNIS_RESERVATION_2=2026-06-14:08:2
      - TENNIS_RESERVATION_3=2026-06-21:10:3
```

#### 예약 조건 환경변수 전체 목록

| 환경변수 | 설명 | 예시 |
|----------|------|------|
| `TENNIS_RESERVATION_N` | 방법 2: 1건씩 개별 지정 | `2026-06-07:10:1` |
| `TENNIS_DATES` | 방법 1/3: 날짜 목록 | `2026-06-07,2026-06-14` |
| `TENNIS_HOURS` | 방법 1: 시간 목록 | `8,10` |
| `TENNIS_COURT` | 방법 1: 단일 코트 | `1` |
| `TENNIS_COURTS` | 방법 1: 복수 코트 | `1,2,3` |
| `TENNIS_COURT_N_HOURS` | 방법 3: N번 코트 시간 | `8,10` |

우선순위: 방법2(`RESERVATION_N`) > 방법3(`COURT_N_HOURS`) > 방법1(`DATES+HOURS`) > config.py 하드코딩

자세한 설명 → [사용 가이드](GUIDE.md#2-예약-조건-설정) 참조

### 방법 B: config.py 볼륨 마운트

환경변수로 표현하기 어려운 복잡한 설정이 필요할 때 사용합니다.

#### 준비

```bash
# 설정 디렉토리 생성
mkdir -p /volume1/docker/apiserver/app

# 컨테이너 내부의 config.py를 호스트로 복사 (최초 1회)
docker cp tennis-reservation:/app/config.py /volume1/docker/apiserver/app/config.py
```

#### config.py 수정

```bash
vi /volume1/docker/apiserver/app/config.py
```

수정 예시:

```python
# 예약 설정 (방법 2: 직접 지정)
RESERVATION_CONFIG = {
    "reservations": [
        {"date": "2026-02-09", "hour": 8,  "court": 1},
        {"date": "2026-02-09", "hour": 10, "court": 1},
        {"date": "2026-02-09", "hour": 6,  "court": 2},
    ]
}

# 예약 오픈 시간 (0: 즉시 실행)
RESERVATION_DAY = 0
RESERVATION_HOUR = 10
RESERVATION_MINUTE = 0

# 동시 접속
MAX_CONCURRENT = 3
```

#### docker-compose.yml 볼륨 설정

```yaml
services:
  tennis-reservation:
    volumes:
      - /volume1/docker/apiserver/app/config.py:/app/config.py
```

#### 수정 후 반드시 재시작

```bash
docker-compose restart
# 또는
docker restart tennis-reservation
```

Python 프로세스는 시작할 때만 config.py를 읽습니다. 수정 후 재시작하지 않으면 변경사항이 반영되지 않습니다.

#### 주의사항

- 볼륨 마운트 경로는 **절대 경로**를 사용하세요.
- 파일 권한 확인: `chmod 644 /volume1/docker/apiserver/app/config.py`

---

## 4. API 테스트

컨테이너가 실행 중인지 먼저 확인:

```bash
curl http://localhost:3100/health
```

```bash
# 현재 설정 조회
curl http://localhost:3100/config

# 로그인 테스트
curl -X POST http://localhost:3100/check-login

# 빈자리 확인
curl -X POST http://localhost:3100/check-slots \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-09", "court": 1}'

# 예약 테스트
curl -X POST http://localhost:3100/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "reservations": [
      {"date": "2026-02-09", "hour": 8, "court": 1}
    ],
    "test_mode": true
  }'
```

전체 API 사용법 → [사용 가이드](GUIDE.md#4-api-서버) 참조

---

## 5. 유용한 명령어

```bash
# 실행 중인 컨테이너 확인
docker ps

# 컨테이너 내부 접속
docker exec -it tennis-reservation /bin/bash

# 실시간 로그
docker logs -f tennis-reservation

# 컨테이너 재시작
docker restart tennis-reservation

# 이미지 재빌드
docker build --no-cache -t tennis-reservation .

# 이미지 삭제
docker rmi tennis-reservation
```

---

## 6. n8n 연동

n8n과 같은 Docker 네트워크에서 실행 시:

```bash
docker network create tennis-net
docker run -d --network tennis-net --name tennis-reservation ...
docker run -d --network tennis-net --name n8n ...
```

n8n HTTP Request 노드 설정:
- URL: `http://tennis-reservation:3100/reserve`
- Method: `POST`
- Body:
  ```json
  {
    "reservations": [
      {"date": "2026-02-09", "hour": 8, "court": 1}
    ],
    "test_mode": false
  }
  ```

---

## 7. 트러블슈팅

### 포트가 이미 사용 중

```bash
# 다른 포트로 실행
docker run -d -p 8080:3100 tennis-reservation
```

### 컨테이너가 즉시 종료됨

```bash
docker logs tennis-reservation
# 또는 bash로 직접 진입
docker run -it --entrypoint /bin/bash tennis-reservation
```

### config.py 수정이 반영되지 않음

```bash
docker-compose restart
```

### "No such file or directory" (볼륨 마운트 시)

호스트 경로에 파일이 있는지 확인:

```bash
ls -l /volume1/docker/apiserver/app/config.py
# 없으면
docker cp tennis-reservation:/app/config.py /volume1/docker/apiserver/app/config.py
```

### 이미지 강제 재빌드

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```
