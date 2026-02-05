# 예약(Reserve) API 사용 설명서 v2

## 📋 3가지 예약 방법

코트별로 다른 시간을 예약할 수 있도록 개선되었습니다!

### 방법 비교표

| 방법 | 사용 케이스 | 파라미터 |
|------|-------------|----------|
| **방법 1** | 모든 코트에 같은 시간 적용 | `dates`, `hours`, `courts` |
| **방법 2** | 각 예약을 개별적으로 지정 (가장 유연) | `reservations` ✨ |
| **방법 3** | 코트별 시간대 지정 | `dates`, `court_schedules` ✨ |

---

## 방법 1: 기존 방식 (모든 코트에 같은 시간)

모든 코트에 동일한 시간대를 적용합니다.

### 요청 예시
```json
{
  "dates": ["2026-02-09"],
  "hours": [8, 10],
  "courts": [1, 2, 3],
  "test_mode": true
}
```

### 결과
- 1번 코트: 8시, 10시
- 2번 코트: 8시, 10시
- 3번 코트: 8시, 10시
- **총 6건 예약**

### curl 예시
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

---

## 방법 2: 예약 목록 직접 지정 ✨ (추천)

각 예약을 개별적으로 지정합니다. **가장 유연한 방법**입니다.

### 요청 예시
```json
{
  "reservations": [
    {"date": "2026-02-09", "hour": 8, "court": 1},
    {"date": "2026-02-09", "hour": 10, "court": 1},
    {"date": "2026-02-09", "hour": 6, "court": 2},
    {"date": "2026-02-09", "hour": 12, "court": 3},
    {"date": "2026-02-16", "hour": 8, "court": 1}
  ],
  "test_mode": true
}
```

### 결과
- 2026-02-09: 1번 코트 8시, 10시 / 2번 코트 6시 / 3번 코트 12시
- 2026-02-16: 1번 코트 8시
- **총 5건 예약**

### curl 예시
```bash
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "reservations": [
      {"date": "2026-02-09", "hour": 8, "court": 1},
      {"date": "2026-02-09", "hour": 10, "court": 1},
      {"date": "2026-02-09", "hour": 6, "court": 2}
    ],
    "test_mode": true
  }'
```

### Python 예시
```python
import requests

# 코트별로 완전히 다른 시간 예약
reservations = [
    {'date': '2026-02-09', 'hour': 8, 'court': 1},
    {'date': '2026-02-09', 'hour': 10, 'court': 1},
    {'date': '2026-02-09', 'hour': 6, 'court': 2},
    {'date': '2026-02-09', 'hour': 8, 'court': 2},
    {'date': '2026-02-09', 'hour': 12, 'court': 3}
]

response = requests.post(
    'http://localhost:5000/reserve',
    json={
        'reservations': reservations,
        'test_mode': True
    }
)

result = response.json()
print(f"결과: {result['summary']}")

# 코트별로 그룹화하여 출력
from collections import defaultdict
by_court = defaultdict(list)
for r in result['results']:
    by_court[r['court']].append(r)

for court in sorted(by_court.keys()):
    print(f"{court}번 코트:")
    for item in by_court[court]:
        status = '✓' if item['success'] else '✗'
        print(f"  {status} {item['date']} {item['hour']:02d}:00 - {item['message']}")
```

---

## 방법 3: 코트별 시간 지정 ✨

코트별로 다른 시간대를 지정하고, 여러 날짜에 적용할 수 있습니다.

### 요청 예시
```json
{
  "dates": ["2026-02-09", "2026-02-16"],
  "court_schedules": [
    {"court": 1, "hours": [8, 10]},
    {"court": 2, "hours": [6, 8]},
    {"court": 3, "hours": [10, 12, 14]}
  ],
  "test_mode": true
}
```

### 결과
**2026-02-09:**
- 1번 코트: 8시, 10시
- 2번 코트: 6시, 8시
- 3번 코트: 10시, 12시, 14시

**2026-02-16:**
- 1번 코트: 8시, 10시
- 2번 코트: 6시, 8시
- 3번 코트: 10시, 12시, 14시

**총 14건 예약** (7건 × 2일)

### curl 예시
```bash
curl -X POST http://localhost:5000/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "dates": ["2026-02-09"],
    "court_schedules": [
      {"court": 1, "hours": [8, 10]},
      {"court": 2, "hours": [6, 8]},
      {"court": 3, "hours": [10, 12, 14]}
    ],
    "test_mode": true
  }'
```

### Python 예시
```python
import requests

# 코트별 선호 시간대 + 여러 날짜
response = requests.post(
    'http://localhost:5000/reserve',
    json={
        'dates': ['2026-02-09', '2026-02-16'],
        'court_schedules': [
            {'court': 1, 'hours': [8, 10]},      # 1번 코트: 아침
            {'court': 2, 'hours': [6, 8]},       # 2번 코트: 이른 아침
            {'court': 3, 'hours': [10, 12, 14]}  # 3번 코트: 오전~오후
        ],
        'test_mode': True
    }
)

result = response.json()
print(f"총 {len(result['results'])}건 예약 시도")
print(f"결과: {result['summary']}")

# 날짜별, 코트별로 그룹화
from collections import defaultdict
by_date = defaultdict(lambda: defaultdict(list))
for r in result['results']:
    by_date[r['date']][r['court']].append(r)

for date in sorted(by_date.keys()):
    print(f"{date}:")
    for court in sorted(by_date[date].keys()):
        print(f"  {court}번 코트:")
        for item in by_date[date][court]:
            status = '✓' if item['success'] else '✗'
            print(f"    {status} {item['hour']:02d}:00 - {item['message']}")
```

---

## 어떤 방법을 사용할까?

### 방법 1 사용 시나리오
- ✅ 모든 코트에 동일한 시간대 적용
- ✅ 간단한 예약
- 예: 토요일 오전 시간대를 모든 코트에 예약

### 방법 2 사용 시나리오 (추천)
- ✅ 코트별로 완전히 다른 날짜/시간
- ✅ 가장 세밀한 제어
- ✅ 복잡한 예약 패턴
- 예: 1번 코트는 주말 아침, 2번 코트는 평일 저녁

### 방법 3 사용 시나리오
- ✅ 코트별 선호 시간대가 있을 때
- ✅ 같은 패턴을 여러 날짜에 반복
- 예: 매주 토요일마다 코트별로 다른 시간대 예약

---

## 응답 형식

모든 방법의 응답 형식은 동일합니다.

```json
{
  "success": true,
  "summary": "4/5건 성공",
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
      "success": true,
      "message": "대관접수 완료"
    },
    {
      "date": "2026-02-09",
      "hour": 6,
      "court": 2,
      "success": true,
      "message": "대관접수 완료"
    },
    {
      "date": "2026-02-09",
      "hour": 12,
      "court": 3,
      "success": true,
      "message": "대관접수 완료"
    },
    {
      "date": "2026-02-16",
      "hour": 8,
      "court": 1,
      "success": false,
      "message": "이미 예약된 시간"
    }
  ]
}
```

---

## 에러 응답

### 방법 2: reservations 관련 에러

```json
{
  "error": "reservations는 배열이어야 합니다."
}
```

```json
{
  "error": "reservations[0]에 date 필드 필요"
}
```

### 방법 3: court_schedules 관련 에러

```json
{
  "error": "court_schedules는 배열이어야 합니다."
}
```

```json
{
  "error": "dates 필드가 필요합니다."
}
```

```json
{
  "error": "court_schedules 항목에 court, hours 필드 필요"
}
```

---

## 실전 예제

### 예제 1: 주말 다른 코트 예약

```python
# 토요일과 일요일에 각각 다른 코트 예약
reservations = []

# 토요일 (2026-02-07): 1번 코트
for hour in [8, 10]:
    reservations.append({
        'date': '2026-02-07',
        'hour': hour,
        'court': 1
    })

# 일요일 (2026-02-08): 2번 코트
for hour in [6, 8]:
    reservations.append({
        'date': '2026-02-08',
        'hour': hour,
        'court': 2
    })

response = requests.post(
    'http://localhost:5000/reserve',
    json={'reservations': reservations, 'test_mode': True}
)
```

### 예제 2: 코트별 선호 시간 패턴

```python
# 매주 같은 패턴으로 예약
# 1번: 아침, 2번: 점심, 3번: 저녁
response = requests.post(
    'http://localhost:5000/reserve',
    json={
        'dates': ['2026-02-07', '2026-02-14', '2026-02-21', '2026-02-28'],
        'court_schedules': [
            {'court': 1, 'hours': [6, 8]},    # 이른 아침
            {'court': 2, 'hours': [10, 12]},  # 오전
            {'court': 3, 'hours': [18, 20]}   # 저녁
        ],
        'test_mode': True
    }
)
```

---

## ⚠️ 중요 주의사항

1. **예약 오픈 시간 대기 (중요!)**
   - **CLI/Browser/API 모두** config.py의 RESERVATION_DAY 설정에 따라 동작합니다
   - **RESERVATION_DAY = 0**: 즉시 실행 (테스트용)
   - **RESERVATION_DAY = 25**: 매월 25일에만 실행
     - 오늘이 25일이면: 설정한 시간(RESERVATION_HOUR:RESERVATION_MINUTE)까지 대기 후 실행
     - 오늘이 25일보다 크면: "이미 지났습니다" 에러 (실행 안됨)
     - 오늘이 25일보다 작으면: "아직 예약일이 아닙니다" 에러 (실행 안됨)
   - **API 사용 시**: 예약일에 맞춰 cron 등으로 호출하거나 RESERVATION_DAY=0으로 설정

2. **test_mode=false로 실행 시 실제 예약됨**
   - 취소 불가능!

3. **동일 날짜에 1건만 예약 가능**
   - "한 건 이상 예약" 오류 발생 가능

4. **동시 접속 제한**
   - config.py의 MAX_CONCURRENT 설정
   - 많은 예약 시 순차적으로 처리됨

5. **reservations 배열 사용 시**
   - 가장 유연하지만 수동으로 입력 필요
   - 실수 방지를 위해 코드로 생성 권장

6. **court_schedules 사용 시**
   - dates와 함께 사용 필수
   - 모든 날짜에 같은 패턴 적용됨

---

## ⏰ 예약 시간 설정 방법

### 방법 1: config.py 설정 (권장)

config.py에서 예약일을 설정하면 CLI/Browser/API 모두 자동으로 대기합니다:

```python
# config.py
RESERVATION_DAY = 25      # 매월 25일
RESERVATION_HOUR = 10     # 10시
RESERVATION_MINUTE = 30   # 30분

# 즉시 실행 (테스트용)
RESERVATION_DAY = 0
```

이렇게 설정하면:
- CLI 모드: `python3 main.py` 실행 시 25일 10:30까지 자동 대기
- API 모드: API 서버 실행 후 API 호출 시 25일 10:30까지 자동 대기

### 방법 2: cron으로 정확한 시간에 호출 (RESERVATION_DAY=0)

config.py에서 `RESERVATION_DAY=0`으로 설정하고 cron으로 호출:

```bash
# crontab 편집
crontab -e

# 매월 25일 10시 30분에 API 호출
30 10 25 * * curl -X POST http://localhost:5000/reserve -H "Content-Type: application/json" -d '{"dates":["2026-02-09"],"hours":[8],"court":1,"test_mode":false}'
```

### 방법 3: Python APScheduler (RESERVATION_DAY=0)

```python
from apscheduler.schedulers.blocking import BlockingScheduler
import requests

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', day=25, hour=10, minute=30)
def reserve_job():
    response = requests.post(
        'http://localhost:5000/reserve',
        json={
            'dates': ['2026-02-09'],
            'hours': [8],
            'court': 1,
            'test_mode': False
        }
    )
    print(response.json())

scheduler.start()
```

### 방법 4: n8n Workflow (RESERVATION_DAY=0)

1. **Schedule Trigger**: 매월 25일 10:30
2. **HTTP Request**: POST http://your-server:5000/reserve

## 💡 어떤 방법을 선택할까?

| 방법 | 장점 | 단점 | 추천 |
|------|-----|-----|------|
| **config.py 설정** | 간단, 별도 스케줄러 불필요 | 프로그램이 계속 실행되어야 함 | ✅ CLI/Browser 모드 |
| **cron + RESERVATION_DAY=0** | 정확한 시간 제어, 리소스 효율적 | 설정 필요 | ✅ API 모드 |
| **APScheduler + RESERVATION_DAY=0** | Python으로 통합 관리 | 별도 스크립트 필요 | API 자동화 |
| **n8n + RESERVATION_DAY=0** | 시각적 워크플로우 | n8n 설정 필요 | 워크플로우 통합 |

---

## 📚 관련 문서

- [검색 API 가이드](API_SEARCH_GUIDE.md)
- [Docker 사용 가이드](README_DOCKER.md)
- [인증 가이드](AUTH_GUIDE.md)
