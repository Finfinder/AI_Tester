FROM python:3.11-slim
WORKDIR /app
COPY task/ ./task/
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest pytest-json-report git+https://github.com/openai/evals.git
CMD ["pytest", "-q", "task/tests", "--json-report", "--json-report-file=/app/pytest_report.json"]
