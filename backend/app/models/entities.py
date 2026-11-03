"""AlumniConnect Authoritative SQLAlchemy Entities
Defines all 25 relational tables according to the Relational Design Specification Version 1.2.
"""

from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, SmallInteger, String, Text, Boolean,
    DateTime, Numeric, ForeignKey, UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def pk_column():
    """Generates a cross-dialect primary key: BIGINT in MySQL, INTEGER in SQLite for autoincrement."""
    return Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)


# 1. Reference and Identity

class Role(Base):
    __tablename__ = "role"

    role_id = pk_column()
    role_code = Column(String(30), unique=True, nullable=False)
    role_name = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    users = relationship("UserAccount", back_populates="role")


class Department(Base):
    __tablename__ = "department"

    department_id = pk_column()
    department_code = Column(String(30), nullable=False)
    department_name = Column(String(120), nullable=False)
    institution_name = Column(String(160), nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_name", "department_code", name="uq_dept_institution_code"),
    )

    students = relationship("StudentProfile", back_populates="department")
    mentors = relationship("MentorProfile", back_populates="department")


class Company(Base):
    __tablename__ = "company"

    company_id = pk_column()
    company_name = Column(String(180), nullable=False)
    website_url = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)

    mentors = relationship("MentorProfile", back_populates="company")


class UserAccount(Base):
    __tablename__ = "user_account"

    user_id = pk_column()
    role_id = Column(BigInteger, ForeignKey("role.role_id", ondelete="RESTRICT"), nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(120), nullable=False)
    account_status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    role = relationship("Role", back_populates="users")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    mentor_profile = relationship("MentorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="recipient", cascade="all, delete-orphan")


# 2. Profiles

class StudentProfile(Base):
    __tablename__ = "student_profile"

    user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="RESTRICT"), primary_key=True)
    student_number = Column(String(50), unique=True, nullable=False)
    department_id = Column(BigInteger, ForeignKey("department.department_id", ondelete="RESTRICT"), nullable=False)
    programme = Column(String(120), nullable=False)
    batch_year = Column(SmallInteger, nullable=False)
    expected_graduation_year = Column(SmallInteger, nullable=True)
    career_goal = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)

    user = relationship("UserAccount", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    domain_interests = relationship("StudentDomainInterest", back_populates="student", cascade="all, delete-orphan")
    requests = relationship("MentorshipRequest", foreign_keys="MentorshipRequest.student_user_id", back_populates="student")


class MentorProfile(Base):
    __tablename__ = "mentor_profile"

    user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="RESTRICT"), primary_key=True)
    alumni_identifier = Column(String(60), unique=True, nullable=True)
    alumni_department_id = Column(BigInteger, ForeignKey("department.department_id", ondelete="RESTRICT"), nullable=False)
    current_company_id = Column(BigInteger, ForeignKey("company.company_id", ondelete="RESTRICT"), nullable=True)
    job_title = Column(String(120), nullable=False)
    years_experience = Column(Numeric(4, 1), default=0.0, nullable=False)
    max_active_mentees = Column(SmallInteger, default=1, nullable=False)
    accepting_requests = Column(Boolean, default=True, nullable=False)
    professional_summary = Column(Text, nullable=True)

    user = relationship("UserAccount", back_populates="mentor_profile")
    department = relationship("Department", back_populates="mentors")
    company = relationship("Company", back_populates="mentors")
    skills = relationship("MentorSkill", back_populates="mentor", cascade="all, delete-orphan")
    domain_expertises = relationship("MentorDomainExpertise", back_populates="mentor", cascade="all, delete-orphan")
    availabilities = relationship("MentorAvailability", back_populates="mentor")
    requests = relationship("MentorshipRequest", foreign_keys="MentorshipRequest.mentor_user_id", back_populates="mentor")


# 3. Skills and Domains

class Skill(Base):
    __tablename__ = "skill"

    skill_id = pk_column()
    skill_name = Column(String(100), unique=True, nullable=False)
    category = Column(String(80), nullable=True)
    description = Column(Text, nullable=True)


class MentorshipDomain(Base):
    __tablename__ = "mentorship_domain"

    domain_id = pk_column()
    domain_name = Column(String(120), unique=True, nullable=False)
    description = Column(Text, nullable=True)


class StudentSkill(Base):
    __tablename__ = "student_skill"

    student_user_id = Column(BigInteger, ForeignKey("student_profile.user_id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(BigInteger, ForeignKey("skill.skill_id", ondelete="RESTRICT"), primary_key=True)
    proficiency_level = Column(String(20), nullable=False)
    years_experience = Column(Numeric(4, 1), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="skills")
    skill = relationship("Skill")


class MentorSkill(Base):
    __tablename__ = "mentor_skill"

    mentor_user_id = Column(BigInteger, ForeignKey("mentor_profile.user_id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(BigInteger, ForeignKey("skill.skill_id", ondelete="RESTRICT"), primary_key=True)
    proficiency_level = Column(String(20), nullable=False)
    years_experience = Column(Numeric(4, 1), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    mentor = relationship("MentorProfile", back_populates="skills")
    skill = relationship("Skill")


class StudentDomainInterest(Base):
    __tablename__ = "student_domain_interest"

    student_user_id = Column(BigInteger, ForeignKey("student_profile.user_id", ondelete="CASCADE"), primary_key=True)
    domain_id = Column(BigInteger, ForeignKey("mentorship_domain.domain_id", ondelete="RESTRICT"), primary_key=True)
    priority_order = Column(SmallInteger, nullable=False)
    interest_notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("student_user_id", "priority_order", name="uq_student_domain_priority"),
    )

    student = relationship("StudentProfile", back_populates="domain_interests")
    domain = relationship("MentorshipDomain")


class MentorDomainExpertise(Base):
    __tablename__ = "mentor_domain_expertise"

    mentor_user_id = Column(BigInteger, ForeignKey("mentor_profile.user_id", ondelete="CASCADE"), primary_key=True)
    domain_id = Column(BigInteger, ForeignKey("mentorship_domain.domain_id", ondelete="RESTRICT"), primary_key=True)
    expertise_level = Column(String(20), nullable=False)
    years_experience = Column(Numeric(4, 1), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)

    mentor = relationship("MentorProfile", back_populates="domain_expertises")
    domain = relationship("MentorshipDomain")


# 4. Mentorship Lifecycle & Recommendations

class MentorshipRequest(Base):
    __tablename__ = "mentorship_request"

    request_id = pk_column()
    student_user_id = Column(BigInteger, ForeignKey("student_profile.user_id", ondelete="RESTRICT"), nullable=False)
    mentor_user_id = Column(BigInteger, ForeignKey("mentor_profile.user_id", ondelete="RESTRICT"), nullable=False)
    domain_id = Column(BigInteger, ForeignKey("mentorship_domain.domain_id", ondelete="RESTRICT"), nullable=False)
    request_message = Column(Text, nullable=False)
    career_goal_snapshot = Column(Text, nullable=True)
    request_status = Column(String(20), default="PENDING", nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    decision_at = Column(DateTime, nullable=True)
    decided_by_user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="RESTRICT"), nullable=True)
    decision_reason = Column(String(120), nullable=True)
    response_note = Column(Text, nullable=True)
    idempotency_key = Column(String(100), unique=True, nullable=True)

    student = relationship("StudentProfile", foreign_keys=[student_user_id], back_populates="requests")
    mentor = relationship("MentorProfile", foreign_keys=[mentor_user_id], back_populates="requests")
    domain = relationship("MentorshipDomain")
    allocation = relationship("MentorAllocation", back_populates="request", uselist=False)


class RecommendationRun(Base):
    __tablename__ = "recommendation_run"

    run_id = pk_column()
    student_user_id = Column(BigInteger, ForeignKey("student_profile.user_id", ondelete="CASCADE"), nullable=False)
    input_goal = Column(Text, nullable=True)
    algorithm_version = Column(String(40), nullable=False)
    profile_version = Column(String(40), nullable=True)
    filter_snapshot = Column(JSON, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    recommendations = relationship("RecommendedMentor", back_populates="run", cascade="all, delete-orphan")


class RecommendedMentor(Base):
    __tablename__ = "recommended_mentor"

    recommendation_id = pk_column()
    run_id = Column(BigInteger, ForeignKey("recommendation_run.run_id", ondelete="CASCADE"), nullable=False)
    mentor_user_id = Column(BigInteger, ForeignKey("mentor_profile.user_id", ondelete="RESTRICT"), nullable=False)
    rank_position = Column(SmallInteger, nullable=False)
    score = Column(Numeric(7, 4), nullable=False)
    eligibility_status = Column(String(20), nullable=False)
    explanation_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", "mentor_user_id", name="uq_rec_run_mentor"),
        UniqueConstraint("run_id", "rank_position", name="uq_rec_run_rank"),
    )

    run = relationship("RecommendationRun", back_populates="recommendations")
    mentor = relationship("MentorProfile")


class MentorAllocation(Base):
    __tablename__ = "mentor_allocation"

    allocation_id = pk_column()
    request_id = Column(BigInteger, ForeignKey("mentorship_request.request_id", ondelete="RESTRICT"), unique=True, nullable=False)
    allocation_status = Column(String(20), default="ACTIVE", nullable=False)
    allocated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    ended_by_user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="RESTRICT"), nullable=True)
    termination_reason = Column(Text, nullable=True)

    request = relationship("MentorshipRequest", back_populates="allocation")
    bookings = relationship("Booking", back_populates="allocation")


# 5. Availability, Booking and Sessions

class MentorAvailability(Base):
    __tablename__ = "mentor_availability"

    availability_id = pk_column()
    mentor_user_id = Column(BigInteger, ForeignKey("mentor_profile.user_id", ondelete="RESTRICT"), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    slot_status = Column(String(20), default="OPEN", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("mentor_user_id", "starts_at", "ends_at", name="uq_mentor_slot_interval"),
    )

    mentor = relationship("MentorProfile", back_populates="availabilities")
    bookings = relationship("Booking", back_populates="availability")


class Booking(Base):
    __tablename__ = "booking"

    booking_id = pk_column()
    allocation_id = Column(BigInteger, ForeignKey("mentor_allocation.allocation_id", ondelete="RESTRICT"), nullable=False)
    availability_id = Column(BigInteger, ForeignKey("mentor_availability.availability_id", ondelete="RESTRICT"), nullable=False)
    booking_type = Column(String(30), default="MENTORSHIP", nullable=False)
    booking_status = Column(String(20), default="CONFIRMED", nullable=False)
    booked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by_user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="RESTRICT"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    idempotency_key = Column(String(100), unique=True, nullable=False)

    allocation = relationship("MentorAllocation", back_populates="bookings")
    availability = relationship("MentorAvailability", back_populates="bookings")
    session = relationship("MentorshipSession", back_populates="booking", uselist=False)


class MentorshipSession(Base):
    __tablename__ = "mentorship_session"

    session_id = pk_column()
    booking_id = Column(BigInteger, ForeignKey("booking.booking_id", ondelete="RESTRICT"), unique=True, nullable=False)
    session_status = Column(String(20), default="SCHEDULED", nullable=False)
    actual_start_at = Column(DateTime, nullable=True)
    actual_end_at = Column(DateTime, nullable=True)
    discussion_summary = Column(Text, nullable=True)
    performance_observations = Column(Text, nullable=True)
    improvement_areas = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    preparation_recommendation = Column(Text, nullable=True)
    recorded_at = Column(DateTime, nullable=True)
    recorded_by_user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="RESTRICT"), nullable=True)

    booking = relationship("Booking", back_populates="session")
    skill_assessments = relationship("SessionSkillAssessment", back_populates="session", cascade="all, delete-orphan")
    feedback = relationship("SessionFeedback", back_populates="session")
    review = relationship("MentorReview", back_populates="session", uselist=False)


class SessionSkillAssessment(Base):
    __tablename__ = "session_skill_assessment"

    session_id = Column(BigInteger, ForeignKey("mentorship_session.session_id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(BigInteger, ForeignKey("skill.skill_id", ondelete="RESTRICT"), primary_key=True)
    assessment_result = Column(String(30), nullable=False)
    assessment_notes = Column(Text, nullable=True)

    session = relationship("MentorshipSession", back_populates="skill_assessments")
    skill = relationship("Skill")


# 6. Feedback, Reviews, Notifications and Audit

class SessionFeedback(Base):
    __tablename__ = "session_feedback"

    feedback_id = pk_column()
    session_id = Column(BigInteger, ForeignKey("mentorship_session.session_id", ondelete="CASCADE"), nullable=False)
    submitted_by_user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="RESTRICT"), nullable=False)
    communication_rating = Column(SmallInteger, nullable=True)
    helpfulness_rating = Column(SmallInteger, nullable=True)
    technical_preparation_rating = Column(SmallInteger, nullable=True)
    comments = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("session_id", "submitted_by_user_id", name="uq_feedback_session_user"),
    )

    session = relationship("MentorshipSession", back_populates="feedback")
    submitted_by = relationship("UserAccount")


class MentorReview(Base):
    __tablename__ = "mentor_review"

    review_id = pk_column()
    session_id = Column(BigInteger, ForeignKey("mentorship_session.session_id", ondelete="RESTRICT"), unique=True, nullable=False)
    rating = Column(SmallInteger, nullable=False)
    review_text = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="chk_mentor_review_rating"),
    )

    session = relationship("MentorshipSession", back_populates="review")


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"

    outbox_id = pk_column()
    aggregate_type = Column(String(40), nullable=False)
    aggregate_id = Column(BigInteger, nullable=False)
    event_type = Column(String(60), nullable=False)
    payload_json = Column(JSON, nullable=False)
    delivery_status = Column(String(20), default="PENDING", nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    next_attempt_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    dedupe_key = Column(String(160), unique=True, nullable=False)


class Notification(Base):
    __tablename__ = "notification"

    notification_id = pk_column()
    recipient_user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="RESTRICT"), nullable=False)
    outbox_id = Column(BigInteger, ForeignKey("notification_outbox.outbox_id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(180), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("outbox_id", "recipient_user_id", name="uq_notification_outbox_recipient"),
    )

    recipient = relationship("UserAccount", back_populates="notifications")
    outbox = relationship("NotificationOutbox")


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = pk_column()
    actor_user_id = Column(BigInteger, ForeignKey("user_account.user_id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    action = Column(String(40), nullable=False)
    old_values_json = Column(JSON, nullable=True)
    new_values_json = Column(JSON, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    correlation_id = Column(String(80), nullable=True)

    actor = relationship("UserAccount")

