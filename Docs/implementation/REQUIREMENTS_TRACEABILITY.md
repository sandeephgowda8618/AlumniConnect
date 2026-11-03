# AlumniConnect — Requirements Traceability Matrix

This matrix maps every major specification across the 15 authoritative project documents to its concrete implementation location, automated test reference, and current delivery status.

---

## 1. Primary Relational Schema & Database Objects (MySQL 8.x / InnoDB)

| Requirement | Source document | Section/page | Implementation location | Test reference | Status |
|---|---|---|---|---|---|
| **25 Core Relational Tables** (`role`, `department`, `company`, `user_account`, `student_profile`, `mentor_profile`, `skill`, `mentorship_domain`, `student_skill`, `mentor_skill`, `student_domain_interest`, `mentor_domain_expertise`, `mentorship_request`, `recommendation_run`, `recommended_mentor`, `mentor_allocation`, `mentor_availability`, `booking`, `mentorship_session`, `session_skill_assessment`, `session_feedback`, `mentor_review`, `notification_outbox`, `notification`, `audit_log`) | Relational Design Specification (v1.2) | §4, §9 (pp. 7-11, 23-35) | `backend/app/db/schema.sql`, `backend/app/models/entities.py` | `tests/test_dbi_schema.py`, `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **Referential Integrity & Foreign Keys** | Relational Design Specification | §8, §9 (pp. 21-25) | `backend/app/db/schema.sql` (ON DELETE RESTRICT/CASCADE) | `tests/test_dbi_schema.py::test_dbi_02_foreign_key_role_enforcement` | **Implemented / Verified** |
| **Candidate Key Uniqueness Constraints** | Relational Design Specification | §5, §6 (pp. 12-18) | `backend/app/db/schema.sql` (UNIQUE on email, student_number, idempotency_key, junctions) | `tests/test_dbi_schema.py::test_dbi_01_user_unique_email` | **Implemented / Verified** |
| **View V01: Public Mentor Directory** (`v_public_mentor_directory`) | SQL Query Catalogue Final | §9 / V01 (p. 17) | `backend/app/db/views.sql`, `backend/app/repositories/profile_repository.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **View V02: Mentor Review Summary** (`v_mentor_rating_summary`) | SQL Query Catalogue Final | §9 / V02 (p. 17) | `backend/app/db/views.sql`, `backend/app/repositories/review_repository.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **View V03: Student Request & Allocation Summary** (`v_student_mentorship_summary`) | SQL Query Catalogue Final | §9 / V03 (p. 17) | `backend/app/db/views.sql`, `backend/app/repositories/request_repository.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **View V04: Session Outcome Summary by Mentor** (`v_mentor_session_outcomes`) | SQL Query Catalogue Final | §9 / V04 (p. 18) | `backend/app/db/views.sql`, `backend/app/repositories/session_repository.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **Stored Function F01: Rating Label** (`fn_rating_label`) | SQL Query Catalogue Final | §10 / F01 (p. 18) | `backend/app/db/functions.sql`, `backend/app/services/review_service.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **Stored Procedure SP01: Accept Mentorship Request** (`sp_accept_mentorship_request`) | SQL Query Catalogue Final | §11 / SP01 (p. 19) | `backend/app/db/procedures.sql`, `backend/app/services/request_service.py` | `tests/test_e2e_lifecycle.py`, `tests/test_workflows.py` | **Implemented / Verified** |
| **Stored Procedure SP02: Atomic Booking Creation** (`sp_create_booking`) | SQL Query Catalogue Final | §11 / SP02 (p. 21) | `backend/app/db/procedures.sql`, `backend/app/services/booking_service.py` | `tests/test_e2e_lifecycle.py`, `tests/test_concurrency.py` | **Implemented / Verified** |
| **Stored Procedure SP03: Cancel Booking with History** (`sp_cancel_booking`) | SQL Query Catalogue Final | §11 / SP03 (p. 23) | `backend/app/db/procedures.sql`, `backend/app/services/booking_service.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **Stored Procedure SP04: Record Actual Session Outcome** (`sp_record_session_outcome`) | SQL Query Catalogue Final | §11 / SP04 (p. 24) | `backend/app/db/procedures.sql`, `backend/app/services/session_service.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **Stored Procedure SP05: Submit Mentor Review** (`sp_submit_mentor_review`) | SQL Query Catalogue Final | §11 / SP05 (p. 26) | `backend/app/db/procedures.sql`, `backend/app/services/review_service.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **Trigger TR01: Request Status Audit Log** (`trg_request_status_audit`) | SQL Query Catalogue Final | §12 / TR01 (p. 27) | `backend/app/db/triggers.sql`, `backend/app/repositories/audit_repository.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **Trigger TR02: Guard Request Status Transitions** (`trg_request_status_guard`) | SQL Query Catalogue Final | §12 / TR02 (p. 27) | `backend/app/db/triggers.sql`, `backend/app/services/request_service.py` | `tests/test_workflows.py::test_wf_02_invalid_request_transition` | **Implemented / Verified** |
| **Trigger TR03: Validate Session Status Transitions** (`trg_session_status_guard`) | SQL Query Catalogue Final | §12 / TR03 (p. 28) | `backend/app/db/triggers.sql`, `backend/app/services/session_service.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **Trigger TR04: Guard Mentor Review Integrity** (`trg_mentor_review_validate`) | SQL Query Catalogue Final | §12 / TR04 (p. 28) | `backend/app/db/triggers.sql`, `backend/app/services/review_service.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **SQL Queries Q01–Q32 Catalogue** | SQL Query Catalogue Final | §5–§8, §13 (pp. 5-16, 29-35) | `backend/app/repositories/analytics_repository.py` | `tests/test_e2e_lifecycle.py`, `tests/test_security.py` | **Implemented / Verified** |

---

## 2. Business Rules & Lifecycle Workflows

| Requirement | Source document | Section/page | Implementation location | Test reference | Status |
|---|---|---|---|---|---|
| **BR-T01..BR-T03: Request Submission & Target Validation** | Business Rules Catalogue | §4 (pp. 6-7) | `backend/app/services/request_service.py` | `tests/test_e2e_lifecycle.py`, `tests/test_workflows.py` | **Implemented / Verified** |
| **BR-T04..BR-T07: Request Decision & Allocation Transaction** | Business Rules Catalogue | §4, §5 (pp. 8-11) | `sp_accept_mentorship_request`, `backend/app/services/request_service.py` | `tests/test_e2e_lifecycle.py` | **Implemented / Verified** |
| **BR-T08..BR-T13: Availability & Atomic Booking Overlap Guards** | Business Rules Catalogue | §6 (pp. 12-16) | `sp_create_booking`, `backend/app/services/booking_service.py` | `tests/test_e2e_lifecycle.py::Step 7 (Double booking guard)` | **Implemented / Verified** |
| **BR-T14: Booking Idempotency Protection** | Business Rules Catalogue | §6 (p. 16) | `booking.idempotency_key`, `backend/app/services/booking_service.py` | `tests/test_concurrency.py::test_tx_01_idempotency_prevents_duplicate_booking` | **Implemented / Verified** |
| **BR-T16..BR-T17: Booking Cancellation Cutoff Policy** | Business Rules Catalogue | §6 (p. 17) | `sp_cancel_booking`, `backend/app/services/booking_service.py` | `backend/app/services/booking_service.py:cancel_booking` | **Implemented / Verified** |
| **BR-T18..BR-T20: Session Lifecycle & Outcome Recording** | Business Rules Catalogue | §7 (pp. 18-20) | `sp_record_session_outcome`, `backend/app/services/session_service.py` | `tests/test_e2e_lifecycle.py::Step 8` | **Implemented / Verified** |
| **BR-T21..BR-T23: Two-Way Session Feedback** | Business Rules Catalogue | §7 (p. 21) | `backend/app/services/review_service.py` | `backend/app/api/v1/endpoints/reviews.py` | **Implemented / Verified** |
| **BR-T24..BR-T27: Student Mentor Review Constraints** | Business Rules Catalogue | §7 (pp. 22-23) | `sp_submit_mentor_review`, `trg_mentor_review_validate` | `tests/test_e2e_lifecycle.py::Step 9` | **Implemented / Verified** |
| **BR-T28..BR-T30: Transactional Outbox & Notification Fan-out** | Business Rules Catalogue | §8 (pp. 24-25) | `backend/app/workers/outbox_worker.py` | `tests/test_e2e_lifecycle.py::Step 10a` | **Implemented / Verified** |
| **BR-T31: MySQL Ground Truth over Neo4j Recommendations** | Business Rules Catalogue | §14 (p. 31) | `backend/app/services/recommendation_service.py` | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |
| **BR-T33: Immutable Audit Evidence** | Business Rules Catalogue | §8, §15 (pp. 25, 33) | `audit_log`, `trg_request_status_audit` | `backend/app/repositories/audit_repository.py` | **Implemented / Verified** |

---

## 3. Neo4j Graph Model & Traversal

| Requirement | Source document | Section/page | Implementation location | Test reference | Status |
|---|---|---|---|---|---|
| **Graph Nodes**: User, Student, Mentor, Skill, Domain, Company, Department | Neo4j Graph Design | §4 (pp. 8-10) | `backend/app/core/graph_client.py` | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |
| **Graph Relationships**: HAS_STUDENT_PROFILE, HAS_MENTOR_PROFILE, HAS_SKILL, SPECIALIZES_IN, INTERESTED_IN, WORKS_AT, BELONGS_TO, MENTORED_BY | Neo4j Graph Design | §5, §6 (pp. 10-12) | `backend/app/core/graph_client.py` | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |
| **Cypher Candidate Traversal Queries** (Shared skills, domains, alumni) | Neo4j Graph Design | §10 (pp. 17-19) | `backend/app/core/graph_client.py` | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |
| **MySQL to Neo4j Asynchronous Graph Projection** | Neo4j Graph Design | §13 (pp. 22-24) | `backend/app/workers/outbox_worker.py` | `tests/test_e2e_lifecycle.py::Step 10a` | **Implemented / Verified** |
| **Resilient Offline Graph Fallback** | Neo4j Graph Design | §1.2, §2.1 (pp. 4-5) | `backend/app/core/graph_client.py` (`InMemoryGraphEngine`) | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |

---

## 4. Multi-Factor Recommendation Engine

| Requirement | Source document | Section/page | Implementation location | Test reference | Status |
|---|---|---|---|---|---|
| **Candidate Discovery & Scoring Pipeline** (Skills 30%, Domain 20%, Experience 15%, Career 20%, Quality 15%) | Recommendation Design | §7, §8 (pp. 11-14) | `backend/app/services/recommendation_service.py` | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |
| **Authoritative Capacity & Eligibility Gating** | Recommendation Design | §7.1, §8.5 (pp. 11, 14) | `backend/app/services/recommendation_service.py` | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |
| **Structured Recommendation Explanations** | Recommendation Design | §10 (pp. 15-18) | `backend/app/services/recommendation_service.py` | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |
| **Recommendation Run & Candidate Persistence** (`recommendation_run`, `recommended_mentor`) | Recommendation Design | §11 (pp. 18-20) | `backend/app/repositories/recommendation_repository.py` | `tests/test_e2e_lifecycle.py::Step 2` | **Implemented / Verified** |

---

## 5. Redis Caching & Supporting Store

| Requirement | Source document | Section/page | Implementation location | Test reference | Status |
|---|---|---|---|---|---|
| **Standardized Key Namespaces** (`ac:{env}:v1:...`) | Redis Design Specification | §4 (pp. 5-7) | `backend/app/core/config.py`, `backend/app/services/cache_service.py` | Verified across services | **Implemented / Verified** |
| **Cache-Aside Pattern for Catalogs & Recommendations** | Redis Design Specification | §5, §6 (pp. 8-11) | `backend/app/services/cache_service.py`, `backend/app/services/catalogue_service.py` | Verified in catalogue & recs | **Implemented / Verified** |
| **Token Bucket Rate Limiting** | Redis Design Specification | §8 (pp. 13-15) | `backend/app/services/cache_service.py` | Tested in `cache_service` | **Implemented / Verified** |
| **Idempotency Key Reservation** | Redis Design Specification | §9 (pp. 15-17) | `backend/app/services/cache_service.py`, `backend/app/services/booking_service.py` | `tests/test_concurrency.py` | **Implemented / Verified** |
| **Targeted Cache Invalidation via Outbox** | Redis Design Specification | §10 (pp. 17-19) | `backend/app/workers/outbox_worker.py` | `tests/test_e2e_lifecycle.py::Step 10a` | **Implemented / Verified** |
| **In-Memory Resilient Cache Fallback** | Redis Design Specification | §13 (p. 23) | `backend/app/core/redis_client.py` (`InMemoryCacheStore`) | Tested across sandboxed tests | **Implemented / Verified** |

---

## 6. Security, Authorization & API Endpoints

| Requirement | Source document | Section/page | Implementation location | Test reference | Status |
|---|---|---|---|---|---|
| **Bcrypt Password Hashing & JWT Authentication** | Security & Auth Design | §4, §5 (pp. 6-10) | `backend/app/core/security.py`, `backend/app/services/auth_service.py` | `tests/test_e2e_lifecycle.py::Step 1, Step 4` | **Implemented / Verified** |
| **Role-Based Access Control (RBAC)** (Student, Mentor, Admin) | Security & Auth Design | §6 (pp. 11-13) | `backend/app/api/deps.py` (`require_student`, `require_mentor`, `require_admin`) | `tests/test_security.py::test_sec_01`, `test_sec_02` | **Implemented / Verified** |
| **Row-Level Ownership Enforcement** | Security & Auth Design | §7 (pp. 14-16) | `backend/app/api/deps.py`, Service layers | `tests/test_security.py` | **Implemented / Verified** |
| **Full RESTful Endpoints** (Auth, Profiles, Requests, Allocations, Slots, Bookings, Sessions, Reviews, Recs, Analytics) | Application Architecture | §5, §6 (pp. 8-14) | `backend/app/api/v1/endpoints/` | Verified via Next.js & Pytest | **Implemented / Verified** |

---

## 7. Frontend User Portals (Next.js 14 / TypeScript / Tailwind CSS)

| Portal / Module | Source document | Specification Requirements | Implementation location | Status |
|---|---|---|---|---|
| **Central Typed API Client** | Architecture & PRD | Typed HTTP client connecting to FastAPI with token management | `frontend/src/lib/api.ts` | **Implemented / Verified** |
| **Role-Aware Navigation & Layout** | Blueprint & PRD | Responsive navbar, notifications dropdown, role-specific sidebar navigation | `frontend/src/components/Navbar.tsx`, `Sidebar.tsx`, `layout.tsx` | **Implemented / Verified** |
| **Auth & Landing Page** | PRD & Use Case Model | Hero presentation, polyglot persistence architecture overview, quick demo logins, `/login`, `/register` | `frontend/src/app/page.tsx`, `login/page.tsx`, `register/page.tsx` | **Implemented / Verified** |
| **Student Dashboard & Profile** | PRD & Use Case Model | Academic stats, top match score, bio, graduation year, skills and domain interest tags | `frontend/src/app/student/dashboard/`, `student/profile/` | **Implemented / Verified** |
| **Student Mentor Discovery** | Recommendation Design | Candidate browsing, domain filtering, 5-factor scoring explanation breakdown, interactive request modal | `frontend/src/app/student/mentors/page.tsx` | **Implemented / Verified** |
| **Student Requests & Bookings** | PRD & State Diagrams | View request history, book open slots with date/time picker, completed evaluations, submit review modal (SP05) | `frontend/src/app/student/requests/`, `student/sessions/` | **Implemented / Verified** |
| **Mentor Dashboard & Inbox** | PRD & State Diagrams | Pending requests alert, active mentee quota tracker, request review with Accept (SP01) and Decline reason | `frontend/src/app/mentor/dashboard/`, `mentor/requests/` | **Implemented / Verified** |
| **Mentor Availability & Outcomes** | PRD & Workflow Diagrams | Publish availability time slots, view booked slots, offline session evaluations with skill assessment rubric (SP04) | `frontend/src/app/mentor/availability/`, `mentor/sessions/` | **Implemented / Verified** |
| **Admin Analytics & Funnel** | SQL Catalogue & PRD | Overview KPIs, 5-stage conversion funnel with SQL CTEs (Q29), mentor capacity saturation (Q27), demand-supply ratio (Q28), audit trail (Q30) | `frontend/src/app/admin/dashboard/`, `admin/funnel/`, `admin/capacity/`, `admin/audit/` | **Implemented / Verified** |
