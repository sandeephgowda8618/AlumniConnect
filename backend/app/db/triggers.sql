-- AlumniConnect Database Triggers (MySQL 8.x / InnoDB)
-- Aligned with AlumniConnect SQL Query Catalogue Final (TR01–TR04) & Relational Design

DELIMITER $$

-- ============================================================================
-- TR01: Audit Request Status Changes
-- Writes an immutable audit_log record whenever request_status transitions.
-- Uses @app_actor_user_id session variable when set by the application connection.
-- ============================================================================
DROP TRIGGER IF EXISTS trg_request_status_audit$$
CREATE TRIGGER trg_request_status_audit
AFTER UPDATE ON mentorship_request
FOR EACH ROW
BEGIN
    IF NOT (OLD.request_status <=> NEW.request_status) THEN
        INSERT INTO audit_log
            (entity_type, entity_id, action, actor_user_id,
             old_values_json, new_values_json, occurred_at)
        VALUES
            ('MENTORSHIP_REQUEST', OLD.request_id, 'STATUS_CHANGED',
             COALESCE(NEW.decided_by_user_id, @app_actor_user_id),
             JSON_OBJECT('request_status', OLD.request_status),
             JSON_OBJECT('request_status', NEW.request_status, 'decision_reason', NEW.decision_reason),
             CURRENT_TIMESTAMP(6));
    END IF;
END$$


-- ============================================================================
-- TR02: Reject Invalid Request-Status Transitions
-- Lifecycle invariant: PENDING -> ACCEPTED, REJECTED, or CANCELLED.
-- Terminal states cannot be altered.
-- ============================================================================
DROP TRIGGER IF EXISTS trg_request_status_guard$$
CREATE TRIGGER trg_request_status_guard
BEFORE UPDATE ON mentorship_request
FOR EACH ROW
BEGIN
    IF OLD.request_status <> NEW.request_status THEN
        IF OLD.request_status <> 'PENDING'
           OR NEW.request_status NOT IN ('ACCEPTED', 'REJECTED', 'CANCELLED') THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Invalid mentorship request status transition: Terminal states cannot be transitioned';
        END IF;
    END IF;
END$$


-- ============================================================================
-- TR03: Validate Session Status Transitions
-- Lifecycle invariant: SCHEDULED -> COMPLETED, CANCELLED, or NO_SHOW.
-- Terminal states cannot be altered.
-- ============================================================================
DROP TRIGGER IF EXISTS trg_session_status_guard$$
CREATE TRIGGER trg_session_status_guard
BEFORE UPDATE ON mentorship_session
FOR EACH ROW
BEGIN
    IF OLD.session_status <> NEW.session_status THEN
        IF OLD.session_status <> 'SCHEDULED'
           OR NEW.session_status NOT IN ('COMPLETED', 'CANCELLED', 'NO_SHOW') THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Invalid mentorship session status transition: Terminal states cannot be transitioned';
        END IF;
    END IF;
END$$


-- ============================================================================
-- TR04: Guard Mentor Review Integrity
-- Enforces that a review can only be inserted for a COMPLETED session.
-- ============================================================================
DROP TRIGGER IF EXISTS trg_mentor_review_validate$$
CREATE TRIGGER trg_mentor_review_validate
BEFORE INSERT ON mentor_review
FOR EACH ROW
BEGIN
    DECLARE v_session_status VARCHAR(20);

    SELECT session_status
      INTO v_session_status
    FROM mentorship_session
    WHERE session_id = NEW.session_id;

    IF v_session_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Referenced mentorship session does not exist';
    END IF;

    IF v_session_status <> 'COMPLETED' THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Review must reference a COMPLETED session';
    END IF;
END$$

DELIMITER ;

