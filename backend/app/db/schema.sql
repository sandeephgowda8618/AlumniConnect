-- AlumniConnect Authoritative Relational Schema (MySQL 8.x / InnoDB)
-- Aligned with AlumniConnect Relational Design Specification Version 1.2
-- Conceptual ER Model: 24 conceptual entities + 1 assessment junction = 25 relational tables

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Reference and Identity Relations

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS notification;
DROP TABLE IF EXISTS notification_outbox;
DROP TABLE IF EXISTS mentor_review;
DROP TABLE IF EXISTS session_feedback;
DROP TABLE IF EXISTS session_skill_assessment;
DROP TABLE IF EXISTS mentorship_session;
DROP TABLE IF EXISTS booking;
DROP TABLE IF EXISTS mentor_availability;
DROP TABLE IF EXISTS mentor_allocation;
DROP TABLE IF EXISTS recommended_mentor;
DROP TABLE IF EXISTS recommendation_run;
DROP TABLE IF EXISTS mentorship_request;
DROP TABLE IF EXISTS mentor_domain_expertise;
DROP TABLE IF EXISTS student_domain_interest;
DROP TABLE IF EXISTS mentor_skill;
DROP TABLE IF EXISTS student_skill;
DROP TABLE IF EXISTS mentorship_domain;
DROP TABLE IF EXISTS skill;
DROP TABLE IF EXISTS mentor_profile;
DROP TABLE IF EXISTS student_profile;
DROP TABLE IF EXISTS user_account;
DROP TABLE IF EXISTS company;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS role;

SET FOREIGN_KEY_CHECKS = 1;

-- 1.1 Role
CREATE TABLE role (
  role_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_code VARCHAR(30) NOT NULL UNIQUE,
  role_name VARCHAR(80) NOT NULL,
  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.2 Department
CREATE TABLE department (
  department_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  department_code VARCHAR(30) NOT NULL,
  department_name VARCHAR(120) NOT NULL,
  institution_name VARCHAR(160) NOT NULL,
  UNIQUE KEY uq_dept_institution_code (institution_name, department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.3 Company
CREATE TABLE company (
  company_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  company_name VARCHAR(180) NOT NULL,
  website_url VARCHAR(255),
  industry VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.4 User Account
CREATE TABLE user_account (
  user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_id BIGINT UNSIGNED NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(120) NOT NULL,
  account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  last_login_at DATETIME(6),
  CONSTRAINT fk_user_role FOREIGN KEY (role_id)
    REFERENCES role(role_id) ON DELETE RESTRICT,
  CONSTRAINT chk_user_status CHECK
    (account_status IN ('ACTIVE','SUSPENDED','DEACTIVATED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Role-Specific Profiles

-- 2.1 Student Profile
CREATE TABLE student_profile (
  user_id BIGINT UNSIGNED PRIMARY KEY,
  student_number VARCHAR(50) NOT NULL UNIQUE,
  department_id BIGINT UNSIGNED NOT NULL,
  programme VARCHAR(120) NOT NULL,
  batch_year SMALLINT NOT NULL,
  expected_graduation_year SMALLINT,
  career_goal TEXT,
  bio TEXT,
  CONSTRAINT fk_student_user FOREIGN KEY (user_id)
    REFERENCES user_account(user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_student_department FOREIGN KEY (department_id)
    REFERENCES department(department_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2.2 Mentor Profile
CREATE TABLE mentor_profile (
  user_id BIGINT UNSIGNED PRIMARY KEY,
  alumni_identifier VARCHAR(60) UNIQUE,
  alumni_department_id BIGINT UNSIGNED NOT NULL,
  current_company_id BIGINT UNSIGNED,
  job_title VARCHAR(120) NOT NULL,
  years_experience DECIMAL(4,1) NOT NULL DEFAULT 0,
  max_active_mentees SMALLINT NOT NULL DEFAULT 1,
  accepting_requests BOOLEAN NOT NULL DEFAULT TRUE,
  professional_summary TEXT,
  CONSTRAINT fk_mentor_user FOREIGN KEY (user_id)
    REFERENCES user_account(user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_mentor_department FOREIGN KEY (alumni_department_id)
    REFERENCES department(department_id) ON DELETE RESTRICT,
  CONSTRAINT fk_mentor_company FOREIGN KEY (current_company_id)
    REFERENCES company(company_id) ON DELETE RESTRICT,
  CONSTRAINT chk_mentor_experience CHECK (years_experience >= 0),
  CONSTRAINT chk_mentor_capacity CHECK (max_active_mentees >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Skills and Domains

-- 3.1 Skill
CREATE TABLE skill (
  skill_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  skill_name VARCHAR(100) NOT NULL UNIQUE,
  category VARCHAR(80),
  description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.2 Mentorship Domain
CREATE TABLE mentorship_domain (
  domain_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  domain_name VARCHAR(120) NOT NULL UNIQUE,
  description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.3 Student Skill Association (M:N)
CREATE TABLE student_skill (
  student_user_id BIGINT UNSIGNED NOT NULL,
  skill_id BIGINT UNSIGNED NOT NULL,
  proficiency_level VARCHAR(20) NOT NULL,
  years_experience DECIMAL(4,1),
  added_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (student_user_id, skill_id),
  CONSTRAINT fk_studentskill_student FOREIGN KEY (student_user_id)
    REFERENCES student_profile(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_studentskill_skill FOREIGN KEY (skill_id)
    REFERENCES skill(skill_id) ON DELETE RESTRICT,
  CONSTRAINT chk_studentskill_exp CHECK (years_experience IS NULL OR years_experience >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.4 Mentor Skill Association (M:N)
CREATE TABLE mentor_skill (
  mentor_user_id BIGINT UNSIGNED NOT NULL,
  skill_id BIGINT UNSIGNED NOT NULL,
  proficiency_level VARCHAR(20) NOT NULL,
  years_experience DECIMAL(4,1),
  added_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (mentor_user_id, skill_id),
  CONSTRAINT fk_mentorskill_mentor FOREIGN KEY (mentor_user_id)
    REFERENCES mentor_profile(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_mentorskill_skill FOREIGN KEY (skill_id)
    REFERENCES skill(skill_id) ON DELETE RESTRICT,
  CONSTRAINT chk_mentorskill_exp CHECK (years_experience IS NULL OR years_experience >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.5 Student Domain Interest Association (M:N)
CREATE TABLE student_domain_interest (
  student_user_id BIGINT UNSIGNED NOT NULL,
  domain_id BIGINT UNSIGNED NOT NULL,
  priority_order SMALLINT NOT NULL,
  interest_notes TEXT,
  PRIMARY KEY (student_user_id, domain_id),
  UNIQUE KEY uq_student_domain_priority (student_user_id, priority_order),
  CONSTRAINT fk_studentdomain_student FOREIGN KEY (student_user_id)
    REFERENCES student_profile(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_studentdomain_domain FOREIGN KEY (domain_id)
    REFERENCES mentorship_domain(domain_id) ON DELETE RESTRICT,
  CONSTRAINT chk_studentdomain_priority CHECK (priority_order > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.6 Mentor Domain Expertise Association (M:N)
CREATE TABLE mentor_domain_expertise (
  mentor_user_id BIGINT UNSIGNED NOT NULL,
  domain_id BIGINT UNSIGNED NOT NULL,
  expertise_level VARCHAR(20) NOT NULL,
  years_experience DECIMAL(4,1),
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (mentor_user_id, domain_id),
  CONSTRAINT fk_mentordomain_mentor FOREIGN KEY (mentor_user_id)
    REFERENCES mentor_profile(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_mentordomain_domain FOREIGN KEY (domain_id)
    REFERENCES mentorship_domain(domain_id) ON DELETE RESTRICT,
  CONSTRAINT chk_mentordomain_exp CHECK (years_experience IS NULL OR years_experience >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Requests, Recommendations and Allocations

-- 4.1 Mentorship Request
CREATE TABLE mentorship_request (
  request_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  student_user_id BIGINT UNSIGNED NOT NULL,
  mentor_user_id BIGINT UNSIGNED NOT NULL,
  domain_id BIGINT UNSIGNED NOT NULL,
  request_message TEXT NOT NULL,
  career_goal_snapshot TEXT,
  request_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  submitted_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  decision_at DATETIME(6),
  decided_by_user_id BIGINT UNSIGNED,
  decision_reason VARCHAR(120),
  response_note TEXT,
  idempotency_key VARCHAR(100) UNIQUE,
  pending_request_key VARCHAR(100)
    GENERATED ALWAYS AS
      (CASE WHEN request_status = 'PENDING'
            THEN CONCAT(student_user_id, ':', mentor_user_id, ':', domain_id)
            ELSE NULL END) STORED,
  CONSTRAINT fk_request_student FOREIGN KEY (student_user_id)
    REFERENCES student_profile(user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_request_mentor FOREIGN KEY (mentor_user_id)
    REFERENCES mentor_profile(user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_request_domain FOREIGN KEY (domain_id)
    REFERENCES mentorship_domain(domain_id) ON DELETE RESTRICT,
  CONSTRAINT fk_request_decider FOREIGN KEY (decided_by_user_id)
    REFERENCES user_account(user_id) ON DELETE RESTRICT,
  CONSTRAINT chk_request_status
    CHECK (request_status IN ('PENDING','ACCEPTED','REJECTED','CANCELLED')),
  CONSTRAINT chk_request_decision_metadata
    CHECK ((request_status = 'PENDING' AND decision_at IS NULL AND decided_by_user_id IS NULL)
        OR (request_status <> 'PENDING' AND decision_at IS NOT NULL AND decided_by_user_id IS NOT NULL)),
  UNIQUE KEY uq_pending_request_guard (pending_request_key),
  INDEX ix_request_student_status (student_user_id, request_status, submitted_at),
  INDEX ix_request_mentor_status (mentor_user_id, request_status, submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4.2 Recommendation Run
CREATE TABLE recommendation_run (
  run_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  student_user_id BIGINT UNSIGNED NOT NULL,
  input_goal TEXT,
  algorithm_version VARCHAR(40) NOT NULL,
  profile_version VARCHAR(40),
  filter_snapshot JSON,
  executed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_recrun_student FOREIGN KEY (student_user_id)
    REFERENCES student_profile(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4.3 Recommended Mentor
CREATE TABLE recommended_mentor (
  recommendation_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  run_id BIGINT UNSIGNED NOT NULL,
  mentor_user_id BIGINT UNSIGNED NOT NULL,
  rank_position SMALLINT NOT NULL,
  score DECIMAL(7,4) NOT NULL,
  eligibility_status VARCHAR(20) NOT NULL,
  explanation_text TEXT,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY uq_rec_run_mentor (run_id, mentor_user_id),
  UNIQUE KEY uq_rec_run_rank (run_id, rank_position),
  CONSTRAINT fk_recmentor_run FOREIGN KEY (run_id)
    REFERENCES recommendation_run(run_id) ON DELETE CASCADE,
  CONSTRAINT fk_recmentor_mentor FOREIGN KEY (mentor_user_id)
    REFERENCES mentor_profile(user_id) ON DELETE RESTRICT,
  CONSTRAINT chk_recmentor_rank CHECK (rank_position > 0),
  CONSTRAINT chk_recmentor_score CHECK (score >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4.4 Mentor Allocation
CREATE TABLE mentor_allocation (
  allocation_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  request_id BIGINT UNSIGNED NOT NULL UNIQUE,
  allocation_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  allocated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  ended_at DATETIME(6),
  ended_by_user_id BIGINT UNSIGNED,
  termination_reason TEXT,
  CONSTRAINT fk_allocation_request FOREIGN KEY (request_id)
    REFERENCES mentorship_request(request_id) ON DELETE RESTRICT,
  CONSTRAINT fk_allocation_ender FOREIGN KEY (ended_by_user_id)
    REFERENCES user_account(user_id) ON DELETE RESTRICT,
  CONSTRAINT chk_allocation_status CHECK (allocation_status IN ('ACTIVE','ENDED')),
  CONSTRAINT chk_allocation_end CHECK
    ((allocation_status = 'ACTIVE' AND ended_at IS NULL)
      OR (allocation_status = 'ENDED' AND ended_at IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Availability, Booking and Session

-- 5.1 Mentor Availability
CREATE TABLE mentor_availability (
  availability_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  mentor_user_id BIGINT UNSIGNED NOT NULL,
  starts_at DATETIME(6) NOT NULL,
  ends_at DATETIME(6) NOT NULL,
  slot_status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY uq_mentor_slot_interval (mentor_user_id, starts_at, ends_at),
  CONSTRAINT fk_availability_mentor FOREIGN KEY (mentor_user_id)
    REFERENCES mentor_profile(user_id) ON DELETE RESTRICT,
  CONSTRAINT chk_slot_interval CHECK (ends_at > starts_at),
  CONSTRAINT chk_slot_status CHECK (slot_status IN ('OPEN','BOOKED','BLOCKED','EXPIRED')),
  INDEX ix_availability_mentor_time (mentor_user_id, starts_at, slot_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.2 Booking
CREATE TABLE booking (
  booking_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  allocation_id BIGINT UNSIGNED NOT NULL,
  availability_id BIGINT UNSIGNED NOT NULL,
  booking_type VARCHAR(30) NOT NULL DEFAULT 'MENTORSHIP',
  booking_status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED',
  booked_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  cancelled_at DATETIME(6),
  cancelled_by_user_id BIGINT UNSIGNED,
  cancellation_reason TEXT,
  idempotency_key VARCHAR(100) NOT NULL UNIQUE,
  active_availability_id BIGINT UNSIGNED
    GENERATED ALWAYS AS
      (CASE WHEN booking_status = 'CONFIRMED'
            THEN availability_id ELSE NULL END) STORED,
  UNIQUE KEY uq_booking_active_slot (active_availability_id),
  CONSTRAINT fk_booking_allocation FOREIGN KEY (allocation_id)
    REFERENCES mentor_allocation(allocation_id) ON DELETE RESTRICT,
  CONSTRAINT fk_booking_availability FOREIGN KEY (availability_id)
    REFERENCES mentor_availability(availability_id) ON DELETE RESTRICT,
  CONSTRAINT fk_booking_canceller FOREIGN KEY (cancelled_by_user_id)
    REFERENCES user_account(user_id) ON DELETE RESTRICT,
  CONSTRAINT chk_booking_type CHECK (booking_type IN ('MENTORSHIP','MOCK_INTERVIEW')),
  CONSTRAINT chk_booking_status CHECK (booking_status IN ('CONFIRMED','CANCELLED')),
  CONSTRAINT chk_booking_cancellation CHECK
    ((booking_status = 'CONFIRMED' AND cancelled_at IS NULL)
      OR (booking_status = 'CANCELLED' AND cancelled_at IS NOT NULL)),
  INDEX ix_booking_allocation_status (allocation_id, booking_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.3 Mentorship Session
CREATE TABLE mentorship_session (
  session_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  booking_id BIGINT UNSIGNED NOT NULL UNIQUE,
  session_status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
  actual_start_at DATETIME(6),
  actual_end_at DATETIME(6),
  discussion_summary TEXT,
  performance_observations TEXT,
  improvement_areas TEXT,
  next_steps TEXT,
  preparation_recommendation TEXT,
  recorded_at DATETIME(6),
  recorded_by_user_id BIGINT UNSIGNED,
  CONSTRAINT fk_session_booking FOREIGN KEY (booking_id)
    REFERENCES booking(booking_id) ON DELETE RESTRICT,
  CONSTRAINT fk_session_recorder FOREIGN KEY (recorded_by_user_id)
    REFERENCES user_account(user_id) ON DELETE RESTRICT,
  CONSTRAINT chk_session_status CHECK (session_status IN ('SCHEDULED','COMPLETED','CANCELLED','NO_SHOW')),
  CONSTRAINT chk_session_times CHECK
    (actual_end_at IS NULL OR actual_start_at IS NULL OR actual_end_at >= actual_start_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5.4 Session Skill Assessment Junction
CREATE TABLE session_skill_assessment (
  session_id BIGINT UNSIGNED NOT NULL,
  skill_id BIGINT UNSIGNED NOT NULL,
  assessment_result VARCHAR(30) NOT NULL,
  assessment_notes TEXT,
  PRIMARY KEY (session_id, skill_id),
  CONSTRAINT fk_assess_session FOREIGN KEY (session_id)
    REFERENCES mentorship_session(session_id) ON DELETE CASCADE,
  CONSTRAINT fk_assess_skill FOREIGN KEY (skill_id)
    REFERENCES skill(skill_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Feedback, Reviews, Notifications and Audit

-- 6.1 Session Feedback (Two-Way Participant Feedback)
CREATE TABLE session_feedback (
  feedback_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  session_id BIGINT UNSIGNED NOT NULL,
  submitted_by_user_id BIGINT UNSIGNED NOT NULL,
  communication_rating TINYINT,
  helpfulness_rating TINYINT,
  technical_preparation_rating TINYINT,
  comments TEXT,
  submitted_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY uq_feedback_session_user (session_id, submitted_by_user_id),
  CONSTRAINT fk_feedback_session FOREIGN KEY (session_id)
    REFERENCES mentorship_session(session_id) ON DELETE CASCADE,
  CONSTRAINT fk_feedback_user FOREIGN KEY (submitted_by_user_id)
    REFERENCES user_account(user_id) ON DELETE RESTRICT,
  CONSTRAINT chk_comm_rating CHECK (communication_rating IS NULL OR communication_rating BETWEEN 1 AND 5),
  CONSTRAINT chk_help_rating CHECK (helpfulness_rating IS NULL OR helpfulness_rating BETWEEN 1 AND 5),
  CONSTRAINT chk_prep_rating CHECK (technical_preparation_rating IS NULL OR technical_preparation_rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6.2 Mentor Review (Student Review of Mentor for Completed Session)
CREATE TABLE mentor_review (
  review_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  session_id BIGINT UNSIGNED NOT NULL UNIQUE,
  rating TINYINT NOT NULL,
  review_text TEXT,
  submitted_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_review_session FOREIGN KEY (session_id)
    REFERENCES mentorship_session(session_id) ON DELETE RESTRICT,
  CONSTRAINT chk_mentor_review_rating CHECK (rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6.3 Notification Outbox (Transactional Outbox Pattern)
CREATE TABLE notification_outbox (
  outbox_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  aggregate_type VARCHAR(40) NOT NULL,
  aggregate_id BIGINT UNSIGNED NOT NULL,
  event_type VARCHAR(60) NOT NULL,
  payload_json JSON NOT NULL,
  delivery_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  attempt_count INT NOT NULL DEFAULT 0,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  next_attempt_at DATETIME(6),
  processed_at DATETIME(6),
  last_error TEXT,
  dedupe_key VARCHAR(160) NOT NULL UNIQUE,
  CONSTRAINT chk_outbox_status CHECK (delivery_status IN ('PENDING','PROCESSING','SENT','FAILED')),
  INDEX ix_outbox_delivery (delivery_status, next_attempt_at, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6.4 Notification (User Inboxes Fan-Out)
CREATE TABLE notification (
  notification_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  recipient_user_id BIGINT UNSIGNED NOT NULL,
  outbox_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(180) NOT NULL,
  body TEXT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  read_at DATETIME(6),
  UNIQUE KEY uq_notification_outbox_recipient (outbox_id, recipient_user_id),
  CONSTRAINT fk_notification_user FOREIGN KEY (recipient_user_id)
    REFERENCES user_account(user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_notification_outbox FOREIGN KEY (outbox_id)
    REFERENCES notification_outbox(outbox_id) ON DELETE RESTRICT,
  INDEX ix_notification_inbox (recipient_user_id, read_at, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6.5 Audit Log (Append-Only Administrative Audit Evidence)
CREATE TABLE audit_log (
  audit_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  actor_user_id BIGINT UNSIGNED,
  entity_type VARCHAR(50) NOT NULL,
  entity_id BIGINT UNSIGNED NOT NULL,
  action VARCHAR(40) NOT NULL,
  old_values_json JSON,
  new_values_json JSON,
  occurred_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  correlation_id VARCHAR(80),
  CONSTRAINT fk_audit_actor FOREIGN KEY (actor_user_id)
    REFERENCES user_account(user_id) ON DELETE SET NULL,
  INDEX ix_audit_entity (entity_type, entity_id, occurred_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

