# 브라우저 모드 문제 해결 가이드

## ChromeDriver 에러 해결 방법

macOS에서 `main.py --test --browser` 실행 시 chromedriver 에러가 발생하는 경우 아래 방법들을 시도하세요.

---

## 🚀 빠른 해결 방법 (권장)

### 방법 1: 자동 스크립트 실행

```bash
cd /Users/hongyver/project/reservation
./fix_chromedriver.sh
```

이 스크립트는 다음 작업을 자동으로 수행합니다:
- chromedriver 캐시 삭제
- selenium 및 webdriver-manager 재설치
- Chrome 버전 확인
- 로그인 테스트 실행

---

## 🔧 수동 해결 방법

### 1단계: ChromeDriver 캐시 삭제

```bash
rm -rf ~/.wdm
```

### 2단계: 패키지 업그레이드

```bash
pip3 install --upgrade selenium webdriver-manager
```

### 3단계: Chrome 버전 확인

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

**현재 시스템:** Google Chrome 144.0.7559.97

Chrome이 설치되어 있지 않으면:
- https://www.google.com/chrome 에서 다운로드하여 설치

### 4단계: 테스트

```bash
cd /Users/hongyver/project/reservation
python3 main.py --check --browser
```

---

## 💡 개선 사항

### reservation.py 브라우저 설정 개선

다음 항목들이 개선되었습니다:

1. **새로운 headless 모드 사용**
   - `--headless=new` (기존 `--headless`보다 안정적)

2. **안정성 향상 옵션 추가**
   ```python
   --disable-software-rasterizer
   --disable-extensions
   --disable-plugins
   --disable-infobars
   --ignore-certificate-errors
   --remote-debugging-port=9222
   ```

3. **WebDriver 감지 우회 개선**
   - CDP 명령으로 더 강력한 감지 우회

4. **폴백 메커니즘 추가**
   - ChromeDriverManager 실패 시 시스템 chromedriver 자동 사용

---

## 🐛 여전히 에러가 발생하는 경우

### 에러 1: "chromedriver not found"

**해결:**
```bash
# Homebrew로 직접 설치
brew install chromedriver

# macOS 보안 설정 해제
xattr -d com.apple.quarantine $(which chromedriver)
```

### 에러 2: "This version of ChromeDriver only supports Chrome version XX"

**원인:** Chrome 버전과 ChromeDriver 버전 불일치

**해결:**
```bash
# 캐시 삭제 후 재설치
rm -rf ~/.wdm
python3 main.py --check --browser  # 자동으로 맞는 버전 다운로드
```

### 에러 3: "chromedriver cannot be opened because the developer cannot be verified"

**원인:** macOS 보안 설정

**해결:**
```bash
# chromedriver 경로 찾기
CHROMEDRIVER_PATH=$(python3 -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())")

# 보안 속성 제거
xattr -d com.apple.quarantine "$CHROMEDRIVER_PATH"
```

### 에러 4: 세그멘테이션 폴트 (Segmentation fault)

**원인:** 브라우저 옵션 충돌

**해결:** config.py에서 HEADLESS 모드 변경
```python
# config.py
HEADLESS = False  # True → False로 변경
```

---

## 🔍 디버깅 팁

### 1. Chrome과 ChromeDriver 버전 확인

```bash
# Chrome 버전
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

# ChromeDriver 버전
python3 -c "from selenium import webdriver; from selenium.webdriver.chrome.service import Service; from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())" | head -1
```

### 2. 상세 로그 확인

```bash
# 디버그 모드로 실행
python3 main.py --check --browser 2>&1 | tee browser_debug.log
```

### 3. 최소 테스트 코드

```python
# test_browser.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("브라우저 시작 성공!")
driver.get("https://www.google.com")
print(f"현재 URL: {driver.current_url}")

driver.quit()
```

실행:
```bash
python3 test_browser.py
```

---

## 📚 대안 방법

### HTTP 모드 사용 (브라우저 없이)

브라우저 모드가 계속 문제가 된다면, HTTP 모드를 사용하세요:

```bash
# 브라우저 없이 실행 (더 빠르고 안정적)
python3 main.py --test          # 브라우저 모드 대신 HTTP 모드
python3 main.py --check         # HTTP 로그인 테스트
```

**HTTP 모드 장점:**
- 브라우저 불필요 (chromedriver 문제 없음)
- 더 빠른 실행 속도
- 메모리 사용량 적음
- 서버 환경에서 안정적

**HTTP 모드 단점:**
- 시각적 확인 불가능
- 일부 복잡한 JavaScript 동작 처리 불가능

---

## 🆘 추가 지원

위 방법으로 해결되지 않으면:

1. **에러 로그 수집**
   ```bash
   python3 main.py --check --browser 2>&1 | tee error.log
   ```

2. **시스템 정보 확인**
   ```bash
   sw_vers  # macOS 버전
   python3 --version  # Python 버전
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version  # Chrome 버전
   pip3 list | grep -E "selenium|webdriver"  # 패키지 버전
   ```

3. **GitHub 이슈 등록**
   - 위 정보와 error.log를 첨부하여 이슈 등록

---

## ✅ 해결 확인

다음 명령어가 성공하면 문제가 해결된 것입니다:

```bash
python3 main.py --check --browser
```

**성공 메시지:**
```
[SUCCESS] 로그인 성공!
[INFO] 예약 가능 시간대: ['06:00', '08:00', ...]
[SUCCESS] 모든 테스트 통과!
```
