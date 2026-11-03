# AlumniConnect — Defect & Issue Register

**Date**: 2026-11-03  
**Status**: Authoritative Resolution Log  
**Scope**: Production-Readiness Remediation Tracking

---

## 1. Issue Summary

| Issue ID | Severity | Category | Title | Status | Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AC-001** | **P0** | Concurrency / DB | Double Booking Race Condition & Student Schedule Overlap | **RESOLVED** | Row locks added on student profile, availability slot, and allocation; mutual exclusion enforced. |
| **AC-002** | **P0** | Security / Auth | Insecure Direct Object Reference (IDOR) on Session Outcomes | **RESOLVED** | Ownership verification added in `GET /api/v1/sessions/{session_id}` for participants/admin only. |
| **AC-003** | **P0** | Transactions | Missing Row Lock on Request Acceptance & Split-Brain Allocation | **RESOLVED** | Enforced `FOR UPDATE` on request row; inserts allocation prior to status transition; unique key guard. |
| **AC-004** | **P1** | Schema / Integrity | Missing Foreign Keys & Uniqueness Constraints on Key Entities | **RESOLVED** | Foreign keys verified; unique keys on `skill_name`, `domain_name`, `idempotency_key`, and active slots. |
| **AC-005** | **P1** | DevOps / CI | Missing Continuous Integration & Testing Automation Pipeline | **RESOLVED** | Created `.github/workflows/ci.yml` with linting, pytest, next build, security audits, and Docker tests. |
| **AC-006** | **P1** | Business Rules | Booking Cancellation Missing 2-Hour Cutoff in Stored Procedure | **RESOLVED** | Added 2-hour interval check in `sp_cancel_booking` and updated `BookingService.cancel_booking`. |
| **AC-007** | **P0** | Integration / CORS | Unhandled 401/422/500 Errors Blocking Browser Fetch via CORS | **RESOLVED** | Added global exception handlers injecting `Access-Control-Allow-Origin` and credentials on all error codes. |
| **AC-008** | **P1** | Security / Infra | Docker Compose Root User and Plaintext Credential Defaults | **RESOLVED** | Migrated `docker-compose.yml` to non-root app user, environment variable overrides, and healthchecks. |
| **AC-009** | **P1** | UI / Discovery | Complete Profile Banner Displayed When Student Already Has Skills | **RESOLVED** | Updated condition in `mentors/page.tsx` to strictly check `!studentProfile.skills.length`. |
| **AC-010** | **P1** | Data Flow | Target Career Goal Not Stored in Relational Domain Interest Table | **RESOLVED** | Added automated domain interest linking in `AuthService.register_student` and synced in DB. |
| **AC-E2E-001** | **P2** | Logic / Defect | Admin Booking Cancellation Model Query Attribute Error | **RESOLVED** | Replaced erroneous `Booking` model query with `UserAccount.role.role_code == 'ADMINISTRATOR'`. |
| **AC-E2E-002** | **P3** | Schema / API | Booking Cancellation Request Reason Payload Requirement | **RESOLVED** | Made `reason` optional with default value `"Cancelled by user"` in `BookingCancelRequest`. |

---

## 2. Detailed Defect Analysis & Fix Records

### AC-001 (P0): Double Booking Race Condition & Student Schedule Overlap
* **Problem**: If two requests to book the same slot were submitted simultaneously, both could read the slot as `OPEN` and create duplicate confirmed bookings. Additionally, a student could book two different mentors during overlapping time windows.
* **Evidence**: Concurrency audit flagged lack of row locking on the student profile during booking creation.
* **Fix**:
  1. Updated `BookingService.create_booking`:
     ```python
     # Row lock on student profile prevents concurrent overlap races by the same student
     student = self.db.query(StudentProfile).filter(StudentProfile.user_id == actor_user_id).with_for_update().first()
     slot = self.avail_repo.get_by_id(availability_id, lock=True)
     alloc = self.alloc_repo.get_by_id(allocation_id, lock=True)
     
     # Check active booking existence
     existing = self.db.query(Booking).filter(
         Booking.availability_id == availability_id,
         Booking.booking_status == "CONFIRMED"
     ).with_for_update().first()
     if existing:
         raise ValueError("Availability slot has already been confirmed for another booking")
     ```
  2. Verified `sp_create_booking` performs identical row-level locks and interval checks.

---

### AC-002 (P0): IDOR on Mentorship Session Details
* **Problem**: `GET /api/v1/sessions/{session_id}` returned private evaluation notes, rubric ratings, and action items to any authenticated user regardless of whether they were part of the session.
* **Evidence**: In `sessions.py`, `_format_session_out(session, current_user.user_id)` was called without checking participant authorization.
* **Fix**: Added explicit guard:
  ```python
  req = session.booking.allocation.request if (session.booking and session.booking.allocation) else None
  is_student = req and req.student_user_id == current_user.user_id
  is_mentor = req and req.mentor_user_id == current_user.user_id
  is_admin = current_user.role and current_user.role.role_code == "ADMINISTRATOR"
  if not (is_student or is_mentor or is_admin):
      raise HTTPException(status_code=403, detail="Forbidden")
  ```

---

### AC-003 (P0): Request Acceptance Atomicity & Invariant Protection
* **Problem**: If request acceptance failed halfway through or was invoked concurrently by multiple workers, the request status could be marked `ACCEPTED` without an allocation, or multiple allocations could be created.
* **Evidence**: Stored procedure `sp_accept_mentorship_request` and `RequestService.accept_request` needed strict ordering.
* **Fix**:
  1. `SELECT ... FOR UPDATE` acquired on `mentorship_request`.
  2. `mentor_allocation` inserted with `request_id` unique constraint.
  3. `mentorship_request` status updated to `ACCEPTED`.
  4. Outbox event written in the same transaction before `self.db.commit()`.

---

### AC-009 (P1): Profile Setup Banner Displayed on Users with Configured Skills
* **Problem**: In `frontend/src/app/student/mentors/page.tsx`, the banner condition was `(studentProfile.skills.length === 0 || studentProfile.domain_interests.length === 0)`. When a student configured skills (`Docker`, `Kubernetes`) but had no explicit domain interests, the banner still showed.
* **Fix**: Updated condition to:
  ```tsx
  {studentProfile && (!studentProfile.skills || studentProfile.skills.length === 0) && (
    <div className="my-6 p-5 ...">...Complete Profile & Skill Setup...</div>
  )}
  ```
  Now, if any skill is configured, the banner is suppressed immediately.
