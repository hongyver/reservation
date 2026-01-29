# 로그인 인증 가이드

고양시 테니스장 예약 프로그램의 로그인 정보 설정 방법입니다.

---

## 🔐 3가지 인증 방법

### 방법 1: .env 파일 (권장)

가장 안전하고 편리한 방법입니다.

1. `.env.example` 파일을 복사:
   ```bash
   cp .env.example .env
   ```

2. `.env` 파일 수정:
   ```bash
   TENNIS_USER_ID=your_id
   TENNIS_USER_PW=your_password
   ```

3. 실행:
   ```bash
   python3 main.py --test
   ```

**장점:**
- `.env` 파일은 `.gitignore`에 포함되어 Git에 업로드되지 않음
- 여러 환경에서 쉽게 관리 가능
- 소스 코드 수정 불필요

---

### 방법 2: 환경변수

CI/CD 또는 Docker 환경에 적합합니다.

```bash
export TENNIS_USER_ID=your_id
export TENNIS_USER_PW=your_password
python3 main.py --test
```

Docker 실행 시:
```bash
docker run -e TENNIS_USER_ID=your_id -e TENNIS_USER_PW=your_password ...
```

Docker Compose:
```yaml
environment:
  - TENNIS_USER_ID=your_id
  - TENNIS_USER_PW=your_password
```

---

### 방법 3: 실행 시 입력

환경변수나 .env 파일이 없으면 자동으로 입력을 요청합니다.

```bash
$ python3 main.py --test

============================================================
로그인 정보 입력
============================================================

[INFO] 환경변수나 .env 파일에 로그인 정보가 없습니다.
[INFO] 직접 입력하시거나, .env 파일을 생성하세요.

아이디: your_id
비밀번호: ********

...
```

**장점:**
- 임시 테스트에 유용
- 파일이나 환경변수 설정 불필요

**단점:**
- 매번 입력해야 함
- 자동화에 부적합

---

## 🌐 API 서버 인증

API 서버를 사용할 때는 3가지 방법이 있습니다.

### 방법 1: 환경변수 (서버 전체 기본값)

API 서버 시작 시 환경변수 설정:

```bash
export TENNIS_USER_ID=your_id
export TENNIS_USER_PW=your_password
python3 api_server.py
```

또는 Docker:

```bash
docker run -e TENNIS_USER_ID=your_id -e TENNIS_USER_PW=your_password ...
```

이제 API 요청 시 user_id, user_pw를 생략 가능:

```bash
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "dates": ["2026-02-09"],
    "hours": [8],
    "court": 1,
    "test_mode": true
  }'
```

---

### 방법 2: 요청 파라미터 (권장)

각 요청마다 다른 계정 사용 가능:

```bash
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your_id",
    "user_pw": "your_password",
    "dates": ["2026-02-09"],
    "hours": [8],
    "court": 1,
    "test_mode": true
  }'
```

---

### 방법 3: .env 파일 (Docker 환경)

docker-compose.yml에서 .env 파일 참조:

```yaml
services:
  tennis-reservation:
    build: .
    env_file:
      - .env
    ports:
      - "3100:5000"
```

.env 파일:
```
TENNIS_USER_ID=your_id
TENNIS_USER_PW=your_password
```

---

## 🔒 보안 권장사항

1. **절대 config.py에 ID/PW 저장하지 마세요**
   - Git에 업로드될 수 있습니다

2. **.env 파일 사용 권장**
   - `.gitignore`에 포함되어 안전합니다

3. **환경변수 사용 (서버 환경)**
   - CI/CD, Docker 등에서 안전하게 관리 가능

4. **API 요청 시**
   - HTTPS 사용
   - 네트워크 로그 주의

---

## 📋 인증 우선순위

프로그램은 다음 순서로 인증 정보를 확인합니다:

1. **API 요청 파라미터** (API 서버만)
   - `user_id`, `user_pw` 필드

2. **환경변수**
   - `TENNIS_USER_ID`, `TENNIS_USER_PW`

3. **.env 파일**
   - 프로젝트 루트의 `.env` 파일

4. **프롬프트 입력**
   - 위 모두 없으면 직접 입력 요청 (CLI만)

5. **에러**
   - API는 인증 정보가 없으면 400 에러 반환

---

## ❌ 더 이상 사용되지 않음

~~config.py에 직접 ID/PW 저장~~ (보안상 위험)

```python
# ❌ 더 이상 사용하지 마세요
USER_ID = "hongyver"  # Git에 업로드될 수 있습니다!
USER_PW = "password"  # 보안 위험!
```

대신 .env 파일을 사용하세요:

```bash
# ✅ .env 파일 사용
TENNIS_USER_ID=hongyver
TENNIS_USER_PW=your_password
```

---

## 💡 예제

### CLI 사용

```bash
# .env 파일 설정
echo "TENNIS_USER_ID=hongyver" > .env
echo "TENNIS_USER_PW=your_password" >> .env

# 테스트 실행
python3 main.py --test

# 브라우저 모드
python3 main.py --browser --test
```

### API 사용

```python
import requests

# 환경변수 설정된 서버
response = requests.post(
    'http://localhost:5000/reserve',
    json={
        'dates': ['2026-02-09'],
        'hours': [8],
        'court': 1,
        'test_mode': True
    }
)

# 또는 요청 파라미터로 전달
response = requests.post(
    'http://localhost:5000/reserve',
    json={
        'user_id': 'your_id',
        'user_pw': 'your_password',
        'dates': ['2026-02-09'],
        'hours': [8],
        'court': 1,
        'test_mode': True
    }
)

print(response.json())
```

---

## 🆘 문제 해결

### "user_id 또는 user_pw 필요" 에러

API 호출 시 이 에러가 발생하면:

1. 환경변수 확인:
   ```bash
   echo $TENNIS_USER_ID
   echo $TENNIS_USER_PW
   ```

2. .env 파일 확인:
   ```bash
   cat .env
   ```

3. 요청 파라미터에 직접 포함:
   ```json
   {
     "user_id": "your_id",
     "user_pw": "your_password",
     ...
   }
   ```

### 로그인 실패

1. ID/PW가 정확한지 확인
2. 공식 사이트에서 직접 로그인 테스트
3. 로그인 테스트 실행:
   ```bash
   python3 main.py --check
   ```

---

## 📚 관련 문서

- [설정 가이드](CONFIG_GUIDE.md)
- [API 가이드](API_RESERVE_GUIDE_v2.md)
- [Docker 가이드](README_DOCKER.md)
