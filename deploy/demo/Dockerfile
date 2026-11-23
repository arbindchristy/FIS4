FROM node:24.4.1-bookworm-slim@sha256:59dc16b4f436d8b03119f93de0d74236cba204ebe474d6545dfb4a9b0b1c2676 AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY frontend/ ./
RUN node --version && npm --version && npm run build

FROM python:3.13.7-slim-bookworm@sha256:781449467ffb6f04218f09b1ecdcdc7d22b289ee5da9ec498b024e24ad7a6db7
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PORT=10000
WORKDIR /app
COPY deploy/demo/requirements-linux.lock /tmp/requirements-linux.lock
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r /tmp/requirements-linux.lock && pip check
COPY api/ /app/api/
COPY simulator/ /app/simulator/
COPY readiness.py /app/readiness.py
COPY deploy/demo/server.py /app/demo_server.py
COPY --from=frontend /build/dist /app/frontend/dist
USER 10001:10001
EXPOSE 10000
STOPSIGNAL SIGTERM
CMD ["python", "-B", "demo_server.py"]
