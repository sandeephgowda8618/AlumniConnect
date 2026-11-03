"""AlumniConnect Comprehensive Database Population & Seeding Script
Populates the relational database with realistic, interconnected synthetic demo data
following the 15 authoritative project specifications.

Deterministic, reusable, and idempotent.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Ensure backend root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal, engine, Base
from app.models.entities import (
    Role, Department, Company, UserAccount,
    StudentProfile, MentorProfile, Skill, MentorshipDomain,
    StudentSkill, MentorSkill, StudentDomainInterest, MentorDomainExpertise,
    MentorshipRequest, MentorAllocation, MentorAvailability,
    Booking, MentorshipSession, SessionSkillAssessment, SessionFeedback,
    MentorReview, RecommendationRun, RecommendedMentor,
    NotificationOutbox, Notification, AuditLog
)
from app.db.init_db import sync_graph_projection
from app.core.graph_client import graph_client
from app.services.cache_service import CacheService
from app.workers.outbox_worker import outbox_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_demo_data")

DEMO_PASSWORD_HASH = "$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a"  # Password123!
ANCHOR_NOW = datetime(2026, 11, 3, 10, 0, 0)


def ensure_views(db: Session):
    """Ensures database views (V01-V04 and v_booking_details) are created."""
    views = [
        """CREATE VIEW IF NOT EXISTS v_public_mentor_directory AS
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
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        LEFT JOIN company AS c ON c.company_id = mp.current_company_id
        LEFT JOIN department AS d ON d.department_id = mp.alumni_department_id
        WHERE ua.account_status = 'ACTIVE' AND mp.accepting_requests = 1;""",

        """CREATE VIEW IF NOT EXISTS v_mentor_rating_summary AS
        SELECT
            mp.user_id AS mentor_user_id,
            ua.display_name AS full_name,
            COUNT(mr.review_id) AS review_count,
            ROUND(AVG(mr.rating), 2) AS average_rating,
            MAX(mr.submitted_at) AS latest_review_at
        FROM mentor_profile AS mp
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        LEFT JOIN mentor_availability AS ma ON ma.mentor_user_id = mp.user_id
        LEFT JOIN booking AS b ON b.availability_id = ma.availability_id
        LEFT JOIN mentorship_session AS ms ON ms.booking_id = b.booking_id
        LEFT JOIN mentor_review AS mr ON mr.session_id = ms.session_id
        GROUP BY mp.user_id, ua.display_name;""",

        """CREATE VIEW IF NOT EXISTS v_student_mentorship_summary AS
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
        JOIN user_account AS ua ON ua.user_id = sp.user_id
        LEFT JOIN department AS d ON d.department_id = sp.department_id
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
        ) AS a ON a.student_user_id = sp.user_id;""",

        """CREATE VIEW IF NOT EXISTS v_mentor_session_outcomes AS
        SELECT
            mp.user_id AS mentor_user_id,
            ua.display_name AS mentor_name,
            COUNT(ms.session_id) AS total_sessions,
            SUM(CASE WHEN ms.session_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_sessions,
            SUM(CASE WHEN ms.session_status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_sessions,
            SUM(CASE WHEN ms.session_status = 'NO_SHOW' THEN 1 ELSE 0 END) AS no_show_sessions,
            SUM(CASE WHEN ms.session_status = 'SCHEDULED' THEN 1 ELSE 0 END) AS scheduled_sessions
        FROM mentor_profile AS mp
        JOIN user_account AS ua ON ua.user_id = mp.user_id
        LEFT JOIN mentor_availability AS ma ON ma.mentor_user_id = mp.user_id
        LEFT JOIN booking AS b ON b.availability_id = ma.availability_id
        LEFT JOIN mentorship_session AS ms ON ms.booking_id = b.booking_id
        GROUP BY mp.user_id, ua.display_name;""",

        """CREATE VIEW IF NOT EXISTS v_booking_details AS
        SELECT
            b.booking_id,
            b.booking_type,
            b.booking_status,
            b.booked_at,
            b.cancelled_at,
            b.cancellation_reason,
            b.idempotency_key,
            b.allocation_id,
            alloc.allocation_status,
            req.student_user_id,
            stud_ua.display_name AS student_name,
            req.mentor_user_id,
            ment_ua.display_name AS mentor_name,
            b.availability_id,
            avail.starts_at AS slot_starts_at,
            avail.ends_at AS slot_ends_at,
            avail.slot_status,
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
        LEFT JOIN mentorship_session AS sess ON sess.booking_id = b.booking_id;"""
    ]
    for sql in views:
        db.execute(text(sql))
    db.commit()


def seed_departments(db: Session) -> Dict[str, int]:
    """Ensures at least 5 departments exist."""
    dept_defs = [
        ("CSE", "Computer Science and Engineering", "PES University"),
        ("ECE", "Electronics and Communication Engineering", "PES University"),
        ("AIML", "Artificial Intelligence and Machine Learning", "PES University"),
        ("ISE", "Information Science and Engineering", "PES University"),
        ("EEE", "Electrical and Electronics Engineering", "PES University"),
        ("MECH", "Mechanical and Automation Engineering", "PES University"),
    ]
    dept_map = {}
    for code, name, inst in dept_defs:
        dept = db.query(Department).filter_by(department_code=code, institution_name=inst).first()
        if not dept:
            dept = Department(department_code=code, department_name=name, institution_name=inst)
            db.add(dept)
            db.flush()
        dept_map[code] = dept.department_id
    db.commit()
    return dept_map


def seed_companies(db: Session) -> Dict[str, int]:
    """Ensures at least 5 companies exist."""
    company_defs = [
        ("Google", "https://about.google", "Technology & AI"),
        ("Amazon", "https://aboutamazon.com", "Cloud Computing & E-Commerce"),
        ("Microsoft", "https://microsoft.com", "Enterprise Software & Cloud"),
        ("Cisco Systems", "https://cisco.com", "Networking & Security"),
        ("Goldman Sachs", "https://goldmansachs.com", "Financial Technology"),
        ("Apple", "https://apple.com", "Consumer Tech & Operating Systems"),
        ("NVIDIA", "https://nvidia.com", "Semiconductors & Accelerated AI"),
        ("Atlassian", "https://atlassian.com", "Developer Collaboration Tools"),
        ("Uber", "https://uber.com", "Mobility & High-Scale Systems"),
    ]
    comp_map = {}
    for name, url, ind in company_defs:
        comp = db.query(Company).filter_by(company_name=name).first()
        if not comp:
            comp = Company(company_name=name, website_url=url, industry=ind)
            db.add(comp)
            db.flush()
        comp_map[name] = comp.company_id
    db.commit()
    return comp_map


def seed_skills(db: Session) -> Dict[str, int]:
    """Ensures at least 5 skills exist."""
    skill_defs = [
        ("Python", "Programming Languages", "Core Python, concurrency, object-oriented design and async programming."),
        ("SQL & RDBMS", "Databases", "Relational design, indexing, transactions, stored procedures and query optimization."),
        ("Machine Learning", "Artificial Intelligence", "Supervised/unsupervised algorithms, evaluation metrics and feature engineering."),
        ("MLOps & CI/CD", "DevOps & AI", "Pipeline automation, model registry, containerization and tracking."),
        ("Docker", "Containers & Infrastructure", "Container creation, multi-stage builds, and compose orchestration."),
        ("Kubernetes", "Cloud Infrastructure", "Container orchestration, deployments, services and cluster administration."),
        ("AWS", "Cloud Providers", "EC2, S3, RDS, Lambda, VPC and IAM architecture."),
        ("React", "Frontend Development", "Component architecture, state management, hooks and Next.js integration."),
        ("FastAPI", "Backend Development", "High-performance asynchronous Python API framework with Pydantic."),
        ("Distributed Systems", "System Architecture", "Consensus, caching strategies, replication and high-availability patterns."),
        ("Data Structures & Algorithms", "Foundations", "Algorithm analysis, tree/graph traversal, and technical interview prep."),
        ("Neo4j & Graph DB", "Databases", "Graph modeling, Cypher query optimization, and traversal algorithms."),
        ("Cybersecurity & Cryptography", "Security", "Network protocols, threat modeling, PKI, and application security."),
        ("Go / Golang", "Programming Languages", "Concurrent systems programming, microservices, and goroutine patterns."),
        ("Data Engineering & Spark", "Data Platforms", "PySpark, distributed ETL pipelines, Apache Iceberg and batch data processing."),
    ]
    skill_map = {}
    for name, cat, desc in skill_defs:
        sk = db.query(Skill).filter_by(skill_name=name).first()
        if not sk:
            sk = Skill(skill_name=name, category=cat, description=desc)
            db.add(sk)
            db.flush()
        skill_map[name] = sk.skill_id
    db.commit()
    return skill_map


def seed_domains(db: Session) -> Dict[str, int]:
    """Ensures at least 5 mentorship domains exist."""
    domain_defs = [
        ("Machine Learning & AI", "Predictive modeling, deep learning, computer vision, NLP and generative models."),
        ("Cloud Computing & DevOps", "Cloud architecture, Kubernetes orchestration, infrastructure as code and SRE."),
        ("Full-Stack Web Engineering", "Modern frontend architectures, REST/GraphQL APIs, relational modeling and auth."),
        ("Distributed Systems & Microservices", "High-scale architectures, event-driven systems, caching and consistency."),
        ("Data Engineering & Analytics", "ETL pipelines, data warehousing, stream processing and analytics workflows."),
        ("Cybersecurity & Systems Security", "Threat modeling, secure code audits, cloud security and identity federation."),
        ("Competitive Programming & DSA Interview Prep", "Advanced algorithmic problem solving, graph algorithms, dynamic programming."),
    ]
    dom_map = {}
    for name, desc in domain_defs:
        dom = db.query(MentorshipDomain).filter_by(domain_name=name).first()
        if not dom:
            dom = MentorshipDomain(domain_name=name, description=desc)
            db.add(dom)
            db.flush()
        dom_map[name] = dom.domain_id
    db.commit()
    return dom_map


def seed_roles(db: Session) -> Dict[str, int]:
    """Maintains the 3 documented fixed roles."""
    role_defs = [
        ("ADMINISTRATOR", "System Administrator", "Platform oversight, user management, catalogue maintenance and reporting."),
        ("MENTOR", "Alumni Mentor", "Provides mentorship, mock interviews, slot availability, and session evaluations."),
        ("STUDENT", "Student Mentee", "Discovers mentors, books eligible sessions, submits requests, and provides feedback."),
    ]
    role_map = {}
    for code, name, desc in role_defs:
        r = db.query(Role).filter_by(role_code=code).first()
        if not r:
            r = Role(role_code=code, role_name=name, description=desc, is_active=True)
            db.add(r)
            db.flush()
        role_map[code] = r.role_id
    db.commit()
    return role_map


def get_or_create_user(db: Session, email: str, display_name: str, role_id: int) -> UserAccount:
    """Idempotently fetches or creates a user account."""
    user = db.query(UserAccount).filter_by(email=email).first()
    if not user:
        user = UserAccount(
            role_id=role_id,
            email=email,
            display_name=display_name,
            password_hash=DEMO_PASSWORD_HASH,
            account_status="ACTIVE",
            created_at=ANCHOR_NOW - timedelta(days=60),
            last_login_at=ANCHOR_NOW - timedelta(hours=2)
        )
        db.add(user)
        db.flush()
    return user


def seed_all():
    """Main seeding function orchestrating all entities."""
    logger.info("Starting AlumniConnect Comprehensive Database Population...")
    db = SessionLocal()
    try:
        # 1. Base Setup & Views
        Base.metadata.create_all(bind=engine)
        ensure_views(db)

        # 2. Reference & Catalogues
        role_map = seed_roles(db)
        dept_map = seed_departments(db)
        comp_map = seed_companies(db)
        skill_map = seed_skills(db)
        dom_map = seed_domains(db)

        # 3. Administrator Account
        admin_user = get_or_create_user(db, "admin@alumniconnect.edu", "Dr. Radhika Sen (Admin)", role_map["ADMINISTRATOR"])
        logger.info(f"Verified Administrator: {admin_user.display_name} (ID: {admin_user.user_id})")

        # 4. Mentors (At least 6 mentors, targeting 8)
        mentor_data = [
            {
                "email": "rohit.verma@alumniconnect.edu",
                "display_name": "Rohit Verma",
                "alumni_id": "ALUM-2019-CSE-042",
                "dept_code": "CSE",
                "comp_name": "Google",
                "job_title": "Senior Machine Learning Engineer",
                "experience": 5.5,
                "max_mentees": 3,
                "bio": "Alumnus of CSE (Batch 2019). Currently working on large-scale machine learning and recommendation infrastructure at Google. Passionate about helping students crack technical interviews and master ML engineering fundamentals.",
                "skills": [("Python", "EXPERT", 5.5), ("Machine Learning", "EXPERT", 5.0), ("MLOps & CI/CD", "ADVANCED", 3.5), ("Docker", "INTERMEDIATE", 3.0), ("SQL & RDBMS", "ADVANCED", 4.0)],
                "domains": [("Machine Learning & AI", "EXPERT", 5.5, True), ("Data Engineering & Analytics", "ADVANCED", 3.5, False)]
            },
            {
                "email": "sneha.rao@alumniconnect.edu",
                "display_name": "Sneha Rao",
                "alumni_id": "ALUM-2018-ISE-108",
                "dept_code": "ISE",
                "comp_name": "Amazon",
                "job_title": "Principal Solutions Architect",
                "experience": 6.5,
                "max_mentees": 2,
                "bio": "Alumna of ISE (Batch 2018). Cloud systems and Kubernetes specialist at AWS. Helping students with distributed systems architecture, cloud infrastructure, and career transitions into DevOps/SRE.",
                "skills": [("AWS", "EXPERT", 6.5), ("Kubernetes", "EXPERT", 5.0), ("Distributed Systems", "ADVANCED", 4.5), ("Docker", "ADVANCED", 4.0), ("Go / Golang", "ADVANCED", 3.0)],
                "domains": [("Cloud Computing & DevOps", "EXPERT", 6.5, True), ("Distributed Systems & Microservices", "ADVANCED", 4.5, False)]
            },
            {
                "email": "vikram.joshi@alumniconnect.edu",
                "display_name": "Vikram Joshi",
                "alumni_id": "ALUM-2020-CSE-091",
                "dept_code": "CSE",
                "comp_name": "Microsoft",
                "job_title": "Lead Software Engineer",
                "experience": 4.0,
                "max_mentees": 3,
                "bio": "Full-stack software architect at Microsoft working on modern enterprise web applications and API platforms using Next.js and Python.",
                "skills": [("React", "EXPERT", 4.0), ("FastAPI", "ADVANCED", 3.5), ("SQL & RDBMS", "ADVANCED", 4.0), ("Python", "ADVANCED", 3.5), ("Distributed Systems", "INTERMEDIATE", 2.5)],
                "domains": [("Full-Stack Web Engineering", "EXPERT", 4.0, True), ("Distributed Systems & Microservices", "INTERMEDIATE", 2.5, False)]
            },
            {
                "email": "ananya.deshmukh@alumniconnect.edu",
                "display_name": "Ananya Deshmukh",
                "alumni_id": "ALUM-2017-ECE-019",
                "dept_code": "ECE",
                "comp_name": "NVIDIA",
                "job_title": "Staff ML & Computer Vision Engineer",
                "experience": 7.0,
                "max_mentees": 3,
                "bio": "Specialized in deep neural network optimization, TensorRT, and edge computer vision inference pipelines. Passionate about guiding students in applied AI and competitive systems prep.",
                "skills": [("Machine Learning", "EXPERT", 7.0), ("Python", "EXPERT", 6.5), ("Data Structures & Algorithms", "EXPERT", 6.0), ("Docker", "ADVANCED", 4.0)],
                "domains": [("Machine Learning & AI", "EXPERT", 7.0, True), ("Competitive Programming & DSA Interview Prep", "ADVANCED", 5.0, False)]
            },
            {
                "email": "karthik.subramanian@alumniconnect.edu",
                "display_name": "Karthik Subramanian",
                "alumni_id": "ALUM-2015-CSE-004",
                "dept_code": "CSE",
                "comp_name": "Goldman Sachs",
                "job_title": "VP of Engineering - FinTech Core",
                "experience": 9.5,
                "max_mentees": 2,
                "bio": "Leading low-latency transactional ledger systems and distributed ledger engines. Strong focus on transaction isolation, ACID properties, and technical leadership.",
                "skills": [("Distributed Systems", "EXPERT", 9.0), ("SQL & RDBMS", "EXPERT", 8.5), ("Go / Golang", "ADVANCED", 5.0), ("Python", "ADVANCED", 6.0)],
                "domains": [("Distributed Systems & Microservices", "EXPERT", 9.0, True), ("Data Engineering & Analytics", "ADVANCED", 6.0, False)]
            },
            {
                "email": "neha.kulkarni@alumniconnect.edu",
                "display_name": "Neha Kulkarni",
                "alumni_id": "ALUM-2019-ISE-077",
                "dept_code": "ISE",
                "comp_name": "Cisco Systems",
                "job_title": "Senior Security Architect",
                "experience": 5.0,
                "max_mentees": 3,
                "bio": "Cybersecurity architect focusing on zero-trust enterprise security, API gateway defenses, and PKI infrastructure. Helping students prepare for infosec careers.",
                "skills": [("Cybersecurity & Cryptography", "EXPERT", 5.0), ("Distributed Systems", "ADVANCED", 4.0), ("Python", "ADVANCED", 4.5), ("Docker", "INTERMEDIATE", 3.0)],
                "domains": [("Cybersecurity & Systems Security", "EXPERT", 5.0, True), ("Cloud Computing & DevOps", "INTERMEDIATE", 3.0, False)]
            },
            {
                "email": "aditya.nair@alumniconnect.edu",
                "display_name": "Aditya Nair",
                "alumni_id": "ALUM-2020-AIML-033",
                "dept_code": "AIML",
                "comp_name": "Uber",
                "job_title": "Lead Data Platform Engineer",
                "experience": 4.5,
                "max_mentees": 2,
                "bio": "Alumnus of AIML batch 2020. Designs streaming ingestion pipelines, Kafka streaming analytics, and lakehouse storage at Uber.",
                "skills": [("Data Engineering & Spark", "EXPERT", 4.5), ("SQL & RDBMS", "EXPERT", 4.5), ("Python", "EXPERT", 4.0), ("Kubernetes", "INTERMEDIATE", 2.5)],
                "domains": [("Data Engineering & Analytics", "EXPERT", 4.5, True), ("Distributed Systems & Microservices", "ADVANCED", 3.5, False)]
            },
            {
                "email": "meera.iyer@alumniconnect.edu",
                "display_name": "Meera Iyer",
                "alumni_id": "ALUM-2016-CSE-011",
                "dept_code": "CSE",
                "comp_name": "Apple",
                "job_title": "Principal Site Reliability Engineer",
                "experience": 8.0,
                "max_mentees": 2,
                "bio": "Specialist in cloud resiliency, chaos engineering, high-availability data infrastructure, and Kubernetes multi-cluster routing at Apple.",
                "skills": [("Kubernetes", "EXPERT", 7.5), ("AWS", "EXPERT", 7.0), ("Go / Golang", "ADVANCED", 5.0), ("Distributed Systems", "EXPERT", 6.5)],
                "domains": [("Cloud Computing & DevOps", "EXPERT", 8.0, True), ("Distributed Systems & Microservices", "ADVANCED", 5.0, False)]
            }
        ]

        mentors: Dict[str, UserAccount] = {}
        for m in mentor_data:
            u = get_or_create_user(db, m["email"], m["display_name"], role_map["MENTOR"])
            mentors[m["email"]] = u
            
            # Mentor Profile
            mp = db.query(MentorProfile).filter_by(user_id=u.user_id).first()
            if not mp:
                mp = MentorProfile(
                    user_id=u.user_id,
                    alumni_identifier=m["alumni_id"],
                    alumni_department_id=dept_map[m["dept_code"]],
                    current_company_id=comp_map[m["comp_name"]],
                    job_title=m["job_title"],
                    years_experience=m["experience"],
                    max_active_mentees=m["max_mentees"],
                    accepting_requests=True,
                    professional_summary=m["bio"]
                )
                db.add(mp)
                db.flush()

            # Mentor Skills
            for sk_name, prof, yrs in m["skills"]:
                sk_id = skill_map[sk_name]
                if not db.query(MentorSkill).filter_by(mentor_user_id=u.user_id, skill_id=sk_id).first():
                    db.add(MentorSkill(mentor_user_id=u.user_id, skill_id=sk_id, proficiency_level=prof, years_experience=yrs))

            # Mentor Domains
            for dom_name, exp_level, yrs, is_prim in m["domains"]:
                d_id = dom_map[dom_name]
                if not db.query(MentorDomainExpertise).filter_by(mentor_user_id=u.user_id, domain_id=d_id).first():
                    db.add(MentorDomainExpertise(mentor_user_id=u.user_id, domain_id=d_id, expertise_level=exp_level, years_experience=yrs, is_primary=is_prim))
        
        db.commit()
        logger.info(f"Verified {len(mentors)} Mentor accounts and profiles.")

        # 5. Students (At least 8 students, targeting 10)
        student_data = [
            {
                "email": "aarav.sharma@alumniconnect.edu",
                "display_name": "Aarav Sharma",
                "student_number": "PES1UG22CS001",
                "dept_code": "CSE",
                "programme": "B.Tech in Computer Science and Engineering",
                "batch": 2022,
                "grad_year": 2026,
                "career_goal": "Aspiring Machine Learning and Systems Software Engineer targeting top tier tech firms.",
                "bio": "Third-year CSE student interested in machine learning algorithms, database internals, and backend microservices.",
                "skills": [("Python", "INTERMEDIATE", 2.0), ("SQL & RDBMS", "INTERMEDIATE", 1.5), ("Machine Learning", "BEGINNER", 1.0), ("FastAPI", "INTERMEDIATE", 1.5)],
                "domains": [("Machine Learning & AI", 1, "Wants to master production ML."), ("Distributed Systems & Microservices", 2, "Interested in high-throughput APIs.")]
            },
            {
                "email": "priya.patel@alumniconnect.edu",
                "display_name": "Priya Patel",
                "student_number": "PES1UG23AM015",
                "dept_code": "AIML",
                "programme": "B.Tech in Artificial Intelligence and Machine Learning",
                "batch": 2023,
                "grad_year": 2027,
                "career_goal": "Targeting roles in Cloud DevOps and scalable Machine Learning platforms.",
                "bio": "Second-year AIML student working on computer vision and cloud infrastructure projects.",
                "skills": [("Python", "INTERMEDIATE", 1.5), ("AWS", "BEGINNER", 0.5), ("Docker", "INTERMEDIATE", 1.0)],
                "domains": [("Cloud Computing & DevOps", 1, "Focusing on Kubernetes orchestration."), ("Machine Learning & AI", 2, "Deploying vision models.")]
            },
            {
                "email": "rohan.gupta@alumniconnect.edu",
                "display_name": "Rohan Gupta",
                "student_number": "PES1UG22CS044",
                "dept_code": "CSE",
                "programme": "B.Tech in Computer Science and Engineering",
                "batch": 2022,
                "grad_year": 2026,
                "career_goal": "Full-Stack Web Engineer targeting enterprise SaaS products.",
                "bio": "Passionate about modern TypeScript, Next.js, FastAPI, and robust relational data modeling.",
                "skills": [("React", "ADVANCED", 2.5), ("FastAPI", "INTERMEDIATE", 2.0), ("SQL & RDBMS", "INTERMEDIATE", 1.5), ("Docker", "INTERMEDIATE", 1.0)],
                "domains": [("Full-Stack Web Engineering", 1, "Building scalable SaaS web platforms."), ("Distributed Systems & Microservices", 2, "Event-driven architecture.")]
            },
            {
                "email": "tanvi.shukla@alumniconnect.edu",
                "display_name": "Tanvi Shukla",
                "student_number": "PES1UG23IS088",
                "dept_code": "ISE",
                "programme": "B.Tech in Information Science and Engineering",
                "batch": 2023,
                "grad_year": 2027,
                "career_goal": "Data Scientist & Analytics Engineer.",
                "bio": "Enthusiastic about data storytelling, statistical inference, feature engineering, and big data warehousing.",
                "skills": [("Python", "INTERMEDIATE", 2.0), ("SQL & RDBMS", "ADVANCED", 2.0), ("Data Engineering & Spark", "BEGINNER", 0.5)],
                "domains": [("Data Engineering & Analytics", 1, "Analytical modeling & big data warehousing."), ("Machine Learning & AI", 2, "Predictive algorithms.")]
            },
            {
                "email": "siddharth.menon@alumniconnect.edu",
                "display_name": "Siddharth Menon",
                "student_number": "PES1UG21EC021",
                "dept_code": "ECE",
                "programme": "B.Tech in Electronics and Communication",
                "batch": 2021,
                "grad_year": 2025,
                "career_goal": "Edge AI & Cloud Solutions Engineer.",
                "bio": "Senior year ECE student working on low-power IoT inference and AWS cloud connectivity.",
                "skills": [("Python", "INTERMEDIATE", 2.5), ("AWS", "INTERMEDIATE", 1.5), ("Machine Learning", "INTERMEDIATE", 2.0)],
                "domains": [("Cloud Computing & DevOps", 1, "Edge serverless architectures."), ("Machine Learning & AI", 2, "Edge inference models.")]
            },
            {
                "email": "ananya.bhat@alumniconnect.edu",
                "display_name": "Ananya Bhat",
                "student_number": "PES1UG23AM072",
                "dept_code": "AIML",
                "programme": "B.Tech in Artificial Intelligence and Machine Learning",
                "batch": 2023,
                "grad_year": 2027,
                "career_goal": "Applied NLP & LLM Systems Researcher.",
                "bio": "Exploring transformer architectures, fine-tuning techniques, and retrieval-augmented generation.",
                "skills": [("Python", "ADVANCED", 2.0), ("Machine Learning", "INTERMEDIATE", 2.0), ("Neo4j & Graph DB", "BEGINNER", 0.5)],
                "domains": [("Machine Learning & AI", 1, "RAG systems and graph-augmented LLMs."), ("Data Engineering & Analytics", 2, "Corpus processing.")]
            },
            {
                "email": "varun.chatterjee@alumniconnect.edu",
                "display_name": "Varun Chatterjee",
                "student_number": "PES1UG22CS119",
                "dept_code": "CSE",
                "programme": "B.Tech in Computer Science and Engineering",
                "batch": 2022,
                "grad_year": 2026,
                "career_goal": "Application Security Engineer & Penetration Tester.",
                "bio": "Focusing on secure software development lifecycle, binary exploitation, and zero-trust cloud network security.",
                "skills": [("Cybersecurity & Cryptography", "INTERMEDIATE", 2.0), ("Python", "INTERMEDIATE", 2.0), ("Docker", "BEGINNER", 1.0)],
                "domains": [("Cybersecurity & Systems Security", 1, "AppSec and cloud defensive mechanisms."), ("Cloud Computing & DevOps", 2, "Container hardening.")]
            },
            {
                "email": "isha.singh@alumniconnect.edu",
                "display_name": "Isha Singh",
                "student_number": "PES1UG22IS055",
                "dept_code": "ISE",
                "programme": "B.Tech in Information Science and Engineering",
                "batch": 2022,
                "grad_year": 2026,
                "career_goal": "Distributed Backend Engineer.",
                "bio": "Interested in distributed consensus, Redis caching patterns, and high-concurrency microservice design.",
                "skills": [("Distributed Systems", "INTERMEDIATE", 1.5), ("SQL & RDBMS", "ADVANCED", 2.0), ("Go / Golang", "BEGINNER", 1.0)],
                "domains": [("Distributed Systems & Microservices", 1, "High concurrency caching and event streaming."), ("Full-Stack Web Engineering", 2, "API gateway design.")]
            },
            {
                "email": "dev.kapoor@alumniconnect.edu",
                "display_name": "Dev Kapoor",
                "student_number": "PES1UG23CS012",
                "dept_code": "CSE",
                "programme": "B.Tech in Computer Science and Engineering",
                "batch": 2023,
                "grad_year": 2027,
                "career_goal": "Competitive Programmer & High-Performance Software Engineer.",
                "bio": "Active competitive programmer (Candidate Master) looking to polish system design fundamentals and behavioral interview techniques.",
                "skills": [("Data Structures & Algorithms", "EXPERT", 3.0), ("Python", "ADVANCED", 2.0), ("SQL & RDBMS", "BEGINNER", 1.0)],
                "domains": [("Competitive Programming & DSA Interview Prep", 1, "Mastering technical coding interview rubrics."), ("Distributed Systems & Microservices", 2, "System design foundations.")]
            },
            {
                "email": "ritika.nambiar@alumniconnect.edu",
                "display_name": "Ritika Nambiar",
                "student_number": "PES1UG22EE009",
                "dept_code": "EEE",
                "programme": "B.Tech in Electrical and Electronics Engineering",
                "batch": 2022,
                "grad_year": 2026,
                "career_goal": "Hardware-Software Co-Design & IoT Cloud Architect.",
                "bio": "Passionate about combining embedded systems with cloud telemetry, MQTT brokers, and automated CI/CD.",
                "skills": [("Python", "INTERMEDIATE", 2.0), ("AWS", "BEGINNER", 1.0), ("Docker", "BEGINNER", 0.5)],
                "domains": [("Cloud Computing & DevOps", 1, "IoT telemetry ingest & cloud analytics."), ("Full-Stack Web Engineering", 2, "Telemetry dashboards.")]
            }
        ]

        students: Dict[str, UserAccount] = {}
        for s in student_data:
            u = get_or_create_user(db, s["email"], s["display_name"], role_map["STUDENT"])
            students[s["email"]] = u

            # Student Profile
            sp = db.query(StudentProfile).filter_by(user_id=u.user_id).first()
            if not sp:
                sp = StudentProfile(
                    user_id=u.user_id,
                    student_number=s["student_number"],
                    department_id=dept_map[s["dept_code"]],
                    programme=s["programme"],
                    batch_year=s["batch"],
                    expected_graduation_year=s["grad_year"],
                    career_goal=s["career_goal"],
                    bio=s["bio"]
                )
                db.add(sp)
                db.flush()

            # Student Skills
            for sk_name, prof, yrs in s["skills"]:
                sk_id = skill_map[sk_name]
                if not db.query(StudentSkill).filter_by(student_user_id=u.user_id, skill_id=sk_id).first():
                    db.add(StudentSkill(student_user_id=u.user_id, skill_id=sk_id, proficiency_level=prof, years_experience=yrs))

            # Student Domains
            for dom_name, priority, notes in s["domains"]:
                d_id = dom_map[dom_name]
                has_prio = db.query(StudentDomainInterest).filter_by(student_user_id=u.user_id, priority_order=priority).first()
                has_dom = db.query(StudentDomainInterest).filter_by(student_user_id=u.user_id, domain_id=d_id).first()
                if not has_prio and not has_dom:
                    db.add(StudentDomainInterest(student_user_id=u.user_id, domain_id=d_id, priority_order=priority, interest_notes=notes))

        db.commit()
        logger.info(f"Verified {len(students)} Student accounts and profiles.")

        # 6. Mentorship Requests (Target >= 10, creating 16)
        request_specs = [
            # 8 Requests that will become ACCEPTED (and have allocations)
            ("aarav.sharma@alumniconnect.edu", "rohit.verma@alumniconnect.edu", "Machine Learning & AI", "ACCEPTED", ANCHOR_NOW - timedelta(days=20), "Hi Rohit, I would love your mentorship guidance on production ML pipelines and recommendation architectures."),
            ("priya.patel@alumniconnect.edu", "sneha.rao@alumniconnect.edu", "Cloud Computing & DevOps", "ACCEPTED", ANCHOR_NOW - timedelta(days=18), "Hello Sneha, aiming to master Kubernetes multi-tenant clusters and infrastructure-as-code."),
            ("rohan.gupta@alumniconnect.edu", "vikram.joshi@alumniconnect.edu", "Full-Stack Web Engineering", "ACCEPTED", ANCHOR_NOW - timedelta(days=16), "Dear Vikram, looking for guidance on enterprise React/Next.js architecture and clean API contracts."),
            ("tanvi.shukla@alumniconnect.edu", "aditya.nair@alumniconnect.edu", "Data Engineering & Analytics", "ACCEPTED", ANCHOR_NOW - timedelta(days=15), "Hi Aditya, seeking advice on big data pipelines, Spark optimizations, and data platform design."),
            ("siddharth.menon@alumniconnect.edu", "meera.iyer@alumniconnect.edu", "Cloud Computing & DevOps", "ACCEPTED", ANCHOR_NOW - timedelta(days=14), "Hello Meera, wanting to learn high-availability systems, SRE observability, and cloud resilience."),
            ("varun.chatterjee@alumniconnect.edu", "neha.kulkarni@alumniconnect.edu", "Cybersecurity & Systems Security", "ACCEPTED", ANCHOR_NOW - timedelta(days=12), "Hi Neha, keen on learning AppSec threat modeling, secure code design, and penetration testing."),
            ("dev.kapoor@alumniconnect.edu", "ananya.deshmukh@alumniconnect.edu", "Competitive Programming & DSA Interview Prep", "ACCEPTED", ANCHOR_NOW - timedelta(days=10), "Hi Ananya, would love mock coding interviews and technical problem-solving evaluation."),
            ("isha.singh@alumniconnect.edu", "karthik.subramanian@alumniconnect.edu", "Distributed Systems & Microservices", "ACCEPTED", ANCHOR_NOW - timedelta(days=8), "Dear Karthik, interested in distributed transaction consistency, consensus algorithms, and ledger systems."),

            # 4 PENDING Requests (visible in mentor inboxes!)
            ("ananya.bhat@alumniconnect.edu", "rohit.verma@alumniconnect.edu", "Machine Learning & AI", "PENDING", ANCHOR_NOW - timedelta(days=2), "Hi Rohit, interested in research on transformer architectures and model pruning."),
            ("ritika.nambiar@alumniconnect.edu", "sneha.rao@alumniconnect.edu", "Cloud Computing & DevOps", "PENDING", ANCHOR_NOW - timedelta(days=1), "Hi Sneha, looking for guidance on IoT serverless architecture and MQTT cloud integration."),
            ("priya.patel@alumniconnect.edu", "meera.iyer@alumniconnect.edu", "Cloud Computing & DevOps", "PENDING", ANCHOR_NOW - timedelta(hours=12), "Hello Meera, seeking advice on SRE career paths and chaos engineering practices."),
            ("rohan.gupta@alumniconnect.edu", "karthik.subramanian@alumniconnect.edu", "Distributed Systems & Microservices", "PENDING", ANCHOR_NOW - timedelta(hours=6), "Hi Karthik, wanting to learn about distributed caching and read-replica replication."),

            # 2 REJECTED Requests
            ("siddharth.menon@alumniconnect.edu", "rohit.verma@alumniconnect.edu", "Machine Learning & AI", "REJECTED", ANCHOR_NOW - timedelta(days=25), "Requesting ML mentorship outside current capacity."),
            ("dev.kapoor@alumniconnect.edu", "vikram.joshi@alumniconnect.edu", "Full-Stack Web Engineering", "REJECTED", ANCHOR_NOW - timedelta(days=22), "Requesting web development guidance."),

            # 2 CANCELLED Requests
            ("aarav.sharma@alumniconnect.edu", "sneha.rao@alumniconnect.edu", "Cloud Computing & DevOps", "CANCELLED", ANCHOR_NOW - timedelta(days=24), "Student withdrew request due to academic exam preparation."),
            ("tanvi.shukla@alumniconnect.edu", "ananya.deshmukh@alumniconnect.edu", "Machine Learning & AI", "CANCELLED", ANCHOR_NOW - timedelta(days=21), "Student selected data engineering domain focus instead.")
        ]

        requests_dict = {}
        for s_email, m_email, dom_name, req_status, sub_time, msg in request_specs:
            s_user = students[s_email]
            m_user = mentors[m_email]
            d_id = dom_map[dom_name]
            idem_key = f"req:{s_user.user_id}:{m_user.user_id}:{d_id}:{req_status}"

            req = db.query(MentorshipRequest).filter_by(
                student_user_id=s_user.user_id,
                mentor_user_id=m_user.user_id,
                domain_id=d_id,
                request_status=req_status
            ).first()
            if not req:
                req = MentorshipRequest(
                    student_user_id=s_user.user_id,
                    mentor_user_id=m_user.user_id,
                    domain_id=d_id,
                    request_message=msg,
                    career_goal_snapshot=s_user.student_profile.career_goal,
                    request_status=req_status,
                    submitted_at=sub_time,
                    idempotency_key=idem_key
                )
                if req_status in ["ACCEPTED", "REJECTED"]:
                    req.decision_at = sub_time + timedelta(hours=4)
                    req.decided_by_user_id = m_user.user_id
                    req.decision_reason = "Accepted for ongoing mentorship" if req_status == "ACCEPTED" else "Schedule at capacity"
                elif req_status == "CANCELLED":
                    req.decision_at = sub_time + timedelta(hours=2)
                    req.decided_by_user_id = s_user.user_id
                    req.decision_reason = "Withdrawn by student"
                db.add(req)
                db.flush()
            requests_dict[(s_email, m_email, dom_name)] = req

        db.commit()
        logger.info(f"Verified {len(request_specs)} Mentorship Requests.")

        # 7. Mentor Allocations (Target >= 5, creating 8 for the 8 ACCEPTED requests)
        # 6 ACTIVE, 2 ENDED
        allocations_dict = {}
        accepted_keys = [k for k in requests_dict.keys() if requests_dict[k].request_status == "ACCEPTED"]
        for idx, key in enumerate(accepted_keys):
            req = requests_dict[key]
            alloc = db.query(MentorAllocation).filter_by(request_id=req.request_id).first()
            if not alloc:
                is_ended = idx >= 6  # 2 ended allocations
                status_val = "ENDED" if is_ended else "ACTIVE"
                alloc = MentorAllocation(
                    request_id=req.request_id,
                    allocation_status=status_val,
                    allocated_at=req.decision_at or (ANCHOR_NOW - timedelta(days=15)),
                    ended_at=(ANCHOR_NOW - timedelta(days=1)) if is_ended else None,
                    ended_by_user_id=req.mentor_user_id if is_ended else None,
                    termination_reason="Completed 6-month goal milestone" if is_ended else None
                )
                db.add(alloc)
                db.flush()
            allocations_dict[key] = alloc

        db.commit()
        logger.info(f"Verified {len(allocations_dict)} Mentor Allocations (6 Active, 2 Ended).")

        # 8. Mentor Availability Slots (Target >= 12, creating 24 slots across mentors)
        # Slots breakdown:
        # - 8 past BOOKED slots (for completed sessions)
        # - 4 future BOOKED slots (for upcoming confirmed bookings)
        # - 10 future OPEN slots (ready for booking)
        # - 2 CANCELLED slots
        slot_defs = [
            # Past slots (Booked for completed sessions)
            ("rohit.verma@alumniconnect.edu", ANCHOR_NOW - timedelta(days=12, hours=3), ANCHOR_NOW - timedelta(days=12, hours=2, minutes=15), "BOOKED"),
            ("sneha.rao@alumniconnect.edu", ANCHOR_NOW - timedelta(days=10, hours=5), ANCHOR_NOW - timedelta(days=10, hours=4, minutes=15), "BOOKED"),
            ("vikram.joshi@alumniconnect.edu", ANCHOR_NOW - timedelta(days=8, hours=2), ANCHOR_NOW - timedelta(days=8, hours=1, minutes=15), "BOOKED"),
            ("aditya.nair@alumniconnect.edu", ANCHOR_NOW - timedelta(days=6, hours=4), ANCHOR_NOW - timedelta(days=6, hours=3), "BOOKED"),
            ("meera.iyer@alumniconnect.edu", ANCHOR_NOW - timedelta(days=5, hours=6), ANCHOR_NOW - timedelta(days=5, hours=5, minutes=15), "BOOKED"),
            ("neha.kulkarni@alumniconnect.edu", ANCHOR_NOW - timedelta(days=4, hours=1), ANCHOR_NOW - timedelta(days=4, minutes=15), "BOOKED"),
            ("ananya.deshmukh@alumniconnect.edu", ANCHOR_NOW - timedelta(days=3, hours=5), ANCHOR_NOW - timedelta(days=3, hours=4, minutes=15), "BOOKED"),
            ("karthik.subramanian@alumniconnect.edu", ANCHOR_NOW - timedelta(days=2, hours=3), ANCHOR_NOW - timedelta(days=2, hours=2), "BOOKED"),

            # Future Booked slots (for upcoming confirmed appointments)
            ("rohit.verma@alumniconnect.edu", ANCHOR_NOW + timedelta(days=1, hours=2), ANCHOR_NOW + timedelta(days=1, hours=2, minutes=45), "BOOKED"),
            ("sneha.rao@alumniconnect.edu", ANCHOR_NOW + timedelta(days=2, hours=4), ANCHOR_NOW + timedelta(days=2, hours=4, minutes=45), "BOOKED"),
            ("vikram.joshi@alumniconnect.edu", ANCHOR_NOW + timedelta(days=3, hours=3), ANCHOR_NOW + timedelta(days=3, hours=4), "BOOKED"),
            ("aditya.nair@alumniconnect.edu", ANCHOR_NOW + timedelta(days=5, hours=5), ANCHOR_NOW + timedelta(days=5, hours=5, minutes=45), "BOOKED"),

            # Future OPEN slots (for student discovery & booking)
            ("rohit.verma@alumniconnect.edu", ANCHOR_NOW + timedelta(days=4, hours=2), ANCHOR_NOW + timedelta(days=4, hours=2, minutes=45), "OPEN"),
            ("rohit.verma@alumniconnect.edu", ANCHOR_NOW + timedelta(days=7, hours=3), ANCHOR_NOW + timedelta(days=7, hours=3, minutes=45), "OPEN"),
            ("sneha.rao@alumniconnect.edu", ANCHOR_NOW + timedelta(days=6, hours=1), ANCHOR_NOW + timedelta(days=6, hours=2), "OPEN"),
            ("sneha.rao@alumniconnect.edu", ANCHOR_NOW + timedelta(days=9, hours=4), ANCHOR_NOW + timedelta(days=9, hours=5), "OPEN"),
            ("vikram.joshi@alumniconnect.edu", ANCHOR_NOW + timedelta(days=5, hours=2), ANCHOR_NOW + timedelta(days=5, hours=3), "OPEN"),
            ("ananya.deshmukh@alumniconnect.edu", ANCHOR_NOW + timedelta(days=2, hours=6), ANCHOR_NOW + timedelta(days=2, hours=7), "OPEN"),
            ("ananya.deshmukh@alumniconnect.edu", ANCHOR_NOW + timedelta(days=8, hours=2), ANCHOR_NOW + timedelta(days=8, hours=3), "OPEN"),
            ("karthik.subramanian@alumniconnect.edu", ANCHOR_NOW + timedelta(days=6, hours=5), ANCHOR_NOW + timedelta(days=6, hours=6), "OPEN"),
            ("neha.kulkarni@alumniconnect.edu", ANCHOR_NOW + timedelta(days=4, hours=4), ANCHOR_NOW + timedelta(days=4, hours=5), "OPEN"),
            ("meera.iyer@alumniconnect.edu", ANCHOR_NOW + timedelta(days=7, hours=6), ANCHOR_NOW + timedelta(days=7, hours=7), "OPEN"),

            # Cancelled/Blocked slots
            ("rohit.verma@alumniconnect.edu", ANCHOR_NOW + timedelta(days=10, hours=2), ANCHOR_NOW + timedelta(days=10, hours=3), "CANCELLED"),
            ("vikram.joshi@alumniconnect.edu", ANCHOR_NOW + timedelta(days=11, hours=4), ANCHOR_NOW + timedelta(days=11, hours=5), "CANCELLED"),
        ]

        slots_list = []
        for m_email, start_t, end_t, st_val in slot_defs:
            m_user = mentors[m_email]
            slot = db.query(MentorAvailability).filter_by(
                mentor_user_id=m_user.user_id,
                starts_at=start_t,
                ends_at=end_t
            ).first()
            if not slot:
                slot = MentorAvailability(
                    mentor_user_id=m_user.user_id,
                    starts_at=start_t,
                    ends_at=end_t,
                    slot_status=st_val,
                    created_at=start_t - timedelta(days=5)
                )
                db.add(slot)
                db.flush()
            slots_list.append(slot)

        db.commit()
        logger.info(f"Verified {len(slots_list)} Mentor Availability slots.")

        # 9. Bookings (Target >= 10, creating 12 bookings)
        # - 7 Historical Completed bookings
        # - 4 Upcoming Confirmed bookings
        # - 1 Cancelled booking
        booking_specs = [
            # 7 Historical Completed Bookings
            (accepted_keys[0], slots_list[0], "MENTORSHIP", "CONFIRMED", slots_list[0].starts_at - timedelta(days=3), None, None),
            (accepted_keys[1], slots_list[1], "MOCK_INTERVIEW", "CONFIRMED", slots_list[1].starts_at - timedelta(days=3), None, None),
            (accepted_keys[2], slots_list[2], "MENTORSHIP", "CONFIRMED", slots_list[2].starts_at - timedelta(days=3), None, None),
            (accepted_keys[3], slots_list[3], "MOCK_INTERVIEW", "CONFIRMED", slots_list[3].starts_at - timedelta(days=2), None, None),
            (accepted_keys[4], slots_list[4], "MENTORSHIP", "CONFIRMED", slots_list[4].starts_at - timedelta(days=2), None, None),
            (accepted_keys[5], slots_list[5], "MOCK_INTERVIEW", "CONFIRMED", slots_list[5].starts_at - timedelta(days=2), None, None),
            (accepted_keys[6], slots_list[6], "MOCK_INTERVIEW", "CONFIRMED", slots_list[6].starts_at - timedelta(days=1), None, None),

            # 4 Upcoming Confirmed Bookings
            (accepted_keys[0], slots_list[8], "MENTORSHIP", "CONFIRMED", ANCHOR_NOW - timedelta(days=1), None, None),
            (accepted_keys[1], slots_list[9], "MOCK_INTERVIEW", "CONFIRMED", ANCHOR_NOW - timedelta(days=1), None, None),
            (accepted_keys[2], slots_list[10], "MENTORSHIP", "CONFIRMED", ANCHOR_NOW - timedelta(hours=12), None, None),
            (accepted_keys[3], slots_list[11], "MENTORSHIP", "CONFIRMED", ANCHOR_NOW - timedelta(hours=6), None, None),

            # 1 Cancelled Booking
            (accepted_keys[7], slots_list[7], "MENTORSHIP", "CANCELLED", slots_list[7].starts_at - timedelta(days=2), slots_list[7].starts_at - timedelta(days=1), "Student had university exam conflict")
        ]

        bookings_list = []
        for req_key, slot, b_type, b_status, b_time, c_time, c_reason in booking_specs:
            alloc = allocations_dict[req_key]
            idem = f"idem:book:{alloc.allocation_id}:{slot.availability_id}"
            booking = db.query(Booking).filter_by(idempotency_key=idem).first()
            if not booking:
                booking = Booking(
                    allocation_id=alloc.allocation_id,
                    availability_id=slot.availability_id,
                    booking_type=b_type,
                    booking_status=b_status,
                    booked_at=b_time,
                    cancelled_at=c_time,
                    cancelled_by_user_id=alloc.request.student_user_id if c_time else None,
                    cancellation_reason=c_reason,
                    idempotency_key=idem
                )
                db.add(booking)
                db.flush()
            bookings_list.append((booking, b_status))

        db.commit()
        logger.info(f"Verified {len(bookings_list)} Bookings.")

        # 10. Mentorship Sessions (Target >= 5 completed sessions, creating 12)
        # 7 COMPLETED sessions with realistic outcomes
        # 4 SCHEDULED upcoming sessions
        # 1 CANCELLED session
        session_outcomes = [
            {
                "discussion": "In-depth review of production machine learning architecture. Discussed model serving latency, quantization, and Redis feature caching strategies.",
                "observations": "Candidate demonstrates clear command of Python and data pipeline orchestration. Solid intuition on bias-variance tradeoff.",
                "improvement": "Needs deeper understanding of distributed model checkpointing, gradient accumulation, and Horovod/NCCL communications.",
                "next_steps": "Implement an end-to-end distributed training mock pipeline using PyTorch DistributedDataParallel and Docker.",
                "prep": "Read the Google Rules of Machine Learning and review matrix factorisation papers.",
                "skills": [("Python", "EXPERT", "Fluency in vectorization, profiling, and async queue consumers."),
                           ("Machine Learning", "PROFICIENT", "Good grasp of gradient descent and cross-entropy losses."),
                           ("SQL & RDBMS", "PROFICIENT", "Understands join planning and indexing on feature store tables.")]
            },
            {
                "discussion": "Mock architectural interview on cloud multi-region disaster recovery and Kubernetes cluster federations.",
                "observations": "Excellent articulation of RTO and RPO metrics. Explained Terraform module hierarchy and VPC peering cleanly.",
                "improvement": "Brush up on Kubernetes custom resource definitions (CRD) and ingress controller SSL termination nuances.",
                "next_steps": "Design and document a complete multi-cluster failover runbook with Route53 weighted health checks.",
                "prep": "Review AWS Well-Architected Framework Reliability Pillar.",
                "skills": [("Kubernetes", "PROFICIENT", "Demonstrated clear understanding of deployments and horizontal pod autoscalers."),
                           ("AWS", "EXPERT", "Strong architectural intuition on VPC subnetting and security groups.")]
            },
            {
                "discussion": "Full-stack code review and system design session for an interactive student dashboard.",
                "observations": "Strong TypeScript types, idiomatic React hooks, and clean separation between API client layer and presentation components.",
                "improvement": "Improve SSR cache-control headers and prevent layout shifts (CLS) on dynamic image loads.",
                "next_steps": "Implement Next.js server actions with optimistic UI mutations.",
                "prep": "Read React Server Components deep dive documentation.",
                "skills": [("React", "EXPERT", "Clean modular hook architecture and responsive Tailwind components."),
                           ("FastAPI", "PROFICIENT", "Understands Pydantic serialization models and dependency injection.")]
            },
            {
                "discussion": "Large-scale data engineering pipeline review: Apache Spark streaming vs batch lakehouse ingestion.",
                "observations": "Solid understanding of partition pruning, shuffle hash joins, and columnar Parquet file formats.",
                "improvement": "Analyze skew join mitigations using salting and broadcast join thresholds.",
                "next_steps": "Run benchmark tests comparing delta table compaction with raw Parquet partitions.",
                "prep": "Review Databricks Spark tuning guide.",
                "skills": [("Data Engineering & Spark", "PROFICIENT", "Understands RDD execution graphs and stage boundaries."),
                           ("SQL & RDBMS", "EXPERT", "Excellent complex window query syntax and analytical aggregation skills.")]
            },
            {
                "discussion": "Site Reliability Engineering mock interview: Incident triage, distributed tracing, and service level objectives (SLO).",
                "observations": "Calm, structured incident response methodology. Excellent use of golden signals (latency, traffic, errors, saturation).",
                "improvement": "Familiarize more with eBPF network tracing and Prometheus histogram bucket configuration.",
                "next_steps": "Build a Prometheus and Grafana alertmanager lab cluster locally.",
                "prep": "Read Google SRE Book chapter on Monitoring Distributed Systems.",
                "skills": [("Kubernetes", "EXPERT", "Deep knowledge of pod lifecycle and container resource limits."),
                           ("Distributed Systems", "PROFICIENT", "Clear grasp of bulkhead patterns and circuit breakers.")]
            },
            {
                "discussion": "Application security audit and threat modeling for a university authentication and RBAC portal.",
                "observations": "Identified OWASP Top 10 vulnerabilities accurately: IDOR risks, broken access controls, and CORS header misconfigurations.",
                "improvement": "Deepen practical experience with OAuth 2.1 PKCE flows and mutual TLS (mTLS).",
                "next_steps": "Write unit test suites verifying token expiration and role-boundary validation.",
                "prep": "Review OAuth 2.0 Security Best Current Practice RFC.",
                "skills": [("Cybersecurity & Cryptography", "EXPERT", "Sharp threat modeling and cryptographic primitive selection."),
                           ("Python", "PROFICIENT", "Analyzed Python security vulnerabilities and SQL injection guards.")]
            },
            {
                "discussion": "Competitive programming interview prep: Graph algorithms, lowest common ancestor (LCA), and Dijkstra variations.",
                "observations": "Exceptional coding speed and precision. Solved binary lifting problem in under 20 minutes with full proof.",
                "improvement": "Communicate algorithmic thoughts out loud before typing code in live whiteboard scenarios.",
                "next_steps": "Practice explaining time and space complexity trade-offs verbally while drafting code.",
                "prep": "Solve 10 hard problems on Codeforces focusing on flow networks.",
                "skills": [("Data Structures & Algorithms", "EXPERT", "Top-tier problem solving, optimal asymptotic complexity analysis."),
                           ("Python", "EXPERT", "Concise, bug-free implementation of complex graph traversals.")]
            }
        ]

        completed_sessions = []
        for idx, (booking, b_status) in enumerate(bookings_list):
            sess = db.query(MentorshipSession).filter_by(booking_id=booking.booking_id).first()
            if not sess:
                if b_status == "CANCELLED":
                    sess_status = "CANCELLED"
                elif idx < 7:
                    sess_status = "COMPLETED"
                else:
                    sess_status = "SCHEDULED"

                slot = booking.availability
                sess = MentorshipSession(
                    booking_id=booking.booking_id,
                    session_status=sess_status,
                    actual_start_at=slot.starts_at if sess_status == "COMPLETED" else None,
                    actual_end_at=slot.ends_at if sess_status == "COMPLETED" else None
                )
                if sess_status == "COMPLETED":
                    outcome = session_outcomes[idx]
                    sess.discussion_summary = outcome["discussion"]
                    sess.performance_observations = outcome["observations"]
                    sess.improvement_areas = outcome["improvement"]
                    sess.next_steps = outcome["next_steps"]
                    sess.preparation_recommendation = outcome["prep"]
                    sess.recorded_at = slot.ends_at + timedelta(minutes=15)
                    sess.recorded_by_user_id = booking.allocation.request.mentor_user_id

                db.add(sess)
                db.flush()

            if sess.session_status == "COMPLETED":
                completed_sessions.append((sess, session_outcomes[idx]))

        db.commit()
        logger.info(f"Verified Mentorship Sessions (7 Completed, 4 Scheduled, 1 Cancelled).")

        # 11. Session Skill Assessments (Target >= 5, creating ~18)
        for sess, outcome in completed_sessions:
            for sk_name, res_val, notes in outcome["skills"]:
                sk_id = skill_map[sk_name]
                sa = db.query(SessionSkillAssessment).filter_by(session_id=sess.session_id, skill_id=sk_id).first()
                if not sa:
                    sa = SessionSkillAssessment(
                        session_id=sess.session_id,
                        skill_id=sk_id,
                        assessment_result=res_val,
                        assessment_notes=notes
                    )
                    db.add(sa)

        db.commit()
        logger.info(f"Verified {db.query(SessionSkillAssessment).count()} Session Skill Assessments.")

        # 12. Session Feedback (Target >= 5, creating 12 two-way feedback records)
        for sess, _ in completed_sessions:
            req = sess.booking.allocation.request
            # Student feedback
            if not db.query(SessionFeedback).filter_by(session_id=sess.session_id, submitted_by_user_id=req.student_user_id).first():
                db.add(SessionFeedback(
                    session_id=sess.session_id,
                    submitted_by_user_id=req.student_user_id,
                    communication_rating=5,
                    helpfulness_rating=5,
                    technical_preparation_rating=5,
                    comments="The mentor provided exceptionally lucid explanations and tailored system design diagrams.",
                    submitted_at=sess.actual_end_at + timedelta(hours=1)
                ))
            # Mentor feedback
            if not db.query(SessionFeedback).filter_by(session_id=sess.session_id, submitted_by_user_id=req.mentor_user_id).first():
                db.add(SessionFeedback(
                    session_id=sess.session_id,
                    submitted_by_user_id=req.mentor_user_id,
                    communication_rating=5,
                    helpfulness_rating=4,
                    technical_preparation_rating=4,
                    comments="The mentee came well-prepared with specific questions and open to constructive feedback.",
                    submitted_at=sess.actual_end_at + timedelta(hours=2)
                ))

        db.commit()
        logger.info(f"Verified {db.query(SessionFeedback).count()} Session Feedback records.")

        # 13. Mentor Reviews (Target >= 5, creating 6 detailed student reviews)
        review_specs = [
            (5, "Rohit is an exceptional mentor! He walked me through Google's real-world ML infrastructure, helped identify bottlenecks in my recommendation pipeline code, and gave me high-yield interview practice questions. Highly recommended!"),
            (5, "Sneha's cloud architecture mock interview was one of the best technical sessions I've ever experienced. She challenged my assumptions on Kubernetes multi-tenancy and gave concrete career advice."),
            (4, "Vikram gave fantastic pointers on Next.js full-stack patterns and clean separation of concerns in React. Really grounded in enterprise software practices."),
            (5, "Aditya explained distributed data pipelines and Spark partitioning with incredible clarity. The best mentorship session for data engineers!"),
            (4, "Meera's insight into SRE principles and Kubernetes reliability changed how I think about systems resilience. Excellent actionable advice."),
            (5, "Neha's security audit breakdown opened my eyes to real-world attack vectors and defense-in-depth strategies. An incredible security mentor!")
        ]

        for idx, (rating_val, review_text) in enumerate(review_specs):
            sess, _ = completed_sessions[idx]
            rev = db.query(MentorReview).filter_by(session_id=sess.session_id).first()
            if not rev:
                rev = MentorReview(
                    session_id=sess.session_id,
                    rating=rating_val,
                    review_text=review_text,
                    submitted_at=sess.actual_end_at + timedelta(hours=3)
                )
                db.add(rev)

        db.commit()
        logger.info(f"Verified {db.query(MentorReview).count()} Mentor Reviews.")

        # 14. Recommendation Runs & Recommended Mentors (Target >= 5 runs, >= 20 recommendations)
        rec_runs_data = [
            ("aarav.sharma@alumniconnect.edu", "Machine Learning & High-Scale Systems", ["Machine Learning & AI", "Distributed Systems & Microservices"]),
            ("priya.patel@alumniconnect.edu", "Cloud DevOps & Kubernetes Orchestration", ["Cloud Computing & DevOps"]),
            ("rohan.gupta@alumniconnect.edu", "Full-Stack Web Architecture", ["Full-Stack Web Engineering", "Distributed Systems & Microservices"]),
            ("tanvi.shukla@alumniconnect.edu", "Data Engineering & Analytics Platforms", ["Data Engineering & Analytics"]),
            ("siddharth.menon@alumniconnect.edu", "Edge AI & Cloud Telemetry", ["Cloud Computing & DevOps", "Machine Learning & AI"]),
            ("varun.chatterjee@alumniconnect.edu", "Cybersecurity & Systems Defense", ["Cybersecurity & Systems Security"])
        ]

        all_mentor_list = list(mentors.values())
        for s_email, goal, target_domains in rec_runs_data:
            s_user = students[s_email]
            run = db.query(RecommendationRun).filter_by(student_user_id=s_user.user_id, input_goal=goal).first()
            if not run:
                run = RecommendationRun(
                    student_user_id=s_user.user_id,
                    input_goal=goal,
                    algorithm_version="v1.0-graph-weighted",
                    profile_version="v1",
                    filter_snapshot={"domains": target_domains},
                    executed_at=ANCHOR_NOW - timedelta(days=2)
                )
                db.add(run)
                db.flush()

                # Add 5 recommended mentors for this run
                ranked_mentors = sorted(all_mentor_list, key=lambda m: (m.mentor_profile.years_experience or 0), reverse=True)[:5]
                for rank_idx, m_u in enumerate(ranked_mentors, start=1):
                    score = round(95.0 - (rank_idx * 4.2), 2)
                    expl = f"Matched based on shared domain expertise in {target_domains[0]}, {m_u.mentor_profile.years_experience} years industry experience at {m_u.mentor_profile.company.company_name}, and alumni affiliation."
                    db.add(RecommendedMentor(
                        run_id=run.run_id,
                        mentor_user_id=m_u.user_id,
                        rank_position=rank_idx,
                        score=score,
                        eligibility_status="ELIGIBLE",
                        explanation_text=expl,
                        created_at=run.executed_at
                    ))

        db.commit()
        logger.info(f"Verified {db.query(RecommendationRun).count()} Recommendation Runs and {db.query(RecommendedMentor).count()} Recommended Mentors.")

        # 15. Notification Outbox & Delivered Notifications (Target >= 5)
        outbox_events = [
            ("MENTORSHIP_REQUEST", 1, "MENTORSHIP_REQUEST_SUBMITTED", {"student_user_id": 5, "mentor_user_id": 2, "student_name": "Aarav Sharma"}, "outbox:req_created:1:demo"),
            ("MENTORSHIP_REQUEST", 1, "MENTORSHIP_REQUEST_ACCEPTED", {"student_user_id": 5, "mentor_user_id": 2, "allocation_id": 1}, "outbox:req_accepted:1:demo"),
            ("BOOKING", 1, "BOOKING_CONFIRMED", {"booking_id": 1, "student_user_id": 5, "mentor_user_id": 2, "starts_at": (ANCHOR_NOW + timedelta(days=1)).isoformat()}, "outbox:book_confirmed:1:demo"),
            ("MENTORSHIP_SESSION", 1, "SESSION_OUTCOME_RECORDED", {"session_id": 1, "student_user_id": 5, "mentor_user_id": 2, "status": "COMPLETED"}, "outbox:sess_done:1:demo"),
            ("MENTOR_REVIEW", 1, "MENTOR_REVIEW_SUBMITTED", {"review_id": 1, "student_user_id": 5, "mentor_user_id": 2, "rating": 5}, "outbox:review_done:1:demo"),
            ("BOOKING", 2, "BOOKING_CONFIRMED", {"booking_id": 2, "student_user_id": 6, "mentor_user_id": 3, "starts_at": (ANCHOR_NOW + timedelta(days=2)).isoformat()}, "outbox:book_confirmed:2:demo"),
            ("MENTORSHIP_REQUEST", 2, "MENTORSHIP_REQUEST_ACCEPTED", {"student_user_id": 6, "mentor_user_id": 3, "allocation_id": 2}, "outbox:req_accepted:2:demo"),
        ]

        for agg_type, agg_id, ev_type, payload, dedupe in outbox_events:
            event = db.query(NotificationOutbox).filter_by(dedupe_key=dedupe).first()
            if not event:
                event = NotificationOutbox(
                    aggregate_type=agg_type,
                    aggregate_id=agg_id,
                    event_type=ev_type,
                    payload_json=payload,
                    delivery_status="SENT",
                    attempt_count=1,
                    created_at=ANCHOR_NOW - timedelta(days=2),
                    processed_at=ANCHOR_NOW - timedelta(days=2),
                    dedupe_key=dedupe
                )
                db.add(event)
                db.flush()

                # Fan-out to notification table
                s_id = payload.get("student_user_id")
                m_id = payload.get("mentor_user_id")
                if s_id and not db.query(Notification).filter_by(outbox_id=event.outbox_id, recipient_user_id=s_id).first():
                    db.add(Notification(
                        recipient_user_id=s_id,
                        outbox_id=event.outbox_id,
                        title=ev_type.replace("_", " ").title(),
                        body=f"Update regarding your {agg_type.lower()}: {ev_type}",
                        created_at=event.created_at,
                        read_at=ANCHOR_NOW - timedelta(days=1)
                    ))
                if m_id and not db.query(Notification).filter_by(outbox_id=event.outbox_id, recipient_user_id=m_id).first():
                    db.add(Notification(
                        recipient_user_id=m_id,
                        outbox_id=event.outbox_id,
                        title=ev_type.replace("_", " ").title(),
                        body=f"Update regarding mentorship action: {ev_type}",
                        created_at=event.created_at,
                        read_at=ANCHOR_NOW - timedelta(days=1)
                    ))

        db.commit()
        logger.info(f"Verified {db.query(NotificationOutbox).count()} Outbox records and {db.query(Notification).count()} Delivered Notifications.")

        # 16. Audit Log Entries (Target >= 5, creating 15+)
        audit_events = [
            (admin_user.user_id, "USER_ACCOUNT", admin_user.user_id, "LOGIN", {"status": "SUCCESS"}, "corr:user:admin:login"),
            (admin_user.user_id, "ROLE", 1, "INITIALIZE_CATALOGUES", {"roles": 3, "departments": 6}, "corr:catalog:init"),
            (mentors["rohit.verma@alumniconnect.edu"].user_id, "MENTOR_AVAILABILITY", 1, "PUBLISH_SLOT", {"status": "OPEN"}, "corr:avail:rohit:1"),
            (students["aarav.sharma@alumniconnect.edu"].user_id, "MENTORSHIP_REQUEST", 1, "SUBMIT_REQUEST", {"mentor_id": 2, "domain_id": 1}, "corr:req:aarav:rohit"),
            (mentors["rohit.verma@alumniconnect.edu"].user_id, "MENTORSHIP_REQUEST", 1, "ACCEPT_REQUEST", {"request_status": "ACCEPTED", "allocation_id": 1}, "corr:req:rohit:accept:1"),
            (students["aarav.sharma@alumniconnect.edu"].user_id, "BOOKING", 1, "CREATE_BOOKING", {"booking_type": "MENTORSHIP", "slot_id": 1}, "corr:book:aarav:1"),
            (mentors["rohit.verma@alumniconnect.edu"].user_id, "MENTORSHIP_SESSION", 1, "RECORD_OUTCOME", {"status": "COMPLETED", "ratings_logged": True}, "corr:sess:rohit:1"),
            (students["aarav.sharma@alumniconnect.edu"].user_id, "MENTOR_REVIEW", 1, "SUBMIT_REVIEW", {"rating": 5}, "corr:rev:aarav:1"),
            (students["priya.patel@alumniconnect.edu"].user_id, "MENTORSHIP_REQUEST", 2, "SUBMIT_REQUEST", {"mentor_id": 3, "domain_id": 2}, "corr:req:priya:sneha"),
            (mentors["sneha.rao@alumniconnect.edu"].user_id, "MENTORSHIP_REQUEST", 2, "ACCEPT_REQUEST", {"request_status": "ACCEPTED", "allocation_id": 2}, "corr:req:sneha:accept:2"),
            (students["priya.patel@alumniconnect.edu"].user_id, "BOOKING", 2, "CREATE_BOOKING", {"booking_type": "MOCK_INTERVIEW", "slot_id": 2}, "corr:book:priya:2"),
            (mentors["sneha.rao@alumniconnect.edu"].user_id, "MENTORSHIP_SESSION", 2, "RECORD_OUTCOME", {"status": "COMPLETED"}, "corr:sess:sneha:2"),
            (students["priya.patel@alumniconnect.edu"].user_id, "MENTOR_REVIEW", 2, "SUBMIT_REVIEW", {"rating": 5}, "corr:rev:priya:2"),
            (students["varun.chatterjee@alumniconnect.edu"].user_id, "BOOKING", 12, "CANCEL_BOOKING", {"reason": "Student had university exam conflict"}, "corr:book:varun:cancel:12")
        ]

        for actor_id, ent_type, ent_id, act, new_val, corr_id in audit_events:
            existing = db.query(AuditLog).filter_by(correlation_id=corr_id).first()
            if not existing:
                db.add(AuditLog(
                    actor_user_id=actor_id,
                    entity_type=ent_type,
                    entity_id=ent_id,
                    action=act,
                    new_values_json=new_val,
                    occurred_at=ANCHOR_NOW - timedelta(days=2),
                    correlation_id=corr_id
                ))

        db.commit()
        logger.info(f"Verified {db.query(AuditLog).count()} Audit Log records.")

        # 17. Synchronize Supporting Stores (Neo4j & Redis)
        logger.info("Synchronizing Graph Projection to Neo4j / In-Memory Graph Engine...")
        sync_graph_projection(db)

        # Invalidate / Pre-warm Redis / in-memory cache
        for m in db.query(MentorProfile).all():
            CacheService.invalidate_mentor_profile(m.user_id)
        logger.info("Supporting stores synchronized successfully.")

        # 18. Generate Final Record Counts
        all_tables = [
            "role", "department", "company", "skill", "mentorship_domain",
            "user_account", "student_profile", "mentor_profile",
            "student_skill", "mentor_skill", "student_domain_interest", "mentor_domain_expertise",
            "mentorship_request", "mentor_allocation", "mentor_availability",
            "booking", "mentorship_session", "session_skill_assessment",
            "session_feedback", "mentor_review", "recommendation_run",
            "recommended_mentor", "notification_outbox", "notification", "audit_log"
        ]

        print("\n" + "=" * 65)
        print("ALUMNICONNECT DATABASE SEEDING REPORT")
        print("=" * 65)
        print(f"{'Table':32} | {'Records':8} | {'Min Target':10} | {'Status'}")
        print("-" * 65)
        for tbl in sorted(all_tables):
            cnt = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            min_tgt = 3 if tbl == "role" else 5
            status = "PASS" if cnt >= min_tgt else "FAIL"
            print(f"{tbl:32} | {cnt:8} | {min_tgt:10} | {status}")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
