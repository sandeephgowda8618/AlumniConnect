"""AlumniConnect Database Initializer
Creates database schema, triggers/views, executes initial seed data,
and synchronizes initial projections into the graph engine.
"""

import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.database import engine, Base, SessionLocal
from app.models.entities import (
    Role, Department, Company, UserAccount,
    StudentProfile, MentorProfile, Skill, MentorshipDomain,
    StudentSkill, MentorSkill, StudentDomainInterest, MentorDomainExpertise,
    MentorAvailability
)
from app.core.graph_client import graph_client

logger = logging.getLogger("alumniconnect.init_db")


def init_db():
    """Initializes the authoritative database and projects reference data to graph."""
    logger.info("Initializing relational database schema...")
    
    # Create all tables defined in SQLAlchemy models
    Base.metadata.create_all(bind=engine)
    logger.info("Relational tables verified / created.")

    db = SessionLocal()
    try:
        # Check if roles are already seeded
        role_count = db.query(Role).count()
        if role_count == 0:
            logger.info("Seeding reference roles, departments, companies, skills, domains, and demo users...")
            
            # 1. Roles
            r_admin = Role(role_id=1, role_code="ADMINISTRATOR", role_name="System Administrator", description="Platform administration")
            r_mentor = Role(role_id=2, role_code="MENTOR", role_name="Alumni Mentor", description="Mentorship & mock interviews")
            r_student = Role(role_id=3, role_code="STUDENT", role_name="Student Mentee", description="Student exploring mentorship")
            db.add_all([r_admin, r_mentor, r_student])
            db.flush()

            # 2. Departments
            d_cse = Department(department_id=1, department_code="CSE", department_name="Computer Science and Engineering", institution_name="PES University")
            d_ece = Department(department_id=2, department_code="ECE", department_name="Electronics and Communication Engineering", institution_name="PES University")
            d_aiml = Department(department_id=3, department_code="AIML", department_name="Artificial Intelligence and Machine Learning", institution_name="PES University")
            d_ise = Department(department_id=4, department_code="ISE", department_name="Information Science and Engineering", institution_name="PES University")
            db.add_all([d_cse, d_ece, d_aiml, d_ise])
            db.flush()

            # 3. Companies
            c_goog = Company(company_id=1, company_name="Google", website_url="https://about.google", industry="Technology & AI")
            c_amzn = Company(company_id=2, company_name="Amazon", website_url="https://aboutamazon.com", industry="Cloud Computing & E-Commerce")
            c_msft = Company(company_id=3, company_name="Microsoft", website_url="https://microsoft.com", industry="Enterprise Software & Cloud")
            c_cisco = Company(company_id=4, company_name="Cisco Systems", website_url="https://cisco.com", industry="Networking & Security")
            c_gs = Company(company_id=5, company_name="Goldman Sachs", website_url="https://goldmansachs.com", industry="Financial Technology")
            db.add_all([c_goog, c_amzn, c_msft, c_cisco, c_gs])
            db.flush()

            # 4. Skills
            s_py = Skill(skill_id=1, skill_name="Python", category="Programming Languages", description="Core Python, concurrency, and async")
            s_sql = Skill(skill_id=2, skill_name="SQL & RDBMS", category="Databases", description="Relational design, indexing, transactions")
            s_ml = Skill(skill_id=3, skill_name="Machine Learning", category="Artificial Intelligence", description="Supervised/unsupervised algorithms")
            s_mlops = Skill(skill_id=4, skill_name="MLOps & CI/CD", category="DevOps & AI", description="Pipeline automation and containerization")
            s_docker = Skill(skill_id=5, skill_name="Docker", category="Containers", description="Containerization and compose orchestration")
            s_k8s = Skill(skill_id=6, skill_name="Kubernetes", category="Cloud Infrastructure", description="Container orchestration and clusters")
            s_aws = Skill(skill_id=7, skill_name="AWS", category="Cloud Providers", description="EC2, S3, RDS, VPC and IAM architecture")
            s_react = Skill(skill_id=8, skill_name="React", category="Frontend Development", description="React, TypeScript, state and Next.js")
            s_fastapi = Skill(skill_id=9, skill_name="FastAPI", category="Backend Development", description="Async Python API framework")
            s_dist = Skill(skill_id=10, skill_name="Distributed Systems", category="System Architecture", description="High-scale architectures, caching")
            s_dsa = Skill(skill_id=11, skill_name="Data Structures & Algorithms", category="Foundations", description="Algorithm analysis, interview prep")
            s_neo = Skill(skill_id=12, skill_name="Neo4j & Graph DB", category="Databases", description="Graph modeling and Cypher traversals")
            db.add_all([s_py, s_sql, s_ml, s_mlops, s_docker, s_k8s, s_aws, s_react, s_fastapi, s_dist, s_dsa, s_neo])
            db.flush()

            # 5. Mentorship Domains
            dom_ml = MentorshipDomain(domain_id=1, domain_name="Machine Learning & AI", description="Predictive modeling, deep learning, NLP")
            dom_cloud = MentorshipDomain(domain_id=2, domain_name="Cloud Computing & DevOps", description="Cloud architecture, Kubernetes, CI/CD")
            dom_web = MentorshipDomain(domain_id=3, domain_name="Full-Stack Web Engineering", description="Modern frontend, REST APIs, auth")
            dom_dist = MentorshipDomain(domain_id=4, domain_name="Distributed Systems & Microservices", description="High-scale systems, caching, consistency")
            dom_data = MentorshipDomain(domain_id=5, domain_name="Data Engineering & Analytics", description="ETL pipelines, data warehousing")
            db.add_all([dom_ml, dom_cloud, dom_web, dom_dist, dom_data])
            db.flush()

            # 6. Demo Users (Password: Password123!)
            bcrypt_pwd = "$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a"

            # Admin
            u_admin = UserAccount(user_id=1, role_id=1, email="admin@alumniconnect.edu", password_hash=bcrypt_pwd, display_name="Dr. Radhika Sen (Admin)", account_status="ACTIVE")
            # Mentor 1: Rohit Verma
            u_rohit = UserAccount(user_id=2, role_id=2, email="rohit.verma@alumniconnect.edu", password_hash=bcrypt_pwd, display_name="Rohit Verma", account_status="ACTIVE")
            # Mentor 2: Sneha Rao
            u_sneha = UserAccount(user_id=3, role_id=2, email="sneha.rao@alumniconnect.edu", password_hash=bcrypt_pwd, display_name="Sneha Rao", account_status="ACTIVE")
            # Mentor 3: Vikram Joshi
            u_vikram = UserAccount(user_id=4, role_id=2, email="vikram.joshi@alumniconnect.edu", password_hash=bcrypt_pwd, display_name="Vikram Joshi", account_status="ACTIVE")
            # Student 1: Aarav Sharma
            u_aarav = UserAccount(user_id=5, role_id=3, email="aarav.sharma@alumniconnect.edu", password_hash=bcrypt_pwd, display_name="Aarav Sharma", account_status="ACTIVE")
            # Student 2: Priya Patel
            u_priya = UserAccount(user_id=6, role_id=3, email="priya.patel@alumniconnect.edu", password_hash=bcrypt_pwd, display_name="Priya Patel", account_status="ACTIVE")

            db.add_all([u_admin, u_rohit, u_sneha, u_vikram, u_aarav, u_priya])
            db.flush()

            # Profiles
            p_rohit = MentorProfile(
                user_id=2, alumni_identifier="ALUM-2019-CSE-042", alumni_department_id=1, current_company_id=1,
                job_title="Senior Machine Learning Engineer", years_experience=5.5, max_active_mentees=3, accepting_requests=True,
                professional_summary="Alumnus of CSE (Batch 2019). Senior ML Engineer at Google working on large-scale recommendation systems."
            )
            p_sneha = MentorProfile(
                user_id=3, alumni_identifier="ALUM-2018-ISE-108", alumni_department_id=4, current_company_id=2,
                job_title="Principal Solutions Architect", years_experience=6.5, max_active_mentees=2, accepting_requests=True,
                professional_summary="Alumna of ISE (Batch 2018). Cloud systems and Kubernetes specialist at AWS."
            )
            p_vikram = MentorProfile(
                user_id=4, alumni_identifier="ALUM-2020-CSE-091", alumni_department_id=1, current_company_id=3,
                job_title="Lead Software Engineer", years_experience=4.0, max_active_mentees=2, accepting_requests=True,
                professional_summary="Full-stack software architect at Microsoft working on modern enterprise web applications and API platforms."
            )
            p_aarav = StudentProfile(
                user_id=5, student_number="PES1UG22CS001", department_id=1, programme="B.Tech in Computer Science and Engineering",
                batch_year=2022, expected_graduation_year=2026, career_goal="Machine Learning Engineer",
                bio="Third-year CSE student passionate about machine learning, databases, and distributed systems."
            )
            p_priya = StudentProfile(
                user_id=6, student_number="PES1UG23AM015", department_id=3, programme="B.Tech in Artificial Intelligence and Machine Learning",
                batch_year=2023, expected_graduation_year=2027, career_goal="Cloud DevOps and AI Platform Engineer",
                bio="Second-year AIML student working on containerization, computer vision, and cloud platforms."
            )
            db.add_all([p_rohit, p_sneha, p_vikram, p_aarav, p_priya])
            db.flush()

            # Mentor Skills
            db.add_all([
                MentorSkill(mentor_user_id=2, skill_id=1, proficiency_level="EXPERT", years_experience=5.5),
                MentorSkill(mentor_user_id=2, skill_id=3, proficiency_level="EXPERT", years_experience=5.0),
                MentorSkill(mentor_user_id=2, skill_id=4, proficiency_level="ADVANCED", years_experience=3.5),
                MentorSkill(mentor_user_id=2, skill_id=5, proficiency_level="INTERMEDIATE", years_experience=3.0),
                MentorSkill(mentor_user_id=3, skill_id=7, proficiency_level="EXPERT", years_experience=6.5),
                MentorSkill(mentor_user_id=3, skill_id=6, proficiency_level="EXPERT", years_experience=5.0),
                MentorSkill(mentor_user_id=3, skill_id=10, proficiency_level="ADVANCED", years_experience=4.5),
                MentorSkill(mentor_user_id=4, skill_id=8, proficiency_level="EXPERT", years_experience=4.0),
                MentorSkill(mentor_user_id=4, skill_id=9, proficiency_level="ADVANCED", years_experience=3.5),
                MentorSkill(mentor_user_id=4, skill_id=2, proficiency_level="ADVANCED", years_experience=4.0),
            ])

            # Mentor Domains
            db.add_all([
                MentorDomainExpertise(mentor_user_id=2, domain_id=1, expertise_level="EXPERT", years_experience=5.5, is_primary=True),
                MentorDomainExpertise(mentor_user_id=2, domain_id=5, expertise_level="ADVANCED", years_experience=3.5, is_primary=False),
                MentorDomainExpertise(mentor_user_id=3, domain_id=2, expertise_level="EXPERT", years_experience=6.5, is_primary=True),
                MentorDomainExpertise(mentor_user_id=3, domain_id=4, expertise_level="ADVANCED", years_experience=4.5, is_primary=False),
                MentorDomainExpertise(mentor_user_id=4, domain_id=3, expertise_level="EXPERT", years_experience=4.0, is_primary=True),
            ])

            # Student Skills
            db.add_all([
                StudentSkill(student_user_id=5, skill_id=1, proficiency_level="INTERMEDIATE", years_experience=2.0),
                StudentSkill(student_user_id=5, skill_id=2, proficiency_level="INTERMEDIATE", years_experience=1.5),
                StudentSkill(student_user_id=5, skill_id=3, proficiency_level="BEGINNER", years_experience=1.0),
                StudentSkill(student_user_id=6, skill_id=1, proficiency_level="INTERMEDIATE", years_experience=1.5),
                StudentSkill(student_user_id=6, skill_id=7, proficiency_level="BEGINNER", years_experience=0.5),
            ])

            # Student Domain Interests
            db.add_all([
                StudentDomainInterest(student_user_id=5, domain_id=1, priority_order=1, interest_notes="Wants to master production ML."),
                StudentDomainInterest(student_user_id=5, domain_id=2, priority_order=2, interest_notes="Interested in deploying ML on cloud."),
                StudentDomainInterest(student_user_id=6, domain_id=2, priority_order=1, interest_notes="Focusing on Kubernetes and microservices."),
            ])

            # Sample Availability for Rohit Verma (User ID 2)
            from datetime import timedelta
            now = datetime.utcnow()
            db.add_all([
                MentorAvailability(availability_id=1, mentor_user_id=2, starts_at=now + timedelta(days=2), ends_at=now + timedelta(days=2, minutes=45), slot_status="OPEN"),
                MentorAvailability(availability_id=2, mentor_user_id=2, starts_at=now + timedelta(days=4), ends_at=now + timedelta(days=4, minutes=45), slot_status="OPEN"),
                MentorAvailability(availability_id=3, mentor_user_id=3, starts_at=now + timedelta(days=3), ends_at=now + timedelta(days=3, minutes=60), slot_status="OPEN")
            ])

            db.commit()
            logger.info("Database successfully seeded.")

        # Project reference data into graph engine
        sync_graph_projection(db)

    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()


def sync_graph_projection(db):
    """Synchronizes relational entities into the graph engine for traversal discovery."""
    try:
        # Clear and repopulate graph nodes
        graph_client.engine.clear()

        # Users & Profiles
        users = db.query(UserAccount).all()
        for u in users:
            graph_client.engine.upsert_user(u.user_id, u.display_name, u.account_status)

        # Departments & Companies
        for d in db.query(Department).all():
            graph_client.engine.upsert_department(d.department_id, d.department_name, d.department_code)
        for c in db.query(Company).all():
            graph_client.engine.upsert_company(c.company_id, c.company_name, c.industry or "")

        # Skills & Domains
        for s in db.query(Skill).all():
            graph_client.engine.upsert_skill(s.skill_id, s.skill_name, s.category or "")
        for dom in db.query(MentorshipDomain).all():
            graph_client.engine.upsert_domain(dom.domain_id, dom.domain_name, dom.description or "")

        # Students
        for sp in db.query(StudentProfile).all():
            graph_client.engine.upsert_student(sp.user_id, sp.user_id, sp.department_id, sp.programme, sp.expected_graduation_year or 0)
        
        # Student Skills & Domains
        for ss in db.query(StudentSkill).all():
            graph_client.engine.set_student_skill(ss.student_user_id, ss.skill_id, ss.proficiency_level, float(ss.years_experience or 0))
        for sdi in db.query(StudentDomainInterest).all():
            graph_client.engine.set_student_domain_interest(sdi.student_user_id, sdi.domain_id, sdi.priority_order)

        # Mentors
        for mp in db.query(MentorProfile).all():
            graph_client.engine.upsert_mentor(mp.user_id, mp.user_id, mp.alumni_department_id, mp.current_company_id, mp.job_title, float(mp.years_experience or 0))

        # Mentor Skills & Domains
        for ms in db.query(MentorSkill).all():
            graph_client.engine.set_mentor_skill(ms.mentor_user_id, ms.skill_id, ms.proficiency_level, float(ms.years_experience or 0))
        for mde in db.query(MentorDomainExpertise).all():
            graph_client.engine.set_mentor_domain_expertise(mde.mentor_user_id, mde.domain_id, mde.expertise_level, mde.is_primary)

        logger.info("Graph projection synchronization completed successfully.")
    except Exception as e:
        logger.error(f"Error during graph synchronization: {e}")
