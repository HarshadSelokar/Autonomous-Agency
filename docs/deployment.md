# Phase 20 Production Deployment & Infrastructure Guide

This document provides complete instructions for deploying the **Autonomous AI Organization Platform** in production environments using containerization, reverse proxying, TLS termination, and container orchestration.

---

## 1. Production Architecture Overview

```
                          [ Internet Traffic ]
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   Nginx Reverse   │
                         │    Proxy (TLS)    │
                         └─────────┬─────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │                                     │
                ▼                                     ▼
     ┌─────────────────────┐               ┌─────────────────────┐
     │  FastAPI API Server │               │  Background Worker  │
     │   (App Engine)      │               │   (Daemon Service)  │
     └──────────┬──────────┘               └──────────┬──────────┘
                │                                     │
                ├──────────────────┬──────────────────┤
                │                  │                  │
                ▼                  ▼                  ▼
     ┌──────────────────┐  ┌───────────────┐  ┌───────────────┐
     │    PostgreSQL    │  │ Redis (Async) │  │ MinIO / S3    │
     │ Connection Pool  │  │  Cache/Lock   │  │ Object Storage│
     └──────────────────┘  └───────────────┘  └───────────────┘
```

The production deployment consists of:
1. **Nginx Reverse Proxy**: Listens on ports 80/443, handles TLS termination, HTTP-to-HTTPS redirection, WebSocket proxying, security headers (`HSTS`, `X-Frame-Options`, `X-Content-Type-Options`), rate limiting, and Gzip compression.
2. **FastAPI Web API Container (`api`)**: Stateteless app server running ASGI server with connection pooling, CORS security, request correlation tracking (`X-Correlation-ID`), and health check probes (`/health/live`, `/health/ready`).
3. **Background Worker Container (`worker`)**: Daemon process running `WorkerLifecycleManager` and `TransactionalOutboxProcessor` to handle asynchronous task execution, event publishing, and retry isolation.
4. **PostgreSQL 16 Engine (`postgres`)**: Relational database with pooled connections (`DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`).
5. **Redis 7 Server (`redis`)**: In-memory data store for connection-pooled caching, locking, and rate limiting.
6. **MinIO / S3 Object Storage (`minio`)**: High-performance S3-compatible binary payload storage with SHA-256 integrity checksum verification.

---

## 2. Environment Configuration

Copy `.env.example` to `.env` and configure all required variables:

```bash
# Application Mode
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Security & Secrets (MUST NOT USE DEFAULT VALUES IN PRODUCTION)
SECRET_KEY=prod_super_secret_jwt_key_change_me_immediately_in_prod
GROQ_API_KEY=gsk_your_groq_production_api_key

# PostgreSQL Connection Pool
DATABASE_URL=postgresql+asyncpg://prod_user:secure_password@postgres:5432/autonomous_agency
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis Cache Pool
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50

# Object Storage
STORAGE_TYPE=s3
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET_NAME=autonomous-artifacts
S3_ACCESS_KEY_ID=prod_minio_access_key
S3_SECRET_ACCESS_KEY=prod_minio_secret_key
S3_REGION=us-east-1
```

---

## 3. Docker Compose Deployment

To build and launch the production stack:

```bash
# Build multi-stage Docker images
docker compose build

# Start services in detached daemon mode
docker compose up -d

# Verify container status
docker compose ps

# Inspect logs across services
docker compose logs -f api worker
```

---

## 4. Health Check Probes & Monitoring

The API container registers standard Kubernetes-compatible health probes:

* **Liveness Probe**: `GET http://localhost:8000/health/live`
  Returns `HTTP 200 OK` if the web application process is responsive.
* **Readiness Probe**: `GET http://localhost:8000/health/ready`
  Verifies connectivity to PostgreSQL, Redis connection pool, Object Storage availability, and transactional outbox depth. Returns `HTTP 503` if dependent infrastructure is unreachable.
