FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
COPY agent/ agent/

RUN pip install --no-cache-dir .

ENV POSTS_DIR=/data

VOLUME /data
EXPOSE 8000

CMD ["uvicorn", "agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
