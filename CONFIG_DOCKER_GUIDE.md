# Docker에서 config.py 수정하는 방법

Docker 컨테이너에서 config.py 파일의 설정을 변경하는 방법입니다.

---

## 📋 전체 흐름

1. 호스트의 config.py 파일 준비
2. Docker 볼륨 마운트로 컨테이너에 연결
3. config.py 수정
4. 컨테이너 재시작

---

## 🚀 방법 1: 볼륨 마운트 사용 (권장)

### 1단계: 호스트에 config.py 디렉토리 생성

```bash
# NAS 또는 서버에서
mkdir -p /volume1/docker/apiserver/app

# 현재 config.py를 복사
cp /path/to/reservation/config.py /volume1/docker/apiserver/app/config.py
```

### 2단계: config.py 수정

```bash
vi /volume1/docker/apiserver/app/config.py
```

수정할 부분:

```python
# 로그인 정보
USER_ID = "your_id"      # 여기에 실제 아이디 입력
USER_PW = "your_password" # 여기에 실제 비밀번호 입력

# 예약 오픈 시간
RESERVATION_DAY = 0      # 0: 즉시 실행, 25: 매월 25일
RESERVATION_HOUR = 10
RESERVATION_MINUTE = 30

# 예약 설정
RESERVATION_CONFIG = {
    "reservations": [
        {"date": "2026-02-09", "hour": 8, "court": 1},
        {"date": "2026-02-09", "hour": 10, "court": 1},
    ]
}
```

### 3단계: docker-compose.yml 확인

`docker-compose.yml` 파일에서 volumes가 설정되어 있는지 확인:

```yaml
services:
  tennis-reservation:
    volumes:
      - /volume1/docker/apiserver/app/config.py:/app/config.py
```

### 4단계: 컨테이너 재시작

```bash
# config.py 수정 후 반드시 재시작
docker-compose restart

# 또는
docker-compose down
docker-compose up -d
```

### 5단계: 로그 확인

```bash
docker-compose logs -f
```

---

## 🔧 방법 2: Docker run으로 직접 실행

### config.py 준비

```bash
# config.py가 있는 디렉토리로 이동
cd /volume1/docker/apiserver/app

# config.py 수정
vi config.py
```

### Docker 실행

```bash
docker run -d \
  --name tennis-reservation \
  -p 3100:3100 \
  -v /volume1/docker/apiserver/app/config.py:/app/config.py \
  -e TZ=Asia/Seoul \
  tennis-reservation

# config.py 수정 후 재시작
docker restart tennis-reservation
```

---

## 📝 config.py 주요 설정 항목

### 1. 로그인 정보 (필수)

```python
USER_ID = "your_id"
USER_PW = "your_password"
```

⚠️ **보안 주의**: Git에 업로드되지 않도록 주의하세요!

### 2. 예약 오픈 시간

```python
# 즉시 실행 (테스트용)
RESERVATION_DAY = 0
RESERVATION_HOUR = 10
RESERVATION_MINUTE = 30

# 매월 25일 10시 30분에 실행
RESERVATION_DAY = 25
RESERVATION_HOUR = 10
RESERVATION_MINUTE = 30
```

### 3. 예약 설정

#### 방법 1: 기본 방식
```python
RESERVATION_CONFIG = {
    "dates": ["2026-02-09"],
    "hours": [8, 10],
    "court_number": 3,
}
```

#### 방법 2: 직접 지정
```python
RESERVATION_CONFIG = {
    "reservations": [
        {"date": "2026-02-09", "hour": 8, "court": 1},
        {"date": "2026-02-09", "hour": 10, "court": 1},
        {"date": "2026-02-09", "hour": 6, "court": 2},
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

### 4. 동시 접속 제한

```python
MAX_CONCURRENT = 3  # 최대 3개씩 동시 예약
```

---

## ⚠️ 중요 주의사항

### 1. 반드시 재시작 필요

config.py를 수정한 후에는 **반드시 컨테이너를 재시작**해야 합니다:

```bash
docker-compose restart
# 또는
docker restart tennis-reservation
```

Python 프로세스가 시작할 때만 config.py를 읽기 때문입니다.

### 2. 절대 경로 사용

볼륨 마운트 시 절대 경로를 사용하세요:

```yaml
# ✅ 올바른 방법
volumes:
  - /volume1/docker/apiserver/app/config.py:/app/config.py

# ❌ 잘못된 방법
volumes:
  - ./config.py:/app/config.py  # 상대 경로는 에러 발생 가능
```

### 3. 파일 권한 확인

```bash
# config.py 파일 권한 확인
ls -l /volume1/docker/apiserver/app/config.py

# 권한이 없으면 수정
chmod 644 /volume1/docker/apiserver/app/config.py
```

### 4. 파일 존재 확인

```bash
# config.py 파일이 있는지 확인
cat /volume1/docker/apiserver/app/config.py | head -20
```

---

## 🔍 문제 해결

### Q: config.py를 수정했는데 변경이 반영되지 않습니다

**A:** 컨테이너를 재시작하세요:

```bash
docker-compose restart
```

### Q: "No such file or directory" 에러가 발생합니다

**A:** config.py 파일이 호스트에 존재하는지 확인하세요:

```bash
# 파일 확인
ls -l /volume1/docker/apiserver/app/config.py

# 없으면 복사
cp /path/to/reservation/config.py /volume1/docker/apiserver/app/config.py
```

### Q: 설정이 이상하게 동작합니다

**A:** 로그를 확인하세요:

```bash
docker-compose logs -f

# 또는
docker logs -f tennis-reservation
```

### Q: 원본 config.py를 가져오려면?

**A:** 컨테이너 안의 파일을 복사하세요:

```bash
# 실행 중인 컨테이너에서 복사
docker cp tennis-reservation:/app/config.py /volume1/docker/apiserver/app/config.py
```

---

## 📚 완전한 설정 예시

### /volume1/docker/apiserver/app/config.py

```python
# -*- coding: utf-8 -*-
"""
고양시 체육시설 예약 프로그램 설정
"""

import os
from pathlib import Path

# 로그인 정보 - 여기에 실제 값 입력
USER_ID = "hongyver"
USER_PW = "hongyver12"

# 사이트 URL
MAIN_URL = "https://daehwa.gys.or.kr:451"
TENNIS_RESERVATION_URL = "https://daehwa.gys.or.kr:451/rent/tennis_rent.php"

# 시설 종류
FACILITY_TYPE = "테니스장"

# 예약 설정
RESERVATION_CONFIG = {
    "reservations": [
        {"date": "2026-02-09", "hour": 8, "court": 1},
        {"date": "2026-02-09", "hour": 10, "court": 1},
        {"date": "2026-02-09", "hour": 6, "court": 2},
    ]
}

# 예약 오픈 시간
RESERVATION_DAY = 0       # 0: 즉시 실행
RESERVATION_HOUR = 10
RESERVATION_MINUTE = 30

# 재시도 횟수
MAX_RETRY = 3

# 동시 접속 개수
MAX_CONCURRENT = 3

# 브라우저 설정
HEADLESS = False
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 10
```

---

## 🚀 빠른 시작 가이드

### 1. config.py 준비

```bash
# 디렉토리 생성
mkdir -p /volume1/docker/apiserver/app

# 원본 복사 (처음 한 번만)
docker cp tennis-reservation:/app/config.py /volume1/docker/apiserver/app/config.py
```

### 2. config.py 수정

```bash
vi /volume1/docker/apiserver/app/config.py
```

다음 항목들을 수정:
- `USER_ID` - 로그인 아이디
- `USER_PW` - 로그인 비밀번호
- `RESERVATION_DAY` - 0 (즉시 실행) 또는 25 (매월 25일)
- `RESERVATION_CONFIG` - 예약할 날짜/시간/코트

### 3. docker-compose.yml 확인

```yaml
volumes:
  - /volume1/docker/apiserver/app/config.py:/app/config.py
```

### 4. 재시작

```bash
docker-compose restart
```

### 5. 테스트

```bash
curl -X POST http://localhost:3100/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "reservations": [
      {"date": "2026-02-09", "hour": 8, "court": 1}
    ],
    "test_mode": true
  }'
```

---

## 📚 관련 문서

- [설정 가이드](CONFIG_GUIDE.md)
- [Docker 사용 가이드](README_DOCKER.md)
- [API 예약 가이드](API_RESERVE_GUIDE_v2.md)
