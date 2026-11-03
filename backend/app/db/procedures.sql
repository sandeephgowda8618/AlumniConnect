-- AlumniConnect Authoritative Stored Procedures (MySQL 8.x / InnoDB)
-- Aligned with AlumniConnect SQL Query Catalogue Final (SP01–SP05)
-- Adheres strictly to Relational Design Specification Version 1.2 column names and constraints.

DELIMITER $$

-- ============================================================================
-- SP01: Accept a Mentorship Request and Create Allocation Atomically
-- ============================================================================
DROP PROCEDURE IF EXISTS sp_accept_mentorship_request$$
CREATE PROCEDURE sp_accept_mentorship_request(
    IN p_request_id BIGINT UNSIGNED,
    IN p_mentor_user_id BIGINT UNSIGNED,
    IN p_actor_user_id BIGINT UNSIGNED
)
BEGIN
    DECLARE v_student_user_id BIGINT UNSIGNED;
    DECLARE v_req_mentor_user_id BIGINT UNSIGNED;
    DECLARE v_request_status VARCHAR(20);
    DECLARE v_mentor_account_status VARCHAR(20);
    DECLARE v_accepting_requests BOOLEAN;
    DECLARE v_max_mentees SMALLINT;
    DECLARE v_active_mentees_count INT DEFAULT 0;
    DECLARE v_existing_active_alloc INT DEFAULT 0;
    DECLARE v_new_allocation_id BIGINT UNSIGNED;
    DECLARE v_dedupe_key VARCHAR(160);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Lock and inspect the mentorship request
    SELECT student_user_id, mentor_user_id, request_status
      INTO v_student_user_id, v_req_mentor_user_id, v_request_status
    FROM mentorship_request
    WHERE request_id = p_request_id
    FOR UPDATE;

    IF v_req_mentor_user_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Mentorship request not found';
    END IF;

    IF v_req_mentor_user_id <> p_mentor_user_id THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Mentorship request is not addressed to this mentor';
    END IF;

    IF v_request_status <> 'PENDING' THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Request is not in PENDING status';
    END IF;

    -- 2. Verify actor identity matches the mentor's user account
    IF p_mentor_user_id <> p_actor_user_id THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Only the addressed mentor may accept this request';
    END IF;

    -- 3. Lock and inspect mentor profile and account status
    SELECT mp.accepting_requests, mp.max_active_mentees, ua.account_status
      INTO v_accepting_requests, v_max_mentees, v_mentor_account_status
    FROM mentor_profile AS mp
    JOIN user_account AS ua ON ua.user_id = mp.user_id
    WHERE mp.user_id = p_mentor_user_id
    FOR UPDATE;

    IF v_mentor_account_status <> 'ACTIVE' THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Mentor account is not active';
    END IF;

    -- 4. Check active mentee capacity
    SELECT COUNT(*)
      INTO v_active_mentees_count
    FROM mentor_allocation AS ma
    JOIN mentorship_request AS mr ON mr.request_id = ma.request_id
    WHERE mr.mentor_user_id = p_mentor_user_id
      AND ma.allocation_status = 'ACTIVE';

    IF v_active_mentees_count >= v_max_mentees THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Mentor has reached maximum active mentee capacity';
    END IF;

    -- 5. Check if an active allocation already exists between this student and mentor
    SELECT COUNT(*)
      INTO v_existing_active_alloc
    FROM mentor_allocation AS ma
    JOIN mentorship_request AS mr ON mr.request_id = ma.request_id
    WHERE mr.student_user_id = v_student_user_id
      AND mr.mentor_user_id = p_mentor_user_id
      AND ma.allocation_status = 'ACTIVE';

    IF v_existing_active_alloc > 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'An active allocation already exists for this student and mentor';
    END IF;

    -- 6. Insert new mentor allocation
    INSERT INTO mentor_allocation
        (request_id, allocation_status, allocated_at)
    VALUES
        (p_request_id, 'ACTIVE', CURRENT_TIMESTAMP(6));

    SET v_new_allocation_id = LAST_INSERT_ID();

    -- 7. Update mentorship request status to ACCEPTED
    UPDATE mentorship_request
    SET request_status = 'ACCEPTED',
        decision_at = CURRENT_TIMESTAMP(6),
        decided_by_user_id = p_actor_user_id,
        decision_reason = 'Accepted by mentor'
    WHERE request_id = p_request_id;

    -- 8. Write transactional outbox event
    SET v_dedupe_key = CONCAT('outbox:req_accepted:', p_request_id, ':', UNIX_TIMESTAMP());
    INSERT INTO notification_outbox
        (aggregate_type, aggregate_id, event_type, payload_json, delivery_status, dedupe_key, created_at)
    VALUES
        ('MENTORSHIP_REQUEST', p_request_id, 'MENTORSHIP_REQUEST_ACCEPTED',
         JSON_OBJECT(
             'request_id', p_request_id,
             'allocation_id', v_new_allocation_id,
             'student_user_id', v_student_user_id,
             'mentor_user_id', p_mentor_user_id,
             'actor_user_id', p_actor_user_id
         ),
         'PENDING', v_dedupe_key, CURRENT_TIMESTAMP(6));

    COMMIT;
END$$


-- ============================================================================
-- SP02: Create an Atomic Booking with Row Locking and Concurrency Protection
-- ============================================================================
DROP PROCEDURE IF EXISTS sp_create_booking$$
CREATE PROCEDURE sp_create_booking(
    IN p_actor_user_id BIGINT UNSIGNED,
    IN p_availability_id BIGINT UNSIGNED,
    IN p_booking_type VARCHAR(30),
    IN p_allocation_id BIGINT UNSIGNED,
    IN p_idempotency_key VARCHAR(100),
    OUT p_booking_id BIGINT UNSIGNED
)
BEGIN
    DECLARE v_student_user_id BIGINT UNSIGNED;
    DECLARE v_mentor_user_id BIGINT UNSIGNED;
    DECLARE v_slot_starts_at DATETIME(6);
    DECLARE v_slot_ends_at DATETIME(6);
    DECLARE v_slot_status VARCHAR(20);
    DECLARE v_mentor_account_status VARCHAR(20);
    DECLARE v_alloc_status VARCHAR(20);
    DECLARE v_alloc_student_id BIGINT UNSIGNED;
    DECLARE v_alloc_mentor_id BIGINT UNSIGNED;
    DECLARE v_student_conflicts INT DEFAULT 0;
    DECLARE v_mentor_conflicts INT DEFAULT 0;
    DECLARE v_existing_booking_id BIGINT UNSIGNED;
    DECLARE v_dedupe_key VARCHAR(160);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 0. Check Idempotency Key first
    SELECT booking_id INTO v_existing_booking_id
    FROM booking
    WHERE idempotency_key = p_idempotency_key;

    IF v_existing_booking_id IS NOT NULL THEN
        SET p_booking_id = v_existing_booking_id;
        COMMIT;
    ELSE
        -- 1. Lock and verify the authenticated student caller
        SELECT sp.user_id
          INTO v_student_user_id
        FROM student_profile AS sp
        JOIN user_account AS ua ON ua.user_id = sp.user_id
        WHERE ua.user_id = p_actor_user_id
          AND ua.account_status = 'ACTIVE'
        FOR UPDATE;

        IF v_student_user_id IS NULL THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Authenticated caller is not an active student';
        END IF;

        -- 2. Lock and verify availability slot
        SELECT mentor_user_id, starts_at, ends_at, slot_status
          INTO v_mentor_user_id, v_slot_starts_at, v_slot_ends_at, v_slot_status
        FROM mentor_availability
        WHERE availability_id = p_availability_id
        FOR UPDATE;

        IF v_mentor_user_id IS NULL THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Availability slot not found';
        END IF;

        IF v_slot_status <> 'OPEN' THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Availability slot is not open for booking';
        END IF;

        IF v_slot_starts_at <= CURRENT_TIMESTAMP(6) THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Cannot book a slot in the past';
        END IF;

        -- 3. Lock and verify mentor profile and account
        SELECT ua.account_status
          INTO v_mentor_account_status
        FROM mentor_profile AS mp
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        WHERE mp.user_id = v_mentor_user_id
        FOR UPDATE;

        IF v_mentor_account_status <> 'ACTIVE' THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Mentor account is not active';
        END IF;

        -- 4. Verify booking type
        IF p_booking_type IS NULL OR p_booking_type NOT IN ('MENTORSHIP', 'MOCK_INTERVIEW') THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Invalid booking type. Must be MENTORSHIP or MOCK_INTERVIEW';
        END IF;

        -- 5. Lock and verify allocation (mandatory in Core Release 1)
        IF p_allocation_id IS NULL THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Active allocation is required for booking';
        END IF;

        SELECT ma.allocation_status, mr.student_user_id, mr.mentor_user_id
          INTO v_alloc_status, v_alloc_student_id, v_alloc_mentor_id
        FROM mentor_allocation AS ma
        JOIN mentorship_request AS mr ON mr.request_id = ma.request_id
        WHERE ma.allocation_id = p_allocation_id
        FOR UPDATE;

        IF v_alloc_status IS NULL OR v_alloc_status <> 'ACTIVE' THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Allocation is not active';
        END IF;

        IF v_alloc_student_id <> v_student_user_id OR v_alloc_mentor_id <> v_mentor_user_id THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Allocation does not match student and mentor participants';
        END IF;

        -- 6. Check for student schedule conflicts (overlapping confirmed bookings)
        SELECT COUNT(*)
          INTO v_student_conflicts
        FROM booking AS b
        JOIN mentor_availability AS ma ON ma.availability_id = b.availability_id
        JOIN mentor_allocation AS alloc ON alloc.allocation_id = b.allocation_id
        JOIN mentorship_request AS req ON req.request_id = alloc.request_id
        WHERE req.student_user_id = v_student_user_id
          AND b.booking_status = 'CONFIRMED'
          AND ma.starts_at < v_slot_ends_at
          AND ma.ends_at > v_slot_starts_at;

        IF v_student_conflicts > 0 THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Student has an overlapping confirmed booking';
        END IF;

        -- 7. Check for mentor schedule conflicts
        SELECT COUNT(*)
          INTO v_mentor_conflicts
        FROM booking AS b
        JOIN mentor_availability AS ma ON ma.availability_id = b.availability_id
        WHERE ma.mentor_user_id = v_mentor_user_id
          AND b.booking_status = 'CONFIRMED'
          AND ma.starts_at < v_slot_ends_at
          AND ma.ends_at > v_slot_starts_at;

        IF v_mentor_conflicts > 0 THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Mentor has an overlapping confirmed booking';
        END IF;

        -- 8. Insert confirmed booking
        INSERT INTO booking
            (allocation_id, availability_id, booking_type, booking_status, idempotency_key, booked_at)
        VALUES
            (p_allocation_id, p_availability_id, p_booking_type, 'CONFIRMED', p_idempotency_key, CURRENT_TIMESTAMP(6));

        SET p_booking_id = LAST_INSERT_ID();

        -- 9. Mark slot as BOOKED
        UPDATE mentor_availability
        SET slot_status = 'BOOKED'
        WHERE availability_id = p_availability_id;

        -- 10. Create planned scheduled mentorship session
        INSERT INTO mentorship_session
            (booking_id, session_status)
        VALUES
            (p_booking_id, 'SCHEDULED');

        -- 11. Write outbox event
        SET v_dedupe_key = CONCAT('outbox:booking_created:', p_booking_id, ':', UNIX_TIMESTAMP());
        INSERT INTO notification_outbox
            (aggregate_type, aggregate_id, event_type, payload_json, delivery_status, dedupe_key, created_at)
        VALUES
            ('BOOKING', p_booking_id, 'BOOKING_CONFIRMED',
             JSON_OBJECT(
                 'booking_id', p_booking_id,
                 'allocation_id', p_allocation_id,
                 'availability_id', p_availability_id,
                 'student_user_id', v_student_user_id,
                 'mentor_user_id', v_mentor_user_id,
                 'starts_at', DATE_FORMAT(v_slot_starts_at, '%Y-%m-%dT%H:%i:%sZ'),
                 'ends_at', DATE_FORMAT(v_slot_ends_at, '%Y-%m-%dT%H:%i:%sZ')
             ),
             'PENDING', v_dedupe_key, CURRENT_TIMESTAMP(6));

        COMMIT;
    END IF;
END$$


-- ============================================================================
-- SP03: Cancel a Booking, Retain History and Reopen Slot
-- ============================================================================
DROP PROCEDURE IF EXISTS sp_cancel_booking$$
CREATE PROCEDURE sp_cancel_booking(
    IN p_booking_id BIGINT UNSIGNED,
    IN p_actor_user_id BIGINT UNSIGNED,
    IN p_reason TEXT
)
BEGIN
    DECLARE v_student_user_id BIGINT UNSIGNED;
    DECLARE v_mentor_user_id BIGINT UNSIGNED;
    DECLARE v_availability_id BIGINT UNSIGNED;
    DECLARE v_booking_status VARCHAR(20);
    DECLARE v_starts_at DATETIME(6);
    DECLARE v_dedupe_key VARCHAR(160);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Lock and inspect booking, availability, and participants
    SELECT b.booking_status, b.availability_id, ma.starts_at, req.student_user_id, req.mentor_user_id
      INTO v_booking_status, v_availability_id, v_starts_at, v_student_user_id, v_mentor_user_id
    FROM booking AS b
    JOIN mentor_availability AS ma ON ma.availability_id = b.availability_id
    JOIN mentor_allocation AS alloc ON alloc.allocation_id = b.allocation_id
    JOIN mentorship_request AS req ON req.request_id = alloc.request_id
    WHERE b.booking_id = p_booking_id
    FOR UPDATE;

    IF v_booking_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Booking not found';
    END IF;

    IF v_booking_status <> 'CONFIRMED' THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Only CONFIRMED bookings may be cancelled';
    END IF;

    -- 2. Verify caller is either the student participant, the mentor participant, or an administrator
    IF p_actor_user_id <> v_student_user_id AND p_actor_user_id <> v_mentor_user_id THEN
        -- Check if administrator
        IF NOT EXISTS (
            SELECT 1 FROM user_account AS ua
            JOIN role AS r ON r.role_id = ua.role_id
            WHERE ua.user_id = p_actor_user_id AND r.role_code = 'ADMINISTRATOR'
        ) THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Not authorized to cancel this booking';
        END IF;
    END IF;

    -- 2.1 Enforce 2-hour cancellation window cutoff (Business Rules BR-T16, BR-T17)
    IF v_starts_at <= DATE_ADD(CURRENT_TIMESTAMP(6), INTERVAL 2 HOUR) THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Cancellation window closed. Bookings must be cancelled at least 2 hours in advance.';
    END IF;

    -- 3. Update booking status to CANCELLED
    UPDATE booking
    SET booking_status = 'CANCELLED',
        cancelled_at = CURRENT_TIMESTAMP(6),
        cancelled_by_user_id = p_actor_user_id,
        cancellation_reason = p_reason
    WHERE booking_id = p_booking_id;

    -- 4. Update scheduled session to CANCELLED
    UPDATE mentorship_session
    SET session_status = 'CANCELLED'
    WHERE booking_id = p_booking_id
      AND session_status = 'SCHEDULED';

    -- 5. Reopen availability slot if in the future
    IF v_starts_at > CURRENT_TIMESTAMP(6) THEN
        UPDATE mentor_availability
        SET slot_status = 'OPEN'
        WHERE availability_id = v_availability_id;
    END IF;

    -- 6. Write outbox event
    SET v_dedupe_key = CONCAT('outbox:booking_cancelled:', p_booking_id, ':', UNIX_TIMESTAMP());
    INSERT INTO notification_outbox
        (aggregate_type, aggregate_id, event_type, payload_json, delivery_status, dedupe_key, created_at)
    VALUES
        ('BOOKING', p_booking_id, 'BOOKING_CANCELLED',
         JSON_OBJECT(
             'booking_id', p_booking_id,
             'availability_id', v_availability_id,
             'cancelled_by_user_id', p_actor_user_id,
             'student_user_id', v_student_user_id,
             'mentor_user_id', v_mentor_user_id,
             'reason', p_reason
         ),
         'PENDING', v_dedupe_key, CURRENT_TIMESTAMP(6));

    COMMIT;
END$$


-- ============================================================================
-- SP04: Record Actual Session Outcome
-- ============================================================================
DROP PROCEDURE IF EXISTS sp_record_session_outcome$$
CREATE PROCEDURE sp_record_session_outcome(
    IN p_session_id BIGINT UNSIGNED,
    IN p_actor_user_id BIGINT UNSIGNED,
    IN p_new_status VARCHAR(20),
    IN p_actual_start_at DATETIME(6),
    IN p_actual_end_at DATETIME(6),
    IN p_discussion_summary TEXT,
    IN p_performance_observations TEXT,
    IN p_improvement_areas TEXT,
    IN p_next_steps TEXT,
    IN p_preparation_recommendation TEXT
)
BEGIN
    DECLARE v_mentor_user_id BIGINT UNSIGNED;
    DECLARE v_student_user_id BIGINT UNSIGNED;
    DECLARE v_booking_id BIGINT UNSIGNED;
    DECLARE v_current_session_status VARCHAR(20);
    DECLARE v_dedupe_key VARCHAR(160);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Lock and verify session and mentor identity
    SELECT ms.session_status, ms.booking_id, req.mentor_user_id, req.student_user_id
      INTO v_current_session_status, v_booking_id, v_mentor_user_id, v_student_user_id
    FROM mentorship_session AS ms
    JOIN booking AS b ON b.booking_id = ms.booking_id
    JOIN mentor_allocation AS alloc ON alloc.allocation_id = b.allocation_id
    JOIN mentorship_request AS req ON req.request_id = alloc.request_id
    WHERE ms.session_id = p_session_id
    FOR UPDATE;

    IF v_current_session_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Session not found';
    END IF;

    IF v_current_session_status <> 'SCHEDULED' THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Session outcome can only be recorded for SCHEDULED sessions';
    END IF;

    IF p_actor_user_id <> v_mentor_user_id THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Only the assigned mentor may record the session outcome';
    END IF;

    IF p_new_status NOT IN ('COMPLETED', 'CANCELLED', 'NO_SHOW') THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'New status must be COMPLETED, CANCELLED, or NO_SHOW';
    END IF;

    -- 2. Update session record
    UPDATE mentorship_session
    SET session_status = p_new_status,
        actual_start_at = p_actual_start_at,
        actual_end_at = p_actual_end_at,
        discussion_summary = p_discussion_summary,
        performance_observations = p_performance_observations,
        improvement_areas = p_improvement_areas,
        next_steps = p_next_steps,
        preparation_recommendation = p_preparation_recommendation,
        recorded_at = CURRENT_TIMESTAMP(6),
        recorded_by_user_id = p_actor_user_id
    WHERE session_id = p_session_id;

    -- 3. Emit outbox event
    SET v_dedupe_key = CONCAT('outbox:session_outcome:', p_session_id, ':', UNIX_TIMESTAMP());
    INSERT INTO notification_outbox
        (aggregate_type, aggregate_id, event_type, payload_json, delivery_status, dedupe_key, created_at)
    VALUES
        ('MENTORSHIP_SESSION', p_session_id, 'SESSION_OUTCOME_RECORDED',
         JSON_OBJECT(
             'session_id', p_session_id,
             'booking_id', v_booking_id,
             'status', p_new_status,
             'student_user_id', v_student_user_id,
             'mentor_user_id', v_mentor_user_id,
             'recorded_by_user_id', p_actor_user_id
         ),
         'PENDING', v_dedupe_key, CURRENT_TIMESTAMP(6));

    COMMIT;
END$$


-- ============================================================================
-- SP05: Submit a Mentor Review with Validation
-- ============================================================================
DROP PROCEDURE IF EXISTS sp_submit_mentor_review$$
CREATE PROCEDURE sp_submit_mentor_review(
    IN p_session_id BIGINT UNSIGNED,
    IN p_actor_user_id BIGINT UNSIGNED,
    IN p_rating TINYINT,
    IN p_review_text TEXT,
    OUT p_review_id BIGINT UNSIGNED
)
BEGIN
    DECLARE v_session_status VARCHAR(20);
    DECLARE v_booking_student_id BIGINT UNSIGNED;
    DECLARE v_mentor_user_id BIGINT UNSIGNED;
    DECLARE v_dedupe_key VARCHAR(160);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Lock and verify session
    SELECT ms.session_status, req.student_user_id, req.mentor_user_id
      INTO v_session_status, v_booking_student_id, v_mentor_user_id
    FROM mentorship_session AS ms
    JOIN booking AS b ON b.booking_id = ms.booking_id
    JOIN mentor_allocation AS alloc ON alloc.allocation_id = b.allocation_id
    JOIN mentorship_request AS req ON req.request_id = alloc.request_id
    WHERE ms.session_id = p_session_id
    FOR UPDATE;

    IF v_session_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Session not found';
    END IF;

    IF v_session_status <> 'COMPLETED' THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Reviews can only be submitted for COMPLETED sessions';
    END IF;

    IF p_actor_user_id <> v_booking_student_id THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Only the participating student may review the mentor for this session';
    END IF;

    IF p_rating IS NULL OR p_rating < 1 OR p_rating > 5 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Rating must be an integer between 1 and 5';
    END IF;

    -- 2. Insert mentor review (UNIQUE constraint on session_id prevents duplicates)
    INSERT INTO mentor_review
        (session_id, rating, review_text, submitted_at)
    VALUES
        (p_session_id, p_rating, p_review_text, CURRENT_TIMESTAMP(6));

    SET p_review_id = LAST_INSERT_ID();

    -- 3. Emit outbox event
    SET v_dedupe_key = CONCAT('outbox:review_submitted:', p_review_id, ':', UNIX_TIMESTAMP());
    INSERT INTO notification_outbox
        (aggregate_type, aggregate_id, event_type, payload_json, delivery_status, dedupe_key, created_at)
    VALUES
        ('MENTOR_REVIEW', p_review_id, 'MENTOR_REVIEW_SUBMITTED',
         JSON_OBJECT(
             'review_id', p_review_id,
             'session_id', p_session_id,
             'student_user_id', p_actor_user_id,
             'mentor_user_id', v_mentor_user_id,
             'rating', p_rating
         ),
         'PENDING', v_dedupe_key, CURRENT_TIMESTAMP(6));

    COMMIT;
END$$

DELIMITER ;

