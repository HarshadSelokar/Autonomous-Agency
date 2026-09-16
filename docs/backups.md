# Database Backup & Disaster Recovery Operational Guide

## Overview
This document outlines the database backup, restore, and disaster recovery procedures for the Autonomous AI Organization Platform.

---

## 1. Automated Backup Execution

Backups capture database schemas, metadata, outbox records, and entity relations. Backup payloads are integrity-hashed using SHA-256 and uploaded to Object Storage (S3 / MinIO).

### Run Manual / Scheduled Backup:
```bash
python -m scripts.backup_database
```

Output:
```
DATABASE BACKUP COMPLETED SUCCESSFULLY
  Backup Key:  backups/db_backup_20260917_013000.json
  Storage Ref: s3://autonomous-artifacts/backups/db_backup_20260917_013000.json
  Checksum:    a3f5b901...
```

---

## 2. Restore Execution

Restores database schema and records from Object Storage, verifying SHA-256 checksums and checking database health.

### Run Restore Command:
```bash
python -m scripts.restore_database backups/db_backup_20260917_013000.json
```

---

## 3. Disaster Recovery Validation Pipeline

1. **Fetch Backup Payload**: Retrieve backup JSON bytes from S3/MinIO.
2. **Checksum Verification**: Validate SHA-256 hash against expected metadata.
3. **Schema Recreation**: Apply migrations / schema tables (`Base.metadata.create_all`).
4. **Data Restoration**: Populate entity tables.
5. **Health Check**: Run `/health/ready` probe and verify database connectivity.
