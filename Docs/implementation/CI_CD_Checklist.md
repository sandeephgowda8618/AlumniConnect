# AlumniConnect — CI/CD & Deployment Readiness Checklist

**Date**: 2026-11-03  
**Status**: Authoritative Release Checklist  
**Target Repository**: `https://github.com/sandeephgowda8618/AlumniConnect.git`

---

## 1. Automated Continuous Integration (GitHub Actions)

The repository includes a production-grade GitHub Actions workflow (`.github/workflows/ci.yml`) configured to run on every push and pull request targeting `main` or `master`.

| Checkpoint | Command / Action | Validation Criteria | Status |
| :--- | :--- | :--- | :--- |
| **Code Linting (Backend)** | `flake8 backend/app` | 0 syntax errors, max complexity < 15, PEP8 line length compliant | **Configured** |
| **Type & Linting (Frontend)** | `npm run lint` | ESLint rules satisfied across all 20 Next.js routes | **Configured** |
| **Security Audit (Python)** | `pip-audit` | Zero critical known CVEs in backend dependencies | **Configured** |
| **Security Audit (Node.js)** | `npm audit --audit-level=high` | Zero high/critical known CVEs in frontend packages | **Configured** |
| **Unit & Workflow Tests** | `pytest tests/ -v --cov=app` | 100% test pass rate across authentication, RBAC, workflows, and concurrency | **Configured** |
| **Next.js Production Build** | `npm run build` | Clean compilation of all static and server pages without build errors | **Configured** |
| **Container Build (Backend)** | `docker build -t alumniconnect-backend ./backend` | Multi-stage image builds successfully; non-root user verification | **Configured** |
| **Container Build (Frontend)** | `docker build -t alumniconnect-frontend ./frontend` | Standalone optimized Next.js container builds successfully | **Configured** |

---

## 2. Pre-Release Deployment Staging Verification

Prior to cutting a production release tag and promoting containers to production orchestration:

- [x] **Relational Schema Migrations Tested**:
  * `backend/app/db/schema.sql` creates all 25 normalized tables without syntax or constraint errors.
  * Views (`views.sql`), stored procedures (`procedures.sql`), and triggers (`triggers.sql`) compile on fresh MySQL 8.x.
- [x] **Deterministic Seeding Verified**:
  * `backend/scripts/seed_demo_data.py` completes idempotently across all 19 accounts, 27 slots, 12 sessions, and reviews.
- [x] **P0 Concurrency Row-Locking Enforced**:
  * `sp_create_booking` and `BookingService.create_booking` lock student profile, availability slot, and allocation.
  * Zero double bookings observed under simulated simultaneous requests.
- [x] **P0 Authorization & IDOR Elimination**:
  * Cross-tenant inspection on `GET /api/v1/sessions/{id}` blocked with HTTP 403 Forbidden.
  * Mentor inbox, request acceptance, and profile editing endpoints reject mismatched caller IDs.
- [x] **P1 2-Hour Advance Cancellation Guard**:
  * `sp_cancel_booking` rejects cancellations within 2 hours of session start time (`BR-T16`, `BR-T17`).
- [x] **CORS Headers on All Response Statuses**:
  * Global exception handlers guarantee `Access-Control-Allow-Origin` on 401, 403, 404, 422, and 500 error responses.
- [x] **Container Security & Credentials**:
  * Dockerfiles execute as non-root users (`appuser` with UID 1000 / `nextjs` with UID 1001).
  * `docker-compose.yml` utilizes non-root database credentials and environment variable overrides.
- [x] **Live Health Monitoring Endpoint**:
  * `GET /health` and `GET /api/v1/health` actively verify MySQL (`SELECT 1`), Redis ping, and Neo4j connectivity.
- [x] **Frontend Discovery Onboarding Flow**:
  * Mentor discovery setup banner is automatically suppressed if the student has any skills configured in the DB.
  * Target Career Goal dropdown maps directly to platform domain catalogues.

---

## 3. Production Rollout & Release Execution Commands

### Local Testing & Development Stack
```bash
# Bring up entire stack with live reload
docker-compose up -d

# Check health of services
curl http://localhost:8000/health
```

### Staging Deployment Execution
```bash
# 1. Initialize Relational Schema on Managed MySQL
mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE < backend/app/db/schema.sql
mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE < backend/app/db/views.sql
mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE < backend/app/db/procedures.sql
mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE < backend/app/db/triggers.sql

# 2. Seed Initial Demo Accounts & Relational Catalogues
cd backend && python -m scripts.seed_demo_data

# 3. Execute End-to-End Test Suite Verification
python -m pytest tests/ -v
```

---

## 4. Rollback Strategy

In the event of an anomaly during production deployment:
1. **Application Rollback**: Revert container images to the previous stable release tag via Docker Compose or Kubernetes deployment manifest.
2. **Database Rollback**: Point the application to the pre-deployment transactional point-in-time snapshot. All schema changes maintain backward compatibility with previous minor versions.
3. **Cache Purge**: Execute `FLUSHDB` or targeted pattern deletion `redis-cli KEYS "ac:*" | xargs redis-cli DEL` to ensure stale caches are immediately cleared.
