# AlumniConnect — Master Implementation Plan

This implementation plan defines the complete, phased engineering roadmap for the **AlumniConnect** Alumni–Student Mentorship Platform, strictly adhering to the 15 authoritative project reference documents.

---

## Architecture Overview

- **Architecture Style**: Modular Monolith + Polyglot Persistence
- **Frontend**: Next.js (React, TypeScript, Tailwind CSS, Responsive Design System, Centralised API Client)
- **Backend**: Python 3.12+ / FastAPI (Modular Architecture, Repositories, Services, Unit of Work, Transaction Managers)
- **Primary Relational Store**: MySQL 8.x with InnoDB (Authoritative System of Record, ACID, Stored Procedures, Triggers, Views, Functions)
- **Supporting Graph Store**: Neo4j (Relationship-based discovery, candidate generation, graph traversal)
- **Supporting Cache Store**: Redis (Cache-aside, temporary rate-limiting, idempotency, short-lived availability preview)
- **Asynchronous Processing**: Transactional Outbox Pattern + Dedicated Background Worker

---

## Phase Breakdown

### Phase 1: Architecture, Environment & Authoritative Database Foundation
- [ ] Inspect environment and verify all 15 specification PDFs.
- [ ] Establish repository structure: `backend/` and `frontend/`.
- [ ] Configure environment settings (`.env.example`, Pydantic Settings).
- [ ] Author MySQL 8.x schema DDL with all 25 tables, primary keys, foreign keys, unique constraints, and check constraints according to Relational Design Specification Version 1.2:
  - `role`, `department`, `company`, `user_account`
  - `student_profile`, `mentor_profile`
  - `skill`, `mentorship_domain`, `student_skill`, `mentor_skill`
  - `student_domain_interest`, `mentor_domain_expertise`
  - `mentorship_request`, `recommendation_run`, `recommended_mentor`
  - `mentor_allocation`, `mentor_availability`, `booking`, `mentorship_session`
  - `session_skill_assessment`, `session_feedback`, `mentor_review`
  - `notification_outbox`, `notification`, `audit_log`
- [ ] Implement database migration runner and versioned DDL scripts.
- [ ] Implement database views (V01–V04):
  - `v_public_mentor_directory` (V01)
  - `v_mentor_rating_summary` (V02)
  - `v_student_mentorship_summary` (V03)
  - `v_mentor_session_outcomes` (V04)
- [ ] Implement stored functions (F01: `fn_rating_label`).
- [ ] Implement stored procedures (SP01–SP05):
  - `sp_accept_mentorship_request` (SP01)
  - `sp_create_booking` (SP02)
  - `sp_cancel_booking` (SP03)
  - `sp_record_session_outcome` (SP04)
  - `sp_submit_mentor_review` (SP05)
- [ ] Implement triggers (TR01–TR04):
  - `trg_request_status_audit` (TR01)
  - `trg_request_status_guard` (TR02)
  - `trg_session_status_guard` (TR03)
  - `trg_mentor_review_validate` (TR04)
- [ ] Implement seed data script for standard reference data (roles, departments, domains, skills, companies, demo users).

### Phase 2: Core Authentication, Authorization & Identity
- [ ] Implement secure password hashing using bcrypt.
- [ ] Implement JWT token authentication (access token, refresh token / session token).
- [ ] Implement user registration for Students and Alumni/Mentors with associated profiles.
- [ ] Implement login, logout, and token refresh endpoints.
- [ ] Implement RBAC dependencies and resource authorization guards (`get_current_user`, `require_role`, `verify_resource_ownership`).
- [ ] Implement account status checking (`account_status == 'ACTIVE'`).

### Phase 3: Reference Catalogues & Profile Management
- [ ] Implement Skills and Mentorship Domains repository and services.
- [ ] Implement Departments and Companies services.
- [ ] Implement Student Profile management:
  - Academic details, graduation year, bio, career goals.
  - Student skills management (add/remove skills with proficiency and experience).
  - Student domain interests management (with priority ordering).
- [ ] Implement Mentor Profile management:
  - Job title, company, years of experience, bio, max mentees, accepting requests flag.
  - Mentor skills management (with proficiency and experience).
  - Mentor domain expertise management (expertise level, primary domain flag).

### Phase 4: Neo4j Graph Model & Recommendation Engine
- [ ] Implement Neo4j graph driver with connection pooling and resilient offline fallback.
- [ ] Implement Neo4j schema constraints and indexes for nodes:
  - `:User(userId)`, `:Student(studentId)`, `:Mentor(mentorId)`, `:Skill(skillId)`, `:Domain(domainId)`, `:Company(companyId)`, `:Department(departmentId)`.
- [ ] Implement graph sync / projection logic to sync MySQL changes into Neo4j nodes and edges (`HAS_STUDENT_PROFILE`, `HAS_MENTOR_PROFILE`, `HAS_SKILL`, `SPECIALIZES_IN`, `INTERESTED_IN`, `WORKS_AT`, `BELONGS_TO`, `MENTORED_BY`).
- [ ] Implement Neo4j Cypher recommendation candidate queries (shared skills, domains, department alumni).
- [ ] Implement deterministic Multi-Dimensional Recommendation Scoring Pipeline:
  - Skill Similarity (`30%`)
  - Domain Relevance (`20%`)
  - Relevant Experience (`15%`)
  - Career Relevance (`20%`)
  - Mentor Quality (`15%`, Bayesian smoothed)
  - Hard Capacity Gate (filter out full or inactive mentors via MySQL)
- [ ] Implement structured recommendation explanations (human-readable match reasons and matched skill/domain tags).
- [ ] Persist recommendation runs and candidate snapshots into `recommendation_run` and `recommended_mentor`.

### Phase 5: Mentorship Request & Allocation Lifecycle
- [ ] Implement Student mentorship request submission endpoint.
- [ ] Enforce business rules: target mentor must be active, accepting requests, and not duplicate an existing pending request.
- [ ] Atomically write `mentorship_request` and `notification_outbox` event in one transaction.
- [ ] Implement Mentor pending request inbox with student profile details.
- [ ] Implement Mentor Accept Request endpoint invoking `sp_accept_mentorship_request` (SP01):
  - Row locking `FOR UPDATE`.
  - Atomically creates `mentor_allocation`, updates request to `ACCEPTED`, checks capacity, and inserts outbox event.
- [ ] Implement Mentor Reject Request endpoint (updates request to `REJECTED`, retains history, inserts outbox event).
- [ ] Implement Student Cancel Request endpoint (guards `PENDING` state).

### Phase 6: Availability & Atomic Booking System
- [ ] Implement Mentor Availability management:
  - Publish time slots (`starts_at`, `ends_at`).
  - Validate half-open interval, no overlapping open slots, future timestamps.
  - Withdraw unbooked slot (`OPEN` -> deleted or cancelled).
- [ ] Implement Student Slot Discovery (authoritative MySQL query + Redis short-lived preview).
- [ ] Implement Atomic Booking Creation invoking `sp_create_booking` (SP02):
  - Validates active mentor allocation.
  - Acquires row locks on availability, mentor, and student.
  - Validates slot is still `OPEN`.
  - Validates no participant schedule overlap.
  - Inserts `booking` (`CONFIRMED`).
  - Updates slot status to `BOOKED`.
  - Inserts planned `mentorship_session` (`SCHEDULED`).
  - Emits outbox notification event.
  - Commits atomically or rolls back on any violation.
- [ ] Implement Booking Cancellation invoking `sp_cancel_booking` (SP03):
  - Validates participant ownership and cancellation cutoff.
  - Marks booking `CANCELLED`, marks scheduled session `CANCELLED`, reopens future slot to `OPEN`.

### Phase 7: Sessions, Outcomes & Reviews
- [ ] Implement Mentor Session Management:
  - View upcoming and past appointments.
  - Record actual session outcome invoking `sp_record_session_outcome` (SP04):
    - Updates status to `COMPLETED`, `CANCELLED`, or `NO_SHOW`.
    - Records actual start/end timestamps, discussion summary, observations, next steps.
    - Records skill assessments in `session_skill_assessment`.
    - Inserts outbox notification event.
- [ ] Implement Two-Way Session Feedback in `session_feedback`:
  - Enforces completed session participation.
  - Ratings for communication, helpfulness, technical preparation, comments.
- [ ] Implement Student Mentor Review invoking `sp_submit_mentor_review` (SP05):
  - Enforces student participant role on completed session.
  - Enforces `UNIQUE(session_id, student_id)` and rating `1..5`.
  - Emits review outbox event to update mentor aggregate rating.

### Phase 8: Redis Caching, Outbox Worker & Notifications
- [ ] Implement Redis integration with strict fallback resilience when Redis is unavailable.
- [ ] Implement standard key namespaces (`ac:{env}:v1:...`) and TTL policies.
- [ ] Implement Cache-Aside for public mentor profiles, catalogues, and recommendation candidates.
- [ ] Implement targeted cache invalidation triggered on mentor profile/skill updates.
- [ ] Implement Background Outbox Worker:
  - Safely claims `PENDING` events from `notification_outbox`.
  - Fans out into `notification` rows for target recipients.
  - Projects updates into Neo4j graph.
  - Invalidates affected Redis cache keys.
  - Handles retries with exponential backoff and error logging.
- [ ] Implement in-app Notifications API (list, count unread, mark read).

### Phase 9: Administration & SQL Query Catalogue
- [ ] Implement Administrator User Management (list users, filter by role, activate/suspend accounts).
- [ ] Implement Administrator Catalogue Management (CRUD for skills, domains, departments, companies).
- [ ] Implement complete SQL Query Catalogue (Q01–Q32) endpoints & reports:
  - Q01–Q06: Profile retrieval & completeness.
  - Q07–Q14: Candidate discovery, shared skills, capacity limits, unreviewed mentors.
  - Q15–Q20: Inboxes, decision histories, booking calendars.
  - Q21–Q28: Department/domain distributions, ratings, demand vs supply.
  - Q29–Q32: Request-to-Session conversion funnel (CTE), ranking within domain, window functions, full-text search.

### Phase 10: Complete Next.js Frontend Portals
- [ ] Set up Next.js application with TypeScript, Tailwind CSS, Lucide icons, and Axios/Fetch client.
- [ ] Build shared Design System: Navbar, Sidebar, Modal, Badges, Stat Cards, Data Tables, Toast notifications, Confirm dialogs.
- [ ] Implement Authentication Views: Login, Register (Student / Mentor), Role selection.
- [ ] Implement Student Portal:
  - Student Dashboard (stats, pending requests, upcoming sessions, recommended mentors).
  - Student Profile (academic info, skills tagger, domain priority order).
  - Mentor Discovery & Recommendations (search, filters, match score badges, match explanation cards).
  - Requests Management (submit request modal, pending list, history).
  - Booking & Calendar (slot picker, upcoming bookings, cancellation modal).
  - Sessions & Reviews (session history, session detail, feedback form, mentor review dialog).
- [ ] Implement Mentor Portal:
  - Mentor Dashboard (stats, pending requests counter, upcoming appointments, rating summary).
  - Mentor Profile (experience, company, bio, skills, domains, max mentees).
  - Request Management (pending requests inbox, student detail modal, accept/reject buttons).
  - Availability Calendar (weekly/monthly view, slot creator, delete slot).
  - Session Management (appointments, record outcome modal, skill assessment rubric).
  - Reviews & Feedback view.
- [ ] Implement Administrator Portal:
  - User Oversight (users table, role filters, suspend/activate action).
  - Catalogue Management (skills, domains, departments CRUD).
  - Analytics & Reports (Conversion funnel chart, rating breakdown, capacity stats).
  - System Audit Log viewer.
- [ ] Implement Notifications Center (bell icon, dropdown, mark as read).

### Phase 11: Automated Testing & End-to-End Acceptance Verification
- [ ] Unit tests for business rules, authorization, scoring formulas, state guards.
- [ ] Database Integrity tests (DBI-01..DBI-10): constraints, triggers, procedures.
- [ ] Workflow lifecycle tests (WF-01..WF-16): request transitions, booking, session completion.
- [ ] Concurrency tests (TX-01..TX-14): simultaneous double booking of single slot, race conditions on request acceptance.
- [ ] Security tests (SEC-01..SEC-24): student accessing other student data, mentor unauthorized actions, role escalation.
- [ ] Resilience tests (RES): Redis offline resilience, Neo4j offline fallback, Outbox retry.
- [ ] Execute Complete 10-Step Acceptance Scenario end-to-end.
- [ ] Update `REQUIREMENTS_TRACEABILITY.md` and `IMPLEMENTATION_LOG.md`.

