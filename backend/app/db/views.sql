-- AlumniConnect Database Views (MySQL 8.x / InnoDB)
-- Aligned with AlumniConnect SQL Query Catalogue Final (V01–V04) & Relational Design

-- V01: Public Mentor Directory
-- Exposes discoverable professional attributes only. Excludes private emails, passwords, and sensitive identifiers.
CREATE OR REPLACE VIEW v_public_mentor_directory AS
SELECT
    mp.user_id AS mentor_user_id,
    ua.display_name AS full_name,
    mp.job_title,
    mp.years_experience,
    mp.max_active_mentees,
    mp.accepting_requests,
    mp.professional_summary AS biography,
    c.company_id,
    c.company_name,
    c.industry,
    d.department_id,
    d.department_name,
    d.institution_name
FROM mentor_profile AS mp
JOIN user_account AS ua
  ON ua.user_id = mp.user_id
LEFT JOIN company AS c
  ON c.company_id = mp.current_company_id
LEFT JOIN department AS d
  ON d.department_id = mp.alumni_department_id
WHERE ua.account_status = 'ACTIVE'
  AND mp.accepting_requests = TRUE;

-- V02: Mentor Review & Rating Summary
-- Aggregates review metrics per mentor profile based on confirmed student reviews.
CREATE OR REPLACE VIEW v_mentor_rating_summary AS
SELECT
    mp.user_id AS mentor_user_id,
    ua.display_name AS full_name,
    COUNT(mr.review_id) AS review_count,
    ROUND(AVG(mr.rating), 2) AS average_rating,
    MAX(mr.submitted_at) AS latest_review_at
FROM mentor_profile AS mp
JOIN user_account AS ua
  ON ua.user_id = mp.user_id
LEFT JOIN mentor_availability AS ma
  ON ma.mentor_user_id = mp.user_id
LEFT JOIN booking AS b
  ON b.availability_id = ma.availability_id
LEFT JOIN mentorship_session AS ms
  ON ms.booking_id = b.booking_id
LEFT JOIN mentor_review AS mr
  ON mr.session_id = ms.session_id
GROUP BY mp.user_id, ua.display_name;

-- V03: Student Request and Allocation Summary
-- Aggregates request counts and allocation counts independently to avoid cartesian inflation.
CREATE OR REPLACE VIEW v_student_mentorship_summary AS
SELECT
    sp.user_id AS student_user_id,
    sp.student_number,
    ua.display_name AS student_name,
    d.department_name,
    COALESCE(r.request_count, 0) AS total_requests,
    COALESCE(r.pending_request_count, 0) AS pending_requests,
    COALESCE(r.accepted_request_count, 0) AS accepted_requests,
    COALESCE(a.allocation_count, 0) AS total_allocations,
    COALESCE(a.active_allocation_count, 0) AS active_allocations
FROM student_profile AS sp
JOIN user_account AS ua
  ON ua.user_id = sp.user_id
LEFT JOIN department AS d
  ON d.department_id = sp.department_id
LEFT JOIN (
    SELECT
        student_user_id,
        COUNT(*) AS request_count,
        SUM(CASE WHEN request_status = 'PENDING' THEN 1 ELSE 0 END) AS pending_request_count,
        SUM(CASE WHEN request_status = 'ACCEPTED' THEN 1 ELSE 0 END) AS accepted_request_count
    FROM mentorship_request
    GROUP BY student_user_id
) AS r ON r.student_user_id = sp.user_id
LEFT JOIN (
    SELECT
        mrq.student_user_id,
        COUNT(ma.allocation_id) AS allocation_count,
        SUM(CASE WHEN ma.allocation_status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_allocation_count
    FROM mentor_allocation AS ma
    JOIN mentorship_request AS mrq ON mrq.request_id = ma.request_id
    GROUP BY mrq.student_user_id
) AS a ON a.student_user_id = sp.user_id;

-- V04: Session Outcome Summary by Mentor
-- Provides administrative overview of session counts and outcomes per mentor.
CREATE OR REPLACE VIEW v_mentor_session_outcomes AS
SELECT
    mp.user_id AS mentor_user_id,
    ua.display_name AS mentor_name,
    COUNT(ms.session_id) AS total_sessions,
    SUM(CASE WHEN ms.session_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_sessions,
    SUM(CASE WHEN ms.session_status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_sessions,
    SUM(CASE WHEN ms.session_status = 'NO_SHOW' THEN 1 ELSE 0 END) AS no_show_sessions,
    SUM(CASE WHEN ms.session_status = 'SCHEDULED' THEN 1 ELSE 0 END) AS scheduled_sessions
FROM mentor_profile AS mp
JOIN user_account AS ua
  ON ua.user_id = mp.user_id
LEFT JOIN mentor_availability AS ma
  ON ma.mentor_user_id = mp.user_id
LEFT JOIN booking AS b
  ON b.availability_id = ma.availability_id
LEFT JOIN mentorship_session AS ms
  ON ms.booking_id = b.booking_id
GROUP BY mp.user_id, ua.display_name;

-- Helper View: Booking Details View
-- Conveniently resolves student, mentor, allocation, and slot details without denormalizing base tables.
CREATE OR REPLACE VIEW v_booking_details AS
SELECT
    b.booking_id,
    b.booking_type,
    b.booking_status,
    b.booked_at,
    b.cancelled_at,
    b.cancellation_reason,
    b.idempotency_key,
    -- Allocation & Participants
    b.allocation_id,
    alloc.allocation_status,
    req.student_user_id,
    stud_ua.display_name AS student_name,
    req.mentor_user_id,
    ment_ua.display_name AS mentor_name,
    -- Availability Slot & Schedule
    b.availability_id,
    avail.starts_at AS slot_starts_at,
    avail.ends_at AS slot_ends_at,
    avail.slot_status,
    -- Session info if created
    sess.session_id,
    sess.session_status,
    sess.actual_start_at,
    sess.actual_end_at
FROM booking AS b
JOIN mentor_allocation AS alloc ON alloc.allocation_id = b.allocation_id
JOIN mentorship_request AS req ON req.request_id = alloc.request_id
JOIN user_account AS stud_ua ON stud_ua.user_id = req.student_user_id
JOIN user_account AS ment_ua ON ment_ua.user_id = req.mentor_user_id
JOIN mentor_availability AS avail ON avail.availability_id = b.availability_id
LEFT JOIN mentorship_session AS sess ON sess.booking_id = b.booking_id;

