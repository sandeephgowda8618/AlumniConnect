# AlumniConnect — Requirements Gap Matrix

**Date**: 2026-11-03  
**Auditor**: Full-Stack Architecture & QA Engineering Team  
**Reference Documents**: PRD, Use-Case Model, Business Rules Catalogue, Relational Design Specification, Workflow & State Diagrams

---

## 1. Traceability & Implementation Status Matrix

| Req ID | Requirement Description | Blueprint Reference | Implementation File | Status | Gap Analysis & Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-AUTH-01** | Student Mentee Registration & Password Hashing | PRD §2.1, Security §4 | `backend/app/services/auth_service.py` | `IMPL_AND_VERIFIED` | Password hashed with PBKDF2/Bcrypt; transactional commit added to prevent rollback; career domain interest automatically linked in DB. |
| **REQ-AUTH-02** | Alumni Mentor Registration & Profile Initialization | PRD §2.1, Relational §2 | `backend/app/services/auth_service.py` | `IMPL_AND_VERIFIED` | Full mentor profile with job title, years of experience, and capacity limits persisted and committed to MySQL. |
| **REQ-AUTH-03** | Email Verification on Registration | PRD §2.1 | `backend/app/services/auth_service.py` | `DEFERRED_V2` | Campus institutional emails are validated via regex; SMTP dispatch deferred to external notification provider. |
| **REQ-AUTH-04** | Role-Based Access Control (RBAC) & Route Guards | Security §6, App Arch §4 | `backend/app/api/deps.py` | `IMPL_AND_VERIFIED` | FastAPI dependency injection enforces `require_student`, `require_mentor`, and `require_admin`. |
| **REQ-PROF-01** | Student Profile & Skill Management | PRD §2.2, Relational §3 | `backend/app/services/profile_service.py` | `IMPL_AND_VERIFIED` | Full interactive skill and domain management UI implemented; atomic SQL sync via `PUT /students/skills-and-domains`. |
| **REQ-PROF-02** | Target Career Goal Catalogue Alignment | BR-P04, Relational §3 | `frontend/src/app/register/page.tsx`, `student/profile/page.tsx` | `IMPL_AND_VERIFIED` | Replaced free-text inputs with dropdowns dynamically populated from `mentorship_domain` catalogue. |
| **REQ-REC-01** | Neo4j Graph-Based Candidate Traversal | Graph Design §8–10 | `backend/app/core/graph_client.py` | `IMPL_AND_VERIFIED` | Traverses `(:Student)-[:HAS_SKILL]->(:Skill)<-[:HAS_SKILL]-(:Mentor)` and domain interests. In-memory fallback available. |
| **REQ-REC-02** | Authoritative MySQL Capacity & Eligibility Hard-Gating | Rec Design §6 | `backend/app/services/recommendation_service.py` | `IMPL_AND_VERIFIED` | Mentors exceeding `max_active_mentees` or inactive accounts are filtered out before scoring. |
| **REQ-REC-03** | 5-Factor Weighted Scoring & Explanations | Rec Design §7–9 | `backend/app/services/recommendation_service.py` | `IMPL_AND_VERIFIED` | Implements Skills (30%), Domains (20%), Experience (15%), Career (20%), and Bayesian Quality (15%). |
| **REQ-REC-04** | Redis Sub-Millisecond Caching & Targeted Invalidation | Redis Design §4, §9 | `backend/app/services/cache_service.py` | `IMPL_AND_VERIFIED` | Cached under `ac:dev:v1:rec:student:{id}:*` with 300s TTL; invalidated whenever student skills/domains are updated. |
| **REQ-REC-05** | Onboarding Setup Banner Suppression on Configured Skills | User Spec | `frontend/src/app/student/mentors/page.tsx` | `IMPL_AND_VERIFIED` | Corrected condition: setup banner is suppressed if student has any technical skills configured in the DB. |
| **REQ-REQ-01** | Mentorship Request Submission & Pending Uniqueness | BR-T01, BR-T02 | `backend/app/services/request_service.py` | `IMPL_AND_VERIFIED` | Enforces one active pending request per student-mentor-domain tuple; idempotency key guard supported. |
| **REQ-REQ-02** | Atomic Request Acceptance Transaction (SP01) | SQL Catalogue SP01, Workflow WF-03 | `backend/app/db/procedures.sql`, `request_service.py` | `IMPL_AND_VERIFIED` | Row-level `SELECT ... FOR UPDATE` on request row; inserts allocation before updating request status to `ACCEPTED`. |
| **REQ-REQ-03** | Request Rejection with Structured Reason | Workflow WF-04 | `backend/app/services/request_service.py` | `IMPL_AND_VERIFIED` | Verifies addressed mentor identity; updates status to `REJECTED`; records audit and outbox events. |
| **REQ-BOOK-01** | Availability Slot Publishing with Interval Guard | BR-T11, BR-T12 | `backend/app/services/availability_service.py` | `IMPL_AND_VERIFIED` | Guards against past slots and overlapping slot intervals for the same mentor via composite unique constraint. |
| **REQ-BOOK-02** | Atomic Booking Creation with Concurrency Protection (SP02) | SQL Catalogue SP02, BR-T13–15 | `backend/app/services/booking_service.py`, `procedures.sql` | `IMPL_AND_VERIFIED` | Pessimistic row locking on student profile, availability slot, and allocation; mutual exclusion on student schedule. |
| **REQ-BOOK-03** | Booking Cancellation with 2-Hour Cutoff (SP03) | BR-T16, BR-T17 | `backend/app/services/booking_service.py`, `procedures.sql` | `IMPL_AND_VERIFIED` | 2-hour cutoff enforced in Python and SQL; status transitioned to `CANCELLED`; future slot reopened; session cancelled. |
| **REQ-SESS-01** | Actual Session Outcome & Rubric Recording (SP04) | SQL Catalogue SP04, Workflow WF-07 | `backend/app/services/session_service.py` | `IMPL_AND_VERIFIED` | Supports `COMPLETED`, `CANCELLED`, `NO_SHOW`; updates discussion summary, observations, and rubric assessments. |
| **REQ-SESS-02** | IDOR Protection on Session Details API | Security §6 | `backend/app/api/v1/endpoints/sessions.py` | `IMPL_AND_VERIFIED` | Restricted to participating student, assigned mentor, or platform administrator. |
| **REQ-REV-01** | Student Mentor Review Submission (SP05) | SQL Catalogue SP05, Workflow WF-08 | `backend/app/services/review_service.py` | `IMPL_AND_VERIFIED` | Requires completed session; rating bounded between 1 and 5; unique review per session. |
| **REQ-ADM-01** | Analytical Overview, Funnel & Capacity Dashboards | SQL Catalogue Q27–Q29 | `backend/app/api/v1/endpoints/analytics.py` | `IMPL_AND_VERIFIED` | Platform overview, conversion funnel CTE, and mentor capacity utilization endpoints implemented. |
| **REQ-ADM-02** | Security & System Audit Log Viewer | SQL Catalogue Q30 | `backend/app/api/v1/endpoints/admin.py`, `frontend/.../admin/audit` | `IMPL_AND_VERIFIED` | Immutable audit log queried via `GET /admin/audit-logs`; rendered in frontend table with actor names and timestamps. |
| **REQ-INFRA-01** | Multi-Stage Containerization | Arch §8 | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` | `IMPL_AND_VERIFIED` | Non-root container execution; production compose stack with healthchecks across MySQL, Redis, and Neo4j. |
| **REQ-INFRA-02** | Automated CI/CD Pipeline | CI/CD Best Practices | `.github/workflows/ci.yml` | `IMPL_AND_VERIFIED` | GitHub Actions workflow automating linting, testing, security scans, and Docker container verification. |

---

## 2. Gap Resolution Summary

1. **P0 Concurrency Gaps**: Completely closed via row-level locks on student schedules and active availability checks.
2. **P0 IDOR Gaps**: Completely closed via participant authorization validation on session inspection.
3. **P1 Stored Procedure Gaps**: 2-hour cancellation window cutoff explicitly embedded in `sp_cancel_booking`.
4. **P1 CI/CD Gaps**: Fully automated GitHub Actions workflow established.
5. **Deferred Non-Critical Items**: SMTP institutional email verification (P2) scheduled for Staging Phase 2 release.
