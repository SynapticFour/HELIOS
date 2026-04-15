FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --upgrade pip build && python -m build

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/dist/*.whl /tmp/helios.whl
RUN python -m pip install --no-cache-dir /tmp/helios.whl && rm -f /tmp/helios.whl
EXPOSE 8765
CMD ["helios", "serve", "--host", "0.0.0.0"]
