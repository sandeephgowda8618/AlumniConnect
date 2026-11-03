# AlumniConnect — System Architecture & Polyglot Persistence Specification

**Date**: 2026-11-03  
**Status**: Authoritative Architectural Baseline  
**Reference Document**: `AlumniConnect_Application_Architecture.pdf`

---

## 1. High-Level Modular Monolith Architecture

AlumniConnect is built as a high-performance modular monolith with polyglot persistence. The presentation layer is decoupled into a modern Next.js React frontend communicating over REST API endpoints to a FastAPI backend service.

```mermaid
graph LR
  subgraph Frontend ["Frontend Presentation Tier"]
    FE[Next.js 14 React Web App]
    StudentPortal[Student Mentee Portal]
    MentorPortal[Alumni Mentor Portal]
    AdminPortal[Admin Analytics & Audit]
    FE --> StudentPortal
    FE --> MentorPortal
    FE --> AdminPortal
  end

  subgraph Backend ["FastAPI Modular Monolith Core"]
    BE[FastAPI REST API Gateway]
    AuthSvc[Auth & JWT Service]
    ProfileSvc[Profile & Skill Service]
    RequestSvc[Request & Allocation Service]
    BookingSvc[Booking & Concurrency Service]
    SessionSvc[Session & Outcome Service]
    ReviewSvc[Feedback & Review Service]
    RecSvc[5-Factor Recommendation Engine]
    Worker[Transactional Outbox Worker]

    BE --> AuthSvc
    BE --> ProfileSvc
    BE --> RequestSvc
    BE --> BookingSvc
    BE --> SessionSvc
    BE --> ReviewSvc
    BE --> RecSvc
  end

  subgraph Polyglot ["Polyglot Storage & Caching Tier"]
    MySQL[(MySQL 8.x InnoDB<br/>Authoritative ACID Store)]
    Redis[(Redis 7 Cluster<br/>ac:dev:v1: Cache & Limits)]
    Neo4j[(Neo4j 5 Graph Engine<br/>Candidate Discovery & Traversals)]
  end

  FE -->|HTTPS / JSON REST API| BE

  AuthSvc -->|ACID Transactions| MySQL
  ProfileSvc -->|ACID Transactions| MySQL
  RequestSvc -->|Atomic SP01 Acceptance| MySQL
  BookingSvc -->|Pessimistic Locks SP02/SP03| MySQL
  SessionSvc -->|Outcomes SP04| MySQL
  ReviewSvc -->|Bayesian Reviews SP05| MySQL

  ProfileSvc -.->|Graph Node Sync| Neo4j
  ProfileSvc -.->|Profile Cache| Redis

  RecSvc -->|1. Graph Traversal| Neo4j
  RecSvc -->|2. Hard Gating & Capacity| MySQL
  RecSvc -->|3. Cached Results (300s TTL)| Redis

  Worker -->|Poll Unprocessed Events| MySQL
  Worker -->|Dispatch Notifications| MySQL
  Worker -.->|Invalidate Caches| Redis
  Worker -.->|Project Relational Edges| Neo4j
```

---

## 2. Polyglot Persistence Responsibilities

### 2.1 Authoritative Relational Database: MySQL 8.x (InnoDB)
* **Single Source of Truth**: All identities, academic records, mentorship requests, active allocations, bookings, session outcomes, and reviews reside in MySQL 8.x.
* **Strict ACID Concurrency**:
  * Stored procedure `sp_accept_mentorship_request` (SP01) executes atomic state transitions with pessimistic row locks.
  * Stored procedure `sp_create_booking` (SP02) acquires row locks on student profile, availability slot, and allocation, checking interval overlap mutual exclusion.
  * Stored procedure `sp_cancel_booking` (SP03) validates the 2-hour advance cutoff and re-opens availability slots atomically.
  * Stored procedure `sp_record_session_outcome` (SP04) persists discussion summaries and skill assessment rubrics.
  * Stored procedure `sp_submit_mentor_review` (SP05) enforces review eligibility and single-submission constraints.
* **Database Triggers**:
  * `trg_request_status_audit`: Automatically captures transitions of mentorship requests into `audit_log`.
  * `trg_request_status_guard`: Forbids invalid state transitions out of terminal states (`CANCELLED`, `REJECTED`).
  * `trg_session_status_guard`: Enforces strict session lifecycle transitions (`SCHEDULED` $\rightarrow$ `COMPLETED`, `CANCELLED`, `NO_SHOW`).
  * `trg_mentor_review_validate`: Validates rating boundaries (1 to 5).
* **Database Views**:
  * `v_public_mentor_directory` (V01): Strips private emails and sensitive identifiers for public discovery.
  * `v_mentor_rating_summary` (V02): Aggregates mentor reviews, total counts, and average star ratings.
  * `v_student_mentorship_summary` (V03): Summarizes student requests, completed sessions, and active allocations.
  * `v_mentor_session_outcomes` (V04): Joins completed sessions with skill assessments and feedback ratings.

### 2.2 In-Memory Distributed Cache: Redis 7
* **Namespace Hierarchy**: Strict key convention following Redis Design §3:
  * `ac:dev:v1:mentor:profile:{id}:public` (TTL 600s)
  * `ac:dev:v1:catalog:skills:all` (TTL 3600s)
  * `ac:dev:v1:catalog:domains:all` (TTL 3600s)
  * `ac:dev:v1:rec:student:{id}:filters:{hash}` (TTL 300s)
* **Targeted Cache Invalidation**: Mutation of student skills, mentorship domains, or mentor profiles instantly purges matching pattern keys via `delete_by_pattern()`.
* **Resilient Fallback**: An in-memory cache store with matching TTL and hash semantics is embedded for offline sandbox environments.

### 2.3 Graph Traversal Engine: Neo4j 5
* **Domain Graph Projection**:
  * Nodes: `(:Student)`, `(:Mentor)`, `(:Skill)`, `(:Domain)`, `(:Department)`, `(:Company)`.
  * Relationships: `[:HAS_SKILL]`, `[:INTERESTED_IN]`, `[:SPECIALIZES_IN]`, `[:BELONGS_TO]`, `[:WORKS_AT]`, `[:MENTORED_BY]`.
* **Candidate Discovery**: Cypher traversal queries discover mentors sharing skills or domain interests with the student:
  ```cypher
  MATCH (s:Student {studentId: $id})-[:HAS_SKILL]->(k:Skill)<-[:HAS_SKILL]-(m:Mentor)
  RETURN m.mentorId AS mentor_id, collect(k.name) AS shared_skills
  ```

---

## 3. Transactional Outbox Pattern

To ensure reliable notification dispatch without distributed 2-phase commits:
1. Business transactions write their payload into `notification_outbox` in the same MySQL transaction.
2. A dedicated background worker (`app.workers.outbox_worker`) periodically polls `PENDING` outbox events with row locks (`SELECT ... FOR UPDATE SKIP LOCKED`).
3. Events are delivered to `notification` and marked `PROCESSED`.
4. Idempotency is guaranteed through unique `dedupe_key` hashes.

