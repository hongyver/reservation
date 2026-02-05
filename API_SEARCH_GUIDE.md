# 검색(Search) API 사용 설명서

## 📋 목차

1. POST /search-weekend - 주말 빈자리 검색
2. POST /search-all     - 전체 빈자리 검색

---

## 1️⃣  POST /search-weekend

**주말(토/일)의 예약 가능 시간 검색**

### 요청 파라미터
```json
{
  "year": 2026,              // 필수: 연도
  "month": 2,                // 필수: 월 (1-12)
  "courts": [1, 2, 3, 4],   // 선택: 코트 번호 배열 (기본값: [1,2,3,4])
  "hours": [6, 8, 10]        // 선택: 시간 배열 (기본값: [6,8,10])
}
```

### 응답 예시
```json
{
  "year": 2026,
  "month": 2,
  "total": 15,
  "results": [
    {
      "date": "2026-02-01",
      "day": "토",
      "court": 1,
      "hour": 6,
      "time": "06:00~08:00"
    },
    {
      "date": "2026-02-01",
      "day": "토",
      "court": 2,
      "hour": 8,
      "time": "08:00~10:00"
    },
    {
      "date": "2026-02-08",
      "day": "토",
      "court": 1,
      "hour": 10,
      "time": "10:00~12:00"
    }
  ]
}
```

### 사용 예시

```bash
# 기본 사용 (모든 코트, 6/8/10시)
curl -X POST http://localhost:5000/search-weekend \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 2
  }'

# 특정 코트만 검색
curl -X POST http://localhost:5000/search-weekend \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 2,
    "courts": [1, 2]
  }'

# 특정 시간만 검색
curl -X POST http://localhost:5000/search-weekend \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 2,
    "hours": [8, 10, 12]
  }'

# 1번 코트, 아침 시간대만
curl -X POST http://localhost:5000/search-weekend \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 2,
    "courts": [1],
    "hours": [6, 8]
  }'
```

---

## 2️⃣  POST /search-all

**해당 월의 모든 날짜/시간 검색**

### 요청 파라미터
```json
{
  "year": 2026,              // 필수: 연도
  "month": 2,                // 필수: 월 (1-12)
  "courts": [1, 2, 3, 4]    // 선택: 코트 번호 배열 (기본값: [1,2,3,4])
}
```

### 응답 예시
```json
{
  "year": 2026,
  "month": 2,
  "total": 120,
  "skipped_dates": ["2026-02-15", "2026-02-16"],
  "results": [
    {
      "date": "2026-02-01",
      "day": "토",
      "court": 1,
      "hour": 6,
      "time": "06:00~08:00",
      "is_weekend": true
    },
    {
      "date": "2026-02-02",
      "day": "일",
      "court": 1,
      "hour": 8,
      "time": "08:00~10:00",
      "is_weekend": true
    },
    {
      "date": "2026-02-03",
      "day": "월",
      "court": 2,
      "hour": 10,
      "time": "10:00~12:00",
      "is_weekend": false
    }
  ]
}
```

### 사용 예시

```bash
# 기본 사용 (모든 코트, 모든 시간)
curl -X POST http://localhost:5000/search-all \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 2
  }'

# 특정 코트만 검색
curl -X POST http://localhost:5000/search-all \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 2,
    "courts": [3, 4]
  }'
```

---

## 3️⃣  차이점 비교

| 항목 | search-weekend | search-all |
|------|----------------|------------|
| **검색 날짜** | 주말만 (토/일) | 모든 날짜 (평일+주말) |
| **검색 시간** | 사용자 지정<br>(기본: 6, 8, 10시) | 모든 시간 고정<br>(6, 8, 10, 12, 14, 16, 18, 20시) |
| **is_weekend 필드** | ❌ 없음 | ✅ 있음 |
| **skipped_dates 필드** | ❌ 없음 | ✅ 있음 (휴장일 목록) |
| **속도** | 빠름 (주말만) | 느림 (전체 날짜) |
| **용도** | 주말 예약 찾기 | 전체 현황 파악 |

---

## 4️⃣  응답 필드 설명

### 공통 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| year | int | 검색한 연도 |
| month | int | 검색한 월 |
| total | int | 총 예약 가능 건수 |
| results | array | 예약 가능 시간 목록 |

### results 배열의 각 항목

| 필드 | 타입 | 설명 | search-weekend | search-all |
|------|------|------|----------------|------------|
| date | string | 날짜 (YYYY-MM-DD) | ✅ | ✅ |
| day | string | 요일 (월/화/.../일) | ✅ | ✅ |
| court | int | 코트 번호 (1-4) | ✅ | ✅ |
| hour | int | 시작 시간 (6, 8, 10...) | ✅ | ✅ |
| time | string | 시간대 (06:00~08:00) | ✅ | ✅ |
| is_weekend | bool | 주말 여부 | ❌ | ✅ |

### search-all 전용 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| skipped_dates | array | 휴장일로 추정되어 제외된 날짜 목록 |

---

## 5️⃣  Python 사용 예시

### 주말 검색

```python
import requests

# 주말 빈자리 검색
response = requests.post(
    'http://localhost:5000/search-weekend',
    json={
        'year': 2026,
        'month': 2,
        'courts': [1, 2, 3, 4],
        'hours': [6, 8, 10]
    }
)

data = response.json()
print(f"총 {data['total']}건 발견")

# 날짜별로 그룹화
from collections import defaultdict
by_date = defaultdict(list)
for item in data['results']:
    by_date[item['date']].append(item)

for date, slots in sorted(by_date.items()):
    print(f"{date} ({slots[0]['day']}):")
    for slot in slots:
        print(f"  {slot['court']}번 코트 {slot['time']}")
```

### 전체 검색

```python
import requests

# 전체 빈자리 검색
response = requests.post(
    'http://localhost:5000/search-all',
    json={
        'year': 2026,
        'month': 2,
        'courts': [1, 2, 3, 4]
    }
)

data = response.json()
print(f"총 {data['total']}건 발견")
print(f"휴장일: {data['skipped_dates']}")

# 주말만 필터링
weekends = [r for r in data['results'] if r['is_weekend']]
print(f"주말: {len(weekends)}건")

# 평일만 필터링
weekdays = [r for r in data['results'] if not r['is_weekend']]
print(f"평일: {len(weekdays)}건")

# 특정 시간대만 필터링 (아침 6-10시)
morning = [r for r in data['results'] if r['hour'] in [6, 8]]
print(f"아침 시간대: {len(morning)}건")

# 특정 코트만 필터링
court3 = [r for r in data['results'] if r['court'] == 3]
print(f"3번 코트: {len(court3)}건")
```

---

## 6️⃣  휴장일 감지 로직

### 휴장일로 판단하는 경우

모든 시간대 (06:00~22:00, 총 8개)가 예약 가능으로 표시되면 휴장일로 추정합니다.

**이유:**
- 정상 운영일에는 인기 시설이라 일부 예약이 있음
- 모든 시간이 비어있다 = 시스템 상에만 존재하는 날짜 (공휴일, 휴장일 등)

### skipped_dates 활용

```python
response = requests.post(
    'http://localhost:5000/search-all',
    json={'year': 2026, 'month': 2}
)

data = response.json()

# 휴장일 확인
if data['skipped_dates']:
    print("⚠️  다음 날짜는 휴장일로 추정됩니다:")
    for date in data['skipped_dates']:
        print(f"  - {date}")
```

---

## 7️⃣  에러 응답

### year, month 누락
```json
{
  "error": "year, month 필드 필요"
}
```
→ HTTP 400

### 로그인 실패
```json
{
  "error": "로그인 실패"
}
```
→ 자동 로그인 시도 중 실패

---

## 8️⃣  활용 예시

### 1. 주말 아침 시간대 찾기

```bash
curl -X POST http://localhost:5000/search-weekend \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 2,
    "hours": [6, 8]
  }'
```

### 2. 특정 코트의 전체 현황 파악

```bash
curl -X POST http://localhost:5000/search-all \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 2,
    "courts": [3]
  }'
```

### 3. 평일 저녁 시간대 찾기

```python
response = requests.post(
    'http://localhost:5000/search-all',
    json={'year': 2026, 'month': 2}
)

data = response.json()

# 평일 + 저녁(18시, 20시)
evening_weekdays = [
    r for r in data['results']
    if not r['is_weekend'] and r['hour'] in [18, 20]
]

print(f"평일 저녁: {len(evening_weekdays)}건")
```

---

## 9️⃣  성능 최적화 팁

### 1. 필요한 데이터만 요청

```bash
# ❌ 나쁜 예: 모든 코트 검색 후 필터링
curl -X POST http://localhost:5000/search-all \
  -d '{"year": 2026, "month": 2}'

# ✅ 좋은 예: 필요한 코트만 검색
curl -X POST http://localhost:5000/search-all \
  -d '{"year": 2026, "month": 2, "courts": [3]}'
```

### 2. 주말만 필요하면 search-weekend 사용

```bash
# ❌ 나쁜 예: search-all로 전체 검색 후 주말 필터링
# → 28일 전체 검색 (느림)

# ✅ 좋은 예: search-weekend 사용
# → 8일만 검색 (빠름)
curl -X POST http://localhost:5000/search-weekend \
  -d '{"year": 2026, "month": 2}'
```

---

## 🔟  전체 워크플로우 예시

```bash
# Step 1: 주말 빈자리 확인
curl -X POST http://localhost:5000/search-weekend \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 2}'

# Step 2: 특정 날짜 상세 확인
curl -X POST http://localhost:5000/check-slots \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-09", "court": 3}'

# Step 3: 예약 실행 (테스트)
curl -X POST http://localhost:5000/reserve-single \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-02-09",
    "hour": 8,
    "court": 3,
    "test_mode": true
  }'
```

---

## 📚 관련 문서

- [예약 API 가이드](API_RESERVE_GUIDE.md)
- [Docker 사용 가이드](README_DOCKER.md)
