# AlumniConnect — Alumni–Student Mentorship Platform
### Enterprise DBMS Mini-Project (Modular Monolith + Polyglot Persistence)

[![Backend Tests](https://img.shields.io/badge/Pytest-9%20Passed-emerald.svg)](backend/tests/)
[![Next.js Build](https://img.shields.io/badge/Next.js-14.2%20Compiled-blue.svg)](frontend/)
[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Monolith-purple.svg)](#architecture)
[![Database](https://img.shields.io/badge/Authoritative%20DB-MySQL%208.x%20InnoDB-orange.svg)](#database-implementation)

AlumniConnect is a full-stack, enterprise-grade alumni–student mentorship platform built strictly according to the 15 authoritative project specification blueprints. It features **polyglot persistence** where **MySQL 8.x / InnoDB** serves as the sole authoritative source of truth for ACID transactions, while **Redis** provides sub-millisecond caching/rate-limiting and **Neo4j** delivers relationship-based graph recommendation candidate generation.

---

## Table of Contents
1. [Architecture & Polyglot Persistence](#architecture--polyglot-persistence)
2. [Database Implementation](#database-implementation)
   - [25 Relational Tables](#25-relational-tables)
   - [Stored Procedures & Stored Functions](#stored-procedures--stored-functions)
   - [Triggers & Invariants](#triggers--invariants)
   - [Views & Query Catalogue Q01–Q32](#views--query-catalogue-q01q32)
3. [Recommendation Engine](#recommendation-engine)
4. [Asynchronous Background Processing](#asynchronous-background-processing)
5. [User Portals & UI Walkthrough](#user-portals--ui-walkthrough)
6. [Demo Accounts & Test Credentials](#demo-accounts--test-credentials)
7. [Getting Started & Local Setup](#getting-started--quick-start)
8. [Running Automated Tests](#running-automated-tests)
9. [Documentation Traceability](#documentation-traceability)

---

## Architecture & Polyglot Persistence

The platform strictly adheres to the **Modular Monolith + Polyglot Persistence** architecture specified in *AlumniConnect Application Architecture*:

```
                           +---------------------------+
                           |    Next.js 14 Frontend    |
                           | (React / TS / Tailwind)   |
                           +-------------+-------------+
                                         | REST / JWT
                                         v
                           +---------------------------+
                           |      FastAPI Backend      |
                           |     (Modular Monolith)    |
                           +--+--------+------------+--+
                              |        |            |
             ACID / Truth     |        | Cache/TTL  | Candidate Graph
                              v        v            v
                       +----------+ +-------+ +-----------+
                       | MySQL 8  | | Redis | |   Neo4j   |
                       | (InnoDB) | |   7   | | Community |
                       +----+-----+ +-------+ +-----------+
                            |
                     Outbox | Poll
                            v
                      +------------+
                      | Background |
                      | Worker     | ---> Notifications / Projections / Invalidation
                      +------------+
```

### Architectural Principles & Boundaries
1. **MySQL 8.x (InnoDB) is the Authoritative Truth:** All domain state, user accounts, allocations, bookings, sessions, reviews, and audit trails reside authoritatively in MySQL.
2. **Redis & Neo4j are Non-Authoritative Supporting Stores:**
   - **Redis:** Caches hot read paths (`ac:{env}:v1:...`), protects against brute-force attacks via token-bucket rate-limiting, and enforces booking idempotency.
   - **Neo4j:** Traverses graph relationships (`(Student)-[:INTERESTED_IN]->(Domain)<-[:SPECIALIZES_IN]-(Mentor)`) for recommendation candidate generation.
   - *Resilience Guarantee:* If Redis or Neo4j are offline, the backend gracefully falls back to in-memory fallback engines without service disruption.
3. **Strict Boundary:** The frontend never connects directly to MySQL, Redis, or Neo4j. All communication flows through the typed FastAPI application layer.

---

## Database Implementation

### 25 Relational Tables
Located in `backend/app/db/schema.sql`:
1. `role` — System RBAC definitions (`ADMINISTRATOR`, `MENTOR`, `STUDENT`).
2. `department` — Academic departments.
3. `company` — Corporate organizations and employer affiliations.
4. `skill` — Normalized technical and soft skills catalogue.
5. `mentorship_domain` — Mentorship specializations and industry domains.
6. `user_account` — Core authentication identities, bcrypt password hashes, and statuses.
7. `student_profile` — 1-to-1 extension with roll numbers, academic batch, and career goals.
8. `mentor_profile` — 1-to-1 extension with job title, years experience, and mentee quotas.
9. `student_skill` — Student self-declared skills and proficiency rubrics.
10. `mentor_skill` — Mentor verified skills and endorsement metrics.
11. `student_domain_interest` — Student targeted learning interest tracks.
12. `mentor_domain_expertise` — Mentor primary and secondary specializations.
13. `mentorship_request` — Student-initiated mentorship proposals (`PENDING`, `ACCEPTED`, `REJECTED`).
14. `recommendation_run` — Audited recommendation executions.
15. `recommended_mentor` — Persisted scoring factors and rank positions.
16. `mentor_allocation` — Active 1-on-1 pairings resulting from accepted requests.
17. `mentor_availability` — Published booking time slots (`OPEN`, `BOOKED`, `BLOCKED`, `EXPIRED`).
18. `booking` — Reserved appointments with idempotency keys and cancellation histories.
19. `mentorship_session` — Offline mentorship meetings and mock interviews (`SCHEDULED`, `COMPLETED`, `NO_SHOW`).
20. `session_skill_assessment` — Mentor-recorded skill evaluations (`PROFICIENT`, `DEVELOPING`, `NEEDS_IMPROVEMENT`).
21. `session_feedback` — Two-way qualitative ratings and feedback.
22. `mentor_review` — Student 1–5 star reviews and published ratings.
23. `notification_outbox` — Transactional outbox event store for asynchronous fan-out.
24. `notification` — User in-app notifications and read statuses.
25. `audit_log` — Immutable security and administrative audit trail.

### Stored Procedures & Stored Functions
Located in `backend/app/db/procedures.sql` and `backend/app/db/functions.sql`:
- **SP01 (`sp_accept_mentorship_request`)**: Atomically validates mentor active capacity, verifies state is `PENDING`, transitions request to `ACCEPTED`, creates an active `mentor_allocation`, writes to `audit_log`, and queues an outbox notification.
- **SP02 (`sp_create_booking`)**: Locks the availability slot with `SELECT ... FOR UPDATE`, validates that slot is `OPEN`, verifies an active allocation exists, sets slot to `BOOKED`, creates a `CONFIRMED` booking record, provisions a `SCHEDULED` mentorship session, and writes an outbox event.
- **SP03 (`sp_cancel_booking`)**: Enforces the 2-hour minimum cancellation cutoff window, transitions booking to `CANCELLED`, releases the availability slot back to `OPEN`, records the cancellation reason, and writes audit records.
- **SP04 (`sp_record_session_outcome`)**: Mentor records offline session completion (`COMPLETED` or `NO_SHOW`), writes discussion summary, observations, next steps, and inserts multi-skill evaluation rubrics.
- **SP05 (`sp_submit_mentor_review`)**: Student submits a 1–5 star review for a completed session, validates student eligibility, updates mentor ratings, and writes audit records.
- **F01 (`fn_rating_label`)**: Deterministic scalar function translating numeric ratings into human-readable qualitative badges (`EXCELLENT`, `VERY_GOOD`, `GOOD`, `AVERAGE`, `POOR`).

### Triggers & Invariants
Located in `backend/app/db/triggers.sql`:
- **TR01 (`trg_request_status_audit`)**: Automatically logs any request status change to `audit_log`.
- **TR02 (`trg_request_status_guard`)**: Aborts invalid request state transitions (e.g., attempting to accept an already `REJECTED` request).
- **TR03 (`trg_session_status_guard`)**: Guards session lifecycles, ensuring finalized sessions cannot be illegally altered.
- **TR04 (`trg_mentor_review_validate`)**: Verifies that a review can only be submitted for an eligible, completed session.

### Views & Query Catalogue Q01–Q32
Located in `backend/app/db/views.sql` and `backend/app/repositories/analytics_repository.py`:
- **V01 (`v_public_mentor_directory`)**: Public mentor catalog with sanitized emails and ratings.
- **V02 (`v_mentor_rating_summary`)**: Aggregated review metrics and bayesian average ratings.
- **V03 (`v_student_mentorship_summary`)**: Student historical request and allocation summaries.
- **V04 (`v_mentor_session_outcomes`)**: Mentor completed sessions and no-show rates.
- **Q01–Q32 SQL Catalogue**:
  - `Q15`: Mentor pending requests inbox.
  - `Q16`: Student request history.
  - `Q22`: Top-rated mentors with minimum review count threshold.
  - `Q26`: Booking cancellation and no-show rate analytics.
  - `Q27`: Mentor capacity utilization and quota saturation report.
  - `Q28`: Skill demand versus alumni mentor supply ratio.
  - **`Q29`**: Multi-stage Request-to-Review Conversion Funnel implemented via SQL Common Table Expressions (CTEs).
  - `Q30`: Comprehensive security and system audit log.

---

## Recommendation Engine

The recommendation pipeline implements the exact 5-factor scoring model specified in *AlumniConnect Recommendation Design*:

$$\text{Final Score} = 0.30 \cdot S_{\text{skill}} + 0.20 \cdot S_{\text{domain}} + 0.15 \cdot S_{\text{exp}} + 0.20 \cdot S_{\text{career}} + 0.15 \cdot S_{\text{quality}}$$

1. **Candidate Generation (Neo4j):** Traverses graph relationships to identify alumni mentors who share technical skills, specializations, or alumni department affiliations with the student.
2. **Skills Match ($S_{\text{skill}}$, 30%):** Jaccard overlap between student declared skills and mentor verified skills.
3. **Domain Affinity ($S_{\text{domain}}$, 20%):** Alignment between student interest tracks and mentor primary/secondary expertise.
4. **Experience ($S_{\text{exp}}$, 15%):** Non-linear normalization of mentor industry experience ($5+\text{ years} = 100\%$).
5. **Career Goal Match ($S_{\text{career}}$, 20%):** Text and token overlap between student career goal statement and mentor job title / summary.
6. **Bayesian Quality ($S_{\text{quality}}$, 15%):** Bayesian smoothed rating ($C=3.0, m=4.0$) weighted by review volume.
7. **Authoritative Gate (MySQL):** Any mentor who is not actively accepting requests or has reached their `max_active_mentees` quota is strictly excluded.

---

## Asynchronous Background Processing

The `backend/app/workers/outbox_worker.py` daemon processes pending events from `notification_outbox`:
- **Guaranteed At-Least-Once Delivery:** Events are committed within the same relational ACID transaction as the business operation.
- **Notification Fan-out:** Delivers in-app notifications to user inboxes for request decisions, session bookings, and reminders.
- **Graph Projection Synchronization:** Updates Neo4j node attributes and relationships asynchronously.
- **Cache Invalidation:** Invalidates affected Redis keys (`ac:v1:student:...`, `ac:v1:mentor:...`) upon state changes.

---

## User Portals & UI Walkthrough

The frontend is a responsive Next.js 14 web application written in TypeScript and styled with Tailwind CSS:

1. **Student Mentee Portal (`/student`):**
   - **Dashboard (`/student/dashboard`):** Key metrics, top match score, quick links to browse mentors.
   - **Discover Mentors (`/student/mentors`):** Graph-backed recommendations, 5-factor scoring explanation breakdown, interactive mentorship proposal modal.
   - **My Requests (`/student/requests`):** Track proposal lifecycle states (`PENDING`, `ACCEPTED`, `REJECTED`), view mentor decision notes.
   - **Sessions & Bookings (`/student/sessions`):** Book open time slots published by assigned mentors, view upcoming scheduled sessions, review mentor evaluation outcomes, submit 1–5 star reviews (SP05).
   - **Profile & Skills (`/student/profile`):** Edit bio, expected graduation year, career goal statements, view verified skills and domain tags.

2. **Alumni Mentor Portal (`/mentor`):**
   - **Dashboard (`/mentor/dashboard`):** Active mentee quota saturation tracker, session counts, average platform rating.
   - **Request Inbox (`/mentor/requests`):** Review incoming student proposals, examine student career goals, Accept (SP01) or Decline with explanation.
   - **Availability Calendar (`/mentor/availability`):** Publish open booking time slots, view booked vs open slots.
   - **Session Evaluations (`/mentor/sessions`):** Record offline session outcomes (`COMPLETED`, `NO_SHOW`), discussion summaries, action items, and multi-skill evaluation rubrics (SP04).
   - **Mentor Profile (`/mentor/profile`):** Update job title, years of experience, professional summary, and adjust `max_active_mentees` intake limits.

3. **Administrator Portal (`/admin`):**
   - **Overview Analytics (`/admin/dashboard`):** Platform KPIs, skill demand vs mentor supply ratio table (Q28).
   - **Conversion Funnel (`/admin/funnel`):** Multi-step visual conversion funnel tracking drop-offs across Request → Allocation → Booking → Session → Review (Q29).
   - **Capacity Saturation (`/admin/capacity`):** Live mentor utilization monitor flagging saturated mentors (Q27).
   - **Audit Trail (`/admin/audit`):** Immutable log of critical business events, state transitions, and security operations (Q30).

---

## Demo Accounts & Test Credentials

All demo accounts are pre-seeded in the database with password `Password123!`:

| Role | Name | Email | Default Dashboard |
|---|---|---|---|
| **Student** | Aarav Sharma | `aarav.sharma@alumniconnect.edu` | `/student/dashboard` |
| **Student** | Priya Patel | `priya.patel@alumniconnect.edu` | `/student/dashboard` |
| **Mentor** | Rohit Verma (Staff ML Engineer) | `rohit.verma@alumniconnect.edu` | `/mentor/dashboard` |
| **Mentor** | Sneha Rao (Engineering Manager) | `sneha.rao@alumniconnect.edu` | `/mentor/dashboard` |
| **Mentor** | Vikram Joshi (VP of Engineering) | `vikram.joshi@alumniconnect.edu` | `/mentor/dashboard` |
| **Admin** | System Administrator | `admin@alumniconnect.edu` | `/admin/dashboard` |

---

## Getting Started & Quick Start

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- (Optional for full containerization) Docker & Docker Compose

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Initialize database schema, stored objects, and seed data
python3 -c "from app.db.init_db import init_db; init_db()"

# Start FastAPI backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI interactive Swagger documentation is available at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```
The Next.js web application is available at: `http://localhost:3000`

---

## Running Automated Tests

The automated test suite verifies database constraints, lifecycle state machines, concurrency guards, RBAC security, and the complete 10-step end-to-end user scenario:

```bash
cd backend

# Run the complete test suite
python3 -m pytest tests/ -v -s
```

### Verified Test Suites:
- `tests/test_e2e_lifecycle.py`: Executes the full 10-step integration journey:
  1. Student Login (Aarav Sharma)
  2. Graph Recommendation Discovery (5-factor multi-attribute ranking)
  3. Mentorship Request Submission (`PENDING`)
  4. Mentor Login & Acceptance via Stored Procedure SP01 (`ACTIVE` allocation)
  5. Mentor Availability Slot Publishing (WF-05)
  6. Atomic Slot Reservation via Stored Procedure SP02 (`CONFIRMED` booking)
  7. Concurrent Double-Booking Race Condition Guard Verification (TX-01 rejection)
  8. Mentor Outcome & Skill Rubric Recording via Stored Procedure SP04 (`COMPLETED`)
  9. Student Review & 1–5 Star Rating Submission via Stored Procedure SP05
  10. Background Outbox Worker Notification Fan-out & Admin Funnel Analytics (Q29)
- `tests/test_dbi_schema.py`: Primary keys, foreign key cascades, candidate key uniqueness (DBI-01..DBI-05).
- `tests/test_workflows.py`: State machine transitions, valid decision paths, invalid transition rejection.
- `tests/test_concurrency.py`: Idempotency key deduplication and slot race protection.
- `tests/test_security.py`: Role-Based Access Control (RBAC) boundaries.

---

## Documentation Traceability

All authoritative references and tracking records are maintained at:
- `Docs/reference/`: Contains all 15 authoritative project specification PDFs.
- `Docs/implementation/REQUIREMENTS_TRACEABILITY.md`: Detailed mapping of requirements to code and tests.
- `Docs/implementation/IMPLEMENTATION_LOG.md`: Detailed engineering log of all implementation steps.
- `Docs/implementation/IMPLEMENTATION_PLAN.md`: Strategic 11-phase development roadmap.
- `Docs/implementation/OPEN_DECISIONS.md`: Architectural reconciliation records and design decisions.
