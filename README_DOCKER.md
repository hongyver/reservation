# Docker 사용 가이드

## 1. Docker 설치 확인

```bash
docker --version
docker-compose --version
```

## 2. Docker 이미지 빌드

```bash
# reservation 디렉토리에서 실행
cd /Users/hongyver/project/reservation

# 이미지 빌드
docker build -t tennis-reservation .
```

## 3. 환경변수 설정

### 방법 1: docker-compose.yml 수정 (권장)

`docker-compose.yml` 파일 수정:

```yaml
environment:
  - TZ=Asia/Seoul
  - TENNIS_USER_ID=your_id           # 로그인 ID
  - TENNIS_USER_PW=your_password     # 로그인 PW
  - TENNIS_RESERVATION_DAY=0         # 0: 즉시 실행, 25: 매월 25일
  - TENNIS_RESERVATION_HOUR=10       # 예약 시간 (시)
  - TENNIS_RESERVATION_MINUTE=30     # 예약 시간 (분)
```

### 방법 2: .env 파일 사용

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 수정:

```env
TENNIS_USER_ID=your_id
TENNIS_USER_PW=your_password
TENNIS_RESERVATION_DAY=0
TENNIS_RESERVATION_HOUR=10
TENNIS_RESERVATION_MINUTE=30
```

`docker-compose.yml`에서 .env 파일 참조:

```yaml
env_file:
  - .env
```

## 4. Docker Compose로 실행 (권장)

```bash
# 백그라운드로 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 재시작 (설정 변경 후)
docker-compose restart

# 중지
docker-compose down

# 완전히 재빌드 (Dockerfile 변경 시)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 5. Docker 직접 실행

```bash
# API 서버 실행 (환경변수 포함)
docker run -d \
  --name tennis-reservation \
  -p 3100:3100 \
  -e TZ=Asia/Seoul \
  -e TENNIS_USER_ID=your_id \
  -e TENNIS_USER_PW=your_password \
  -e TENNIS_RESERVATION_DAY=0 \
  tennis-reservation

# 로그 확인
docker logs -f tennis-reservation

# 중지 및 제거
docker stop tennis-reservation
docker rm tennis-reservation
```

## ⚠️ 중요 주의사항

### config.py 파일 수정은 권장하지 않습니다!

Docker 컨테이너 내부의 `/volume1/docker/apiserver/app/config.py` 파일을 직접 수정하면:
- **변경사항이 반영되지 않습니다** (Python 프로세스가 이미 시작되어 config.py를 로드한 상태)
- 컨테이너 재시작 필요
- 재빌드 시 변경사항 손실 가능

### ✅ 올바른 방법: 환경변수 사용

**docker-compose.yml** 파일을 수정하고 재시작:

```bash
# 1. docker-compose.yml 수정
# environment:
#   - TENNIS_RESERVATION_DAY=0

# 2. 컨테이너 재시작
docker-compose restart

# 또는 완전히 재시작
docker-compose down
docker-compose up -d
```

### 환경변수 우선순위

1. Docker 환경변수 (`-e` 또는 `environment:`)
2. .env 파일
3. config.py 파일 기본값

환경변수로 설정하면 **즉시 반영**됩니다 (재시작 후).

## 6. config.py 볼륨 마운트 (비권장)

config.py를 직접 수정하려면 볼륨 마운트 후 **반드시 재시작** 필요:

```bash
docker run -d \
  --name tennis-reservation \
  -p 3100:3100 \
  -v /volume1/docker/apiserver/app/config.py:/app/config.py \
  -e TZ=Asia/Seoul \
  tennis-reservation

# config.py 수정 후 반드시 재시작
docker restart tennis-reservation
```

또는 docker-compose.yml에서:

```yaml
volumes:
  - /volume1/docker/apiserver/app/config.py:/app/config.py

# config.py 수정 후
# docker-compose restart
```

## 7. API 테스트

```bash
# 헬스 체크
curl http://localhost:5000/health

# 설정 조회
curl http://localhost:5000/config

# 로그인 테스트
curl -X POST http://localhost:5000/check-login

# 예약 실행 (테스트)
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "dates": ["2026-02-09"],
    "hours": [8],
    "court": 3,
    "test_mode": true
  }'
```

## 7. 유용한 Docker 명령어

```bash
# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인
docker ps -a

# 컨테이너 내부 접속
docker exec -it tennis-reservation /bin/bash

# 이미지 확인
docker images

# 이미지 삭제
docker rmi tennis-reservation

# 컨테이너 로그 (실시간)
docker logs -f tennis-reservation

# 컨테이너 재시작
docker restart tennis-reservation
```

## 8. 트러블슈팅

### 포트가 이미 사용 중인 경우

```bash
# 다른 포트로 실행 (예: 8080)
docker run -d -p 8080:5000 tennis-reservation
```

### 이미지 강제 재빌드

```bash
docker build --no-cache -t tennis-reservation .
```

### 컨테이너가 즉시 종료되는 경우

```bash
# 로그 확인
docker logs tennis-reservation

# 강제로 bash 실행하여 디버깅
docker run -it --entrypoint /bin/bash tennis-reservation
```

## 9. 프로덕션 환경 설정

### gunicorn 설정 (Dockerfile에 포함됨)

- Workers: 2개
- Timeout: 120초
- 바인딩: 0.0.0.0:5000

### 환경 변수 설정

```bash
docker run -d \
  -p 5000:5000 \
  -e TZ=Asia/Seoul \
  -e PYTHONUNBUFFERED=1 \
  tennis-reservation
```

## 10. n8n과 연동

n8n에서 HTTP Request 노드 사용:

- URL: `http://tennis-reservation:5000/reserve`
- Method: POST
- Body:
  ```json
  {
    "dates": ["2026-02-09"],
    "hours": [8],
    "court": 3,
    "test_mode": false
  }
  ```

같은 Docker 네트워크에 있어야 함:

```bash
docker network create tennis-net
docker run -d --network tennis-net --name tennis-reservation ...
docker run -d --network tennis-net --name n8n ...
```
