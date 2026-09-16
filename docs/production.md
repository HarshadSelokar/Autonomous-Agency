# Production Hardening & Security Specification

This document details the security hardening measures, request safety controls, secret redaction, and startup validation implemented in **Phase 20**.

---

## 1. Fast-Fail Environment Validation

At application startup in production mode (`APP_ENV=production`), `validate_production_env()` performs automated checks before opening network sockets:

```python
from src.infrastructure.env_validation import validate_production_env

# Execution fails immediately (raising ValueError) if:
# 1. DEBUG=True in production
# 2. SQLite / local fallback URLs are used in production
# 3. Default or placeholder credentials (e.g. "postgres:postgres", "minioadmin") are detected
# 4. S3 credentials or Groq API keys are missing when required
```

---

## 2. Sensitive Secret Redaction in Structured Logging

All operational logs emitted by the platform are formatted as single-line JSON (`StructuredJsonFormatter`).

* **Redaction Policy**: String values matching patterns such as `gsk_`, `sk-`, `JWT`, `password`, `secret`, `bearer`, or `authorization` are automatically masked with `[REDACTED]`.
* **Context Preservation**: Log metadata (correlation IDs, timestamps, logger names, request paths) remains intact for auditing without exposing credentials.

---

## 3. HTTP Request Guardrails & Security Headers

### Security Headers Middleware
In production environments, `ProductionSecurityHeadersMiddleware` automatically injects security headers onto every HTTP response:

* `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
* `X-Frame-Options: DENY`
* `X-Content-Type-Options: nosniff`
* `X-XSS-Protection: 1; mode=block`
* `Content-Security-Policy: default-src 'self'`
* `Referrer-Policy: strict-origin-when-cross-origin`

### Request Payload Limits
To prevent Denial of Service (DoS) via memory exhaustion, `RequestSizeLimitMiddleware` inspects `Content-Length` headers:
* Requests exceeding **10 MB** (or configured `MAX_REQUEST_SIZE_BYTES`) are rejected immediately with `HTTP 413 Payload Too Large`.

---

## 4. Connection Pooling & Resource Bounds

| Component | Setting | Production Default | Purpose |
|---|---|---|---|
| PostgreSQL Pool | `DATABASE_POOL_SIZE` | 20 | Concurrent connection pool capacity |
| PostgreSQL Overflow | `DATABASE_MAX_OVERFLOW` | 10 | Temporary burst connection limit |
| PostgreSQL Recycle | `DATABASE_POOL_RECYCLE` | 1800 sec (30m) | Prevents stale closed connections |
| Redis Connection Pool | `REDIS_MAX_CONNECTIONS` | 50 | Async connection pool limit |
| Async Worker Drain | `DRAIN_TIMEOUT_SECONDS` | 30.0 sec | Max wait time for in-flight job completion |
