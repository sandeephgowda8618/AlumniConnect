# AlumniConnect — Open Decisions & Implementation Reconciliations

This document tracks all design decisions, reconciliations between specifications, and configurable policy defaults for AlumniConnect, strictly adhering to the 15 authoritative project reference documents.

---

## 1. Resolved Reconciliations Across Specifications

| ID | Topic | Discrepancy / Choice | Authoritative Source Reconciliation | Implementation Decision & Status |
|---|---|---|---|---|
| **OD-01** | **Allocation Lifecycle States** | Some early draft documents mention `COMPLETED` / `TERMINATED` for allocations, while the Relational Design and Business Rules Catalogue use `ACTIVE` and `ENDED`. | Relational Design Specification (§2.1, p. 4) and Business Rules Catalogue explicitly standardise on `ACTIVE` and `ENDED`. | **Adopted**: `mentor_allocation.allocation_status` ENUM/VARCHAR check allows `ACTIVE` and `ENDED`. Reasons for termination stored in `termination_reason`. |
| **OD-02** | **Booking Requires Active Allocation** | Conceptual ER diagram showed `allocation_id` as optional (`0..1`) for potential ad-hoc public mock interviews, while PRD, Business Rules, and Relational Design require an accepted allocation. | Relational Design Specification (§2.1, p. 4 & A7) resolves: Core Release 1 bookings strictly require an `ACTIVE` allocation (`allocation_id NOT NULL`). Ad-hoc bookings without allocation are deferred to Phase 2. | **Adopted**: `booking.allocation_id` is mandatory (`NOT NULL`) and foreign-keyed to `mentor_allocation(allocation_id)`. |
| **OD-03** | **Participant Redundancy in Allocation & Booking** | Conceptual/sample queries in Business Rules showed redundant `student_id` and `mentor_id` in `mentor_allocation` and `booking`, while Relational Design normalizes them. | Relational Design Specification (§2.1 & Normalization walkthrough §7, pp. 4, 15-20) specifies that 3NF/BCNF removes transitive dependencies: student and mentor are derived from `mentorship_request` (for allocation) and through `allocation`/`availability` (for booking). Views provide convenience joins. | **Adopted**: Normalized schema avoids update anomalies. Views `v_student_mentorship_summary` and `v_booking_details` expose denormalized attributes cleanly for reads. |
| **OD-04** | **Availability Slot Lifecycle States** | Draft documents refer to slots as `AVAILABLE` or `OPEN`. | Relational Design Specification (§2.1, p. 4) and Business Rules Catalogue standardize availability slot vocabulary: `OPEN`, `BOOKED`, `BLOCKED`, `EXPIRED`. | **Adopted**: `mentor_availability.slot_status` uses `OPEN`, `BOOKED`, `BLOCKED`, `EXPIRED`. |
| **OD-05** | **Event Log vs Audit Log vs Outbox** | Business Rules examples mention `business_event_log`, while Conceptual ER and Relational Design define `audit_log` and `notification_outbox`. | Relational Design Specification (§2.1, p. 4) reconciles: `audit_log` is dedicated to actor/action compliance auditing, while `notification_outbox` is dedicated to asynchronous transactional event delivery and fan-out to `notification`. | **Adopted**: Two separate tables implemented: `audit_log` and `notification_outbox`. No redundant `business_event_log` table. |
| **OD-06** | **Outbox to Notification Fan-out** | Single outbox row per event vs single outbox row per recipient. | Relational Design Specification (§2.1, p. 4 & A15): One durable domain event inserted into `notification_outbox`. The background worker fans out into individual `notification` records per recipient, deduplicated by `UNIQUE(outbox_id, recipient_user_id)`. | **Adopted**: Outbox preserves 1:N fan-out to recipient inboxes. |

---

## 2. Configurable Policy Defaults (Documented Defaults)

The reference documents explicitly distinguish between mandatory system invariants and configurable operational policies. The following defaults are implemented and exposed via configuration:

| ID | Policy Parameter | Reference Document | Recommended Default | Config Key / Location |
|---|---|---|---|---|
| **CP-01** | **Recommendation Scoring Weights** | Recommendation Design (§7, p. 11) | Skills: `30%`<br>Domain: `20%`<br>Experience: `15%`<br>Career: `20%`<br>Quality: `15%` | `RECOMMENDATION_WEIGHTS` in `backend/app/core/config.py` |
| **CP-02** | **Recommendation Capacity Filter** | Recommendation Design (§7, p. 11) & PRD (FR-09) | Binary Hard Gate (Filter out mentors with active mentees >= `max_active_mentees`) | `RECOMMENDATION_GATE_CAPACITY=True` |
| **CP-03** | **Booking Cancellation Cutoff Window** | Business Rules Catalogue (BR-T16, BR-T17) | `2 hours` prior to slot start time (`starts_at`) | `BOOKING_CANCELLATION_CUTOFF_HOURS=2` |
| **CP-04** | **Slot Reopening on Cancellation** | Relational Design (A8) & SP03 | If cancelled before cutoff, future slot status is restored to `OPEN` unless explicitly blocked by mentor. | `REOPEN_SLOT_ON_CANCELLATION=True` |
| **CP-05** | **Default Max Active Mentees** | Relational Design (Table `mentor_profile`) | Default: `2` active mentees per mentor (mentor can adjust in profile). | `DEFAULT_MAX_ACTIVE_MENTEES=2` |
| **CP-06** | **Rating Prior for Bayesian Quality Score** | Recommendation Design (§8.5, p. 14) | Prior weight `m = 5` reviews, Default platform rating mean `PlatformAverage = 4.0` | `BAYESIAN_PRIOR_M=5`, `DEFAULT_PLATFORM_RATING=4.0` |
| **CP-07** | **Redis Cache Key Prefix & TTLs** | Redis Design Specification (§3, §7) | Namespace: `ac:{env}:v1:`<br>Profile: `600s`<br>Catalogues: `3600s`<br>Recs: `300s`<br>Availability: `15s`<br>Idempotency: `86400s` | `backend/app/core/redis_config.py` |
| **CP-08** | **Session Status Lifecycle** | Workflow and State Diagrams (§7) | `SCHEDULED` -> `COMPLETED`, `CANCELLED`, or `NO_SHOW` | Enforced by Trigger `trg_session_status_guard` |
| **CP-09** | **Review Eligibility Window** | Business Rules (BR-T24) & SP05 | Exactly 1 review per student per completed session; rating integer between `1` and `5`. | Enforced by Trigger `trg_mentor_review_validate` & SP05 |

---

## 3. Scope Boundaries Maintained (Non-Core Phase 2 Exclusions)

As directed by the PRD and project blueprint:
- **No Real-Money Payments**: Free mentorship/mock interview platform.
- **No Video Conferencing**: Offline/independent video platform. Platform tracks scheduling, booking, agenda, and outcomes.
- **No Independent Microservices**: Strict Modular Monolith in FastAPI.
- **No Vector Search in Release 1**: Deterministic Neo4j graph traversal + multi-dimensional weighted ranking + MySQL validation.

