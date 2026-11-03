# AlumniConnect — Implementation & Production Staging Roadmap

**Date**: 2026-11-03  
**Status**: Active Production Release Plan  
**Target Repository**: `https://github.com/sandeephgowda8618/AlumniConnect.git`

---

## 1. Roadmap Overview & Milestones

```
+-------------------------------------------------------------------------------------------------+
|                                    ALUMNICONNECT RELEASE PHASES                                 |
+-------------------------------------------------------------------------------------------------+
|  Phase 1: Critical P0/P1 Fixes   -->  Phase 2: CI/CD & Containers   -->  Phase 3: Staging & E2E  |
|  - Booking race condition locks       - GitHub Actions CI                - Staging DB Seeding   |
|  - IDOR session guards                - Multi-stage Dockerfiles          - Full regression run  |
|  - 2-hr cutoff in SP03                - Non-root Compose stack           - Load benchmarking    |
|  [COMPLETED]                          [COMPLETED]                        [CURRENT]              |
+-------------------------------------------------------------------------------------------------+
```

---

## 2. Chronological Phase Breakdown

### Phase 1: Critical P0/P1 Engineering Fixes (Completed)
* **Milestone 1.1**: Concurrency & Double-Booking Protection (`AC-001`)
  * Added pessimistic row locks on student profile, availability slot, and allocation.
  * Enforced mutual exclusion on overlapping intervals in `BookingService` and `sp_create_booking`.
* **Milestone 1.2**: Authorization & IDOR Elimination (`AC-002`)
  * Hardened `GET /api/v1/sessions/{session_id}` with participant/admin role checks.
  * Verified mentor request acceptance and rejection caller authorization.
* **Milestone 1.3**: Transaction Atomicity & SP Updates (`AC-003`, `AC-006`)
  * Enforced allocation-before-update in `sp_accept_mentorship_request`.
  * Embedded 2-hour advance cancellation window cutoff in `sp_cancel_booking`.
* **Milestone 1.4**: UI Discovery & Onboarding Alignment (`AC-009`, `AC-010`)
  * Target Career Goal dropdown mapped to canonical database tracks.
  * Suppressed setup banner for students with existing skills.

### Phase 2: DevOps, CI/CD & Container Hardening (Completed)
* **Milestone 2.1**: Automated Continuous Integration (`AC-005`)
  * Configured `.github/workflows/ci.yml` running linting, tests, coverage, security audits, and Next.js builds on every push/PR.
* **Milestone 2.2**: Container Image Optimization & Compose Orchestration (`AC-008`)
  * Created multi-stage `backend/Dockerfile` and `frontend/Dockerfile` running as non-root users (`appuser` / `nextjs`).
  * Configured `docker-compose.yml` with MySQL 8.x, Redis 7, Neo4j 5, Backend, Outbox Worker, and Next.js Frontend.
  * Embedded active health checks across all containerized services.
* **Milestone 2.3**: Health Monitoring Endpoint (`AC-006`)
  * Implemented `/health` and `/api/v1/health` with live checks on database connectivity (`SELECT 1`), Redis ping, and Neo4j connectivity.

### Phase 3: Staging Deployment & Acceptance Testing (In Progress)
* **Milestone 3.1**: Production Database Provisioning
  * Apply `backend/app/db/schema.sql`, `views.sql`, `procedures.sql`, and `triggers.sql` on managed MySQL 8.0 instance.
  * Execute deterministic seeder `backend/scripts/seed_demo_data.py`.
* **Milestone 3.2**: E2E Acceptance & Concurrency Stress Testing
  * Execute 42-scenario automated verification harness (`run_e2e_tests.py`).
  * Run parallel booking contention simulations to verify zero double-bookings.
* **Milestone 3.3**: Security Review & Secret Rotation
  * Verify `.env.example` template against staging environment variables.
  * Ensure no hardcoded credentials remain in source control.

### Phase 4: Production Launch & Observability (Upcoming)
* **Milestone 4.1**: Staging Sign-Off
  * Final stakeholder review across Student, Mentor, and Administrator portals.
* **Milestone 4.2**: Production Staged Rollout
  * DNS switchover and reverse proxy SSL termination (Nginx / Cloudflare).
  * Enable Prometheus / Grafana scraping of platform health metrics.
* **Milestone 4.3**: Post-Launch Monitoring
  * Monitor outbox worker event delivery latency.
  * Audit database lock contention and Redis cache hit ratios.

---

## 3. Work Package Ownership & Tracking

| Work Package | Owner | Target Date | Current Status |
| :--- | :--- | :--- | :--- |
| **WP-01: ACID Concurrency Row-Locking** | Principal Database Engineer | 2026-11-03 | **Done (Verified)** |
| **WP-02: Security & IDOR Hardening** | Security Auditor & Backend Eng | 2026-11-03 | **Done (Verified)** |
| **WP-03: Stored Procedure Guards** | Senior Database Engineer | 2026-11-03 | **Done (Verified)** |
| **WP-04: CI/CD Pipeline Implementation** | DevOps / SRE | 2026-11-03 | **Done (Verified)** |
| **WP-05: Docker Multi-Stage Builds** | DevOps / SRE | 2026-11-03 | **Done (Verified)** |
| **WP-06: Production Staging Verification** | Full-Stack QA Team | 2026-11-04 | **Active** |
| **WP-07: Production Cutover** | Lead Architect / Ops Team | 2026-11-06 | **Pending Staging Sign-Off** |

