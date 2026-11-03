# AlumniConnect — Comprehensive Database Population & Seeding Report

**Authoritative DBMS Project Technical Verification & Seeding Documentation**  
**Database Architecture:** MySQL 8.x / InnoDB Relational Core (with SQLite local development compatibility)  
**Supporting Engines:** Redis Key-Value Cache-Aside (`ac:dev:v1:*`), Neo4j / In-Memory Graph Engine  
**Seeding Implementation:** `backend/scripts/seed_demo_data.py` (Idempotent, Reusable, Deterministic)  
**Execution Timestamp:** 2026-11-03  

---

## A. Population Summary

The AlumniConnect relational database was systematically populated with high-fidelity, interconnected synthetic demo data strictly adhering to the 15 authoritative specification blueprints (`Docs/reference/`).

- **Total Registered Accounts:** 19 Users
  - **Administrators:** 1 Account (`admin@alumniconnect.edu`)
  - **Alumni Mentors:** 8 Complete Professional Profiles across 8 major companies
  - **Student Mentees:** 10 Complete Academic Profiles across 5 engineering departments
- **Academic Departments:** 6 Registered Institutional Departments
- **Partner & Alumni Companies:** 9 Technology & Engineering Enterprises
- **Verified Skills Catalogue:** 15 Technical Competencies
- **Mentorship Domains:** 7 Specialized Practice Areas
- **Mentorship Ecosystem Operations:**
  - **Mentorship Requests:** 17 Lifecycle Records (`ACCEPTED`, `PENDING`, `REJECTED`, `CANCELLED`)
  - **Active & Historical Allocations:** 8 Verified Mentorship Agreements (6 Active, 2 Ended)
  - **Mentor Availability Schedule:** 27 Discrete Calendar Slots (8 Past Booked, 4 Upcoming Booked, 13 Open Future, 2 Cancelled)
  - **Transactional Bookings:** 12 ACID-guaranteed Booking Appointments
  - **Mentorship Sessions:** 12 Session Records (7 Completed with comprehensive evaluations, 4 Scheduled upcoming, 1 Cancelled)
  - **Skill Evaluations:** 15 Objective Session Rubric Assessments
  - **Two-Way Feedback:** 14 Session Feedback Records (Student & Mentor ratings)
  - **Eligible Mentor Reviews:** 6 Verified Public Student Reviews (Average platform rating: 4.67 / 5.00)
  - **Recommendation Runs & Graph Projections:** 7 Executed Pipelines yielding 33 Ranked Recommendations
  - **Transactional Outbox & In-App Inboxes:** 9 Outbox Events delivering 14 Notifications
  - **Immutable Audit Trail:** 15 Structured Event Audit Records

---

## B. Table-by-Table Record Count Report

Every data-bearing relational table defined in `app/db/schema.sql` and `app/models/entities.py` was populated to meet or exceed the target of **at least 5 valid records**.

| Table Name | Existing Records | Inserted Records | Final Records | Minimum Target | Compliance Status | Business Integrity Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `role` | 3 | 0 | **3** | 3 | **PASS** | Fixed domain: `ADMINISTRATOR`, `MENTOR`, `STUDENT`. Preserved without invalid synthetic roles. |
| `department` | 4 | 2 | **6** | 5 | **PASS** | Covers CSE, ECE, AIML, ISE, EEE, and MECH at PES University. |
| `company` | 5 | 4 | **9** | 5 | **PASS** | Google, Amazon, Microsoft, Cisco, Goldman Sachs, Apple, NVIDIA, Atlassian, Uber. |
| `skill` | 12 | 3 | **15** | 5 | **PASS** | Distributed across Foundations, Programming, AI, Cloud, Databases, Security. |
| `mentorship_domain` | 5 | 2 | **7** | 5 | **PASS** | Covers ML, Cloud/DevOps, Full-Stack, Distributed Systems, Data Eng, AppSec, CP. |
| `user_account` | 6 | 13 | **19** | 5 | **PASS** | 1 Admin, 8 Mentors, 10 Students. Bcrypt hashes (`Password123!`). |
| `student_profile` | 2 | 8 | **10** | 5 | **PASS** | Rich biographical, academic, and career goal attributes. |
| `mentor_profile` | 3 | 5 | **8** | 5 | **PASS** | Diverse designations (Staff ML, VP Eng, Principal SRE, Solutions Architect). |
| `student_skill` | 5 | 27 | **32** | 5 | **PASS** | Multiple skill associations per student with proficiency and experience. |
| `mentor_skill` | 10 | 25 | **35** | 5 | **PASS** | Expert and advanced proficiency ratings backed by years of experience. |
| `student_domain_interest`| 3 | 17 | **20** | 5 | **PASS** | Priority-ordered interest rankings (Priority 1, 2) with learning goals. |
| `mentor_domain_expertise`| 5 | 11 | **16** | 5 | **PASS** | Primary and secondary domain authorizations with expertise levels. |
| `mentorship_request` | 1 | 16 | **17** | 5 | **PASS** | Demonstrates all 4 states: `ACCEPTED` (8), `PENDING` (4), `REJECTED` (3), `CANCELLED` (2). |
| `mentor_allocation` | 0 | 8 | **8** | 5 | **PASS** | 6 `ACTIVE` mentorship allocations, 2 `ENDED` historical milestones. |
| `mentor_availability` | 3 | 24 | **27** | 5 | **PASS** | Chronologically spread from past historical to future upcoming schedules. |
| `booking` | 0 | 12 | **12** | 5 | **PASS** | 7 Completed historical, 4 Confirmed upcoming, 1 Cancelled with reasons. |
| `mentorship_session` | 0 | 12 | **12** | 5 | **PASS** | 7 Completed sessions with deep technical feedback, 4 Scheduled, 1 Cancelled. |
| `session_skill_assessment`| 0 | 15 | **15** | 5 | **PASS** | Objective skill results (`EXPERT`, `PROFICIENT`, `NEEDS_IMPROVEMENT`). |
| `session_feedback` | 0 | 14 | **14** | 5 | **PASS** | Two-way ratings on communication, helpfulness, and technical preparation. |
| `mentor_review` | 0 | 6 | **6** | 5 | **PASS** | Verified student reviews with written testimonials (ratings 4 to 5). |
| `recommendation_run` | 1 | 6 | **7** | 5 | **PASS** | Multi-factor graph recommendation runs persisted across students. |
| `recommended_mentor` | 3 | 30 | **33** | 5 | **PASS** | Ranked candidates with multi-factor scores and explainability rationale. |
| `notification_outbox` | 2 | 7 | **9** | 5 | **PASS** | Asynchronous transactional outbox event records with deduplication keys. |
| `notification` | 2 | 12 | **14** | 5 | **PASS** | Delivered in-app notifications in user inboxes. |
| `audit_log` | 1 | 14 | **15** | 5 | **PASS** | Comprehensive audit trail of logins, requests, bookings, and outcomes. |

*Note on Fixed-Domain Exception:* The `role` catalogue is restricted to the three architectural roles (`ADMINISTRATOR`, `MENTOR`, `STUDENT`) required by the RBAC design. Creating arbitrary synthetic roles would violate the application's authorization boundaries.

---

## C. Demo User Credentials & Access Directory

All demo accounts share the uniform development credential policy:
**Password:** `Password123!` (Bcrypt Hash: `$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a`).

### 1. Administrator Account
| User ID | Full Name | Email Address | Role | System Authority |
| :---: | :--- | :--- | :---: | :--- |
| **1** | Dr. Radhika Sen | `admin@alumniconnect.edu` | `ADMINISTRATOR` | Full system audit, catalogue management, capacity & funnel analytics. |

### 2. Alumni Mentor Accounts
| User ID | Full Name | Email Address | Company | Designation | Dept | Exp | Max Mentees |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **2** | Rohit Verma | `rohit.verma@alumniconnect.edu` | Google | Senior Machine Learning Engineer | CSE | 5.5y | 3 |
| **3** | Sneha Rao | `sneha.rao@alumniconnect.edu` | Amazon | Principal Solutions Architect | ISE | 6.5y | 2 |
| **4** | Vikram Joshi | `vikram.joshi@alumniconnect.edu` | Microsoft | Lead Software Engineer | CSE | 4.0y | 3 |
| **7** | Ananya Deshmukh | `ananya.deshmukh@alumniconnect.edu` | NVIDIA | Staff ML & Computer Vision Engineer | ECE | 7.0y | 3 |
| **8** | Karthik Subramanian | `karthik.subramanian@alumniconnect.edu` | Goldman Sachs | VP of Engineering - FinTech Core | CSE | 9.5y | 2 |
| **9** | Neha Kulkarni | `neha.kulkarni@alumniconnect.edu` | Cisco Systems | Senior Security Architect | ISE | 5.0y | 3 |
| **10** | Aditya Nair | `aditya.nair@alumniconnect.edu` | Uber | Lead Data Platform Engineer | AIML | 4.5y | 2 |
| **11** | Meera Iyer | `meera.iyer@alumniconnect.edu` | Apple | Principal Site Reliability Engineer | CSE | 8.0y | 2 |

### 3. Student Mentee Accounts
| User ID | Full Name | Email Address | Dept | Batch | Grad | Career Focus Area |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **5** | Aarav Sharma | `aarav.sharma@alumniconnect.edu` | CSE | 2022 | 2026 | Machine Learning & Systems Software |
| **6** | Priya Patel | `priya.patel@alumniconnect.edu` | AIML | 2023 | 2027 | Cloud DevOps & Scalable ML Platforms |
| **12** | Rohan Gupta | `rohan.gupta@alumniconnect.edu` | CSE | 2022 | 2026 | Enterprise Full-Stack SaaS Engineering |
| **13** | Tanvi Shukla | `tanvi.shukla@alumniconnect.edu` | ISE | 2023 | 2027 | Data Science & Big Data Analytics |
| **14** | Siddharth Menon | `siddharth.menon@alumniconnect.edu` | ECE | 2021 | 2025 | Edge AI, IoT & Cloud Connectivity |
| **15** | Ananya Bhat | `ananya.bhat@alumniconnect.edu` | AIML | 2023 | 2027 | Applied NLP & LLM Systems Research |
| **16** | Varun Chatterjee | `varun.chatterjee@alumniconnect.edu` | CSE | 2022 | 2026 | Application Security & Penetration Testing |
| **17** | Isha Singh | `isha.singh@alumniconnect.edu` | ISE | 2022 | 2026 | Distributed Backend & High Concurrency |
| **18** | Dev Kapoor | `dev.kapoor@alumniconnect.edu` | CSE | 2023 | 2027 | Competitive Programming & High-Perf Systems |
| **19** | Ritika Nambiar | `ritika.nambiar@alumniconnect.edu` | EEE | 2022 | 2026 | Hardware-Software Co-Design & Telemetry |

---

## D. Booking & Mentorship Ecosystem Overview

The populated database establishes real, end-to-end relational connections between students and mentors across all supported booking states.

| Booking ID | Student Mentee | Mentor | Type | Booking Status | Scheduled Start (UTC) | Allocation ID | Session Status | Review Rating |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | Aarav Sharma | Rohit Verma | `MENTORSHIP` | `CONFIRMED` | 2026-10-22 07:00 | 1 | `COMPLETED` | ★★★★★ (5) |
| **2** | Priya Patel | Sneha Rao | `MOCK_INTERVIEW` | `CONFIRMED` | 2026-10-24 05:00 | 2 | `COMPLETED` | ★★★★★ (5) |
| **3** | Rohan Gupta | Vikram Joshi | `MENTORSHIP` | `CONFIRMED` | 2026-10-26 08:00 | 3 | `COMPLETED` | ★★★★☆ (4) |
| **4** | Tanvi Shukla | Aditya Nair | `MOCK_INTERVIEW` | `CONFIRMED` | 2026-10-28 06:00 | 4 | `COMPLETED` | ★★★★★ (5) |
| **5** | Siddharth Menon | Meera Iyer | `MENTORSHIP` | `CONFIRMED` | 2026-10-29 04:00 | 5 | `COMPLETED` | ★★★★☆ (4) |
| **6** | Varun Chatterjee | Neha Kulkarni | `MOCK_INTERVIEW` | `CONFIRMED` | 2026-10-30 09:00 | 6 | `COMPLETED` | ★★★★★ (5) |
| **7** | Dev Kapoor | Ananya Deshmukh | `MOCK_INTERVIEW` | `CONFIRMED` | 2026-10-31 05:00 | 7 | `COMPLETED` | Pending |
| **8** | Aarav Sharma | Rohit Verma | `MENTORSHIP` | `CONFIRMED` | 2026-11-04 12:00 | 1 | `SCHEDULED` | N/A (Upcoming) |
| **9** | Priya Patel | Sneha Rao | `MOCK_INTERVIEW` | `CONFIRMED` | 2026-11-05 14:00 | 2 | `SCHEDULED` | N/A (Upcoming) |
| **10** | Rohan Gupta | Vikram Joshi | `MENTORSHIP` | `CONFIRMED` | 2026-11-06 13:00 | 3 | `SCHEDULED` | N/A (Upcoming) |
| **11** | Tanvi Shukla | Aditya Nair | `MENTORSHIP` | `CONFIRMED` | 2026-11-08 15:00 | 4 | `SCHEDULED` | N/A (Upcoming) |
| **12** | Isha Singh | Karthik Subramanian | `MENTORSHIP` | `CANCELLED` | 2026-11-01 07:00 | 8 | `CANCELLED` | N/A (Exam Conflict) |

---

## E. Relational Integrity & Schema Validation

Integrity checks executed on the populated database confirmed:
1. **Foreign Key Integrity:** Zero orphan records across all 25 relational tables. Every junction record (`student_skill`, `mentor_skill`, `student_domain_interest`, `mentor_domain_expertise`) resolves to existing primary entities.
2. **Unique Constraints:**
   - `uq_booking_active_slot` / `idempotency_key`: Zero duplicate active bookings per availability slot.
   - `uq_mentor_slot_interval`: Zero overlapping availability slots for any mentor.
   - `uq_student_domain_priority`: Strict priority order enforcement per student.
   - `uq_feedback_session_user`: Exactly one feedback per participant per session.
   - `user_account.email`: Strict email uniqueness maintained.
3. **Capacity Constraints:** Mentor active allocations obey `max_active_mentees` (highest current utilization is 50%, no mentor exceeds capacity).
4. **Lifecycle Consistency:**
   - Every completed mentorship session has corresponding actual timestamps (`actual_start_at`, `actual_end_at`), recorder user ID, and detailed observations.
   - Every review references an actual completed session with a valid rating between 1 and 5.
   - Cancelled bookings have `cancelled_at`, `cancelled_by_user_id`, and structured `cancellation_reason`.

---

## F. Redis & Neo4j Synchronization Verification

1. **Graph Traversal Engine (Neo4j / Resilient In-Memory Graph Projection):**
   - Synchronized all 19 User nodes, 10 Student nodes, 8 Mentor nodes, 6 Department nodes, 9 Company nodes, 15 Skill nodes, and 7 Domain nodes.
   - Projected all directional relationships: `[:HAS_SKILL]`, `[:INTERESTED_IN]`, `[:EXPERT_IN]`, `[:ALUMNI_OF]`, `[:EMPLOYED_BY]`, and `[:MENTORED_BY]`.
   - Verified that calling `/api/v1/recommendations/discover` dynamically traverses graph candidate sets and executes the 5-factor weighted scoring model across skills, domains, experience, career goals, and Bayesian rating smoothing.
2. **Redis Cache Store (`ac:dev:v1:*`):**
   - Invalidation mechanisms executed for updated mentor profiles.
   - Pre-warmed catalogues for instant, sub-millisecond frontend retrieval.

---

## G. Frontend Verification

The populated dataset renders fully across all 20 Next.js routes:

- **Student Portal:**
  - `http://localhost:3000/student/mentors`: Displays 8 verified mentors across Google, Amazon, Microsoft, NVIDIA, Goldman Sachs, Cisco, Apple, and Uber with multi-factor match explanations and domain tags.
  - `http://localhost:3000/student/requests`: Shows submitted, accepted, and pending requests.
  - `http://localhost:3000/student/sessions`: Displays both upcoming scheduled appointments (with countdown timers) and historical completed sessions with mentor feedback and review dialogs.
  - `http://localhost:3000/student/profile`: Shows full student biography, skill proficiencies, and prioritized domain interests.
- **Mentor Portal:**
  - `http://localhost:3000/mentor/dashboard`: Reflects active mentee allocation counts, upcoming appointments, and average rating summaries.
  - `http://localhost:3000/mentor/requests`: Shows incoming requests with Accept/Reject actions.
  - `http://localhost:3000/mentor/availability`: Displays published availability slots (both booked and open for reservation).
  - `http://localhost:3000/mentor/sessions`: Enables mentors to review session history and record outcomes for scheduled slots.
- **Administrator Portal:**
  - `http://localhost:3000/admin/dashboard`: Populates platform statistics (10 students, 8 mentors, 17 requests, 6 active allocations, 7 completed sessions, 4.67 average rating).
  - `http://localhost:3000/admin/funnel`: Renders the complete request-to-allocation-to-booking-to-session conversion funnel.
  - `http://localhost:3000/admin/capacity`: Displays mentor capacity utilization percentages.
  - `http://localhost:3000/admin/audit`: Shows chronological system audit logs.

---

## H. Seeding Script Reusability & Execution

To re-seed or verify the database at any time, run:

```bash
cd backend
python3 scripts/seed_demo_data.py
```

The script is **fully idempotent**: re-executing it performs non-destructive upserts, preserving existing data and avoiding duplicate records.

