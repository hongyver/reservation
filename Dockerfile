FROM python:3.11-slim

WORKDIR /app

# 필요한 패키지 설치
RUN pip install --no-cache-dir flask requests beautifulsoup4 gunicorn

# 소스 복사
COPY config.py .
COPY reservation_http.py .
COPY api_server.py .

# 포트 노출
EXPOSE 3100

# gunicorn으로 프로덕션 실행
CMD ["gunicorn", "--bind", "0.0.0.0:3100", "--workers", "2", "--timeout", "120", "api_server:app"]
