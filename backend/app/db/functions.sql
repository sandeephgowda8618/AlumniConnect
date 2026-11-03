-- AlumniConnect Stored Functions (MySQL 8.x / InnoDB)
-- Aligned with AlumniConnect SQL Query Catalogue Final (F01)

DELIMITER $$

-- F01: Convert a numeric rating to a descriptive label
DROP FUNCTION IF EXISTS fn_rating_label$$
CREATE FUNCTION fn_rating_label(p_rating DECIMAL(3,2))
RETURNS VARCHAR(20)
DETERMINISTIC
NO SQL
BEGIN
    RETURN CASE
        WHEN p_rating IS NULL THEN 'NOT_RATED'
        WHEN p_rating >= 4.50 THEN 'EXCELLENT'
        WHEN p_rating >= 4.00 THEN 'VERY_GOOD'
        WHEN p_rating >= 3.00 THEN 'GOOD'
        WHEN p_rating >= 2.00 THEN 'NEEDS_REVIEW'
        ELSE 'POOR'
    END;
END$$

DELIMITER ;

