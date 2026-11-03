-- AlumniConnect Seed Reference & Demo Data (MySQL 8.x / InnoDB)
-- Password for all demo accounts: Password123!

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Roles
INSERT INTO role (role_id, role_code, role_name, description, is_active) VALUES
(1, 'ADMINISTRATOR', 'System Administrator', 'Platform oversight, user management, catalogue maintenance and reporting.', TRUE),
(2, 'MENTOR', 'Alumni Mentor', 'Provides mentorship, mock interviews, slot availability, and session evaluations.', TRUE),
(3, 'STUDENT', 'Student Mentee', 'Discovers mentors, books eligible sessions, submits requests, and provides feedback.', TRUE)
ON DUPLICATE KEY UPDATE role_name = VALUES(role_name);

-- 2. Departments
INSERT INTO department (department_id, department_code, department_name, institution_name) VALUES
(1, 'CSE', 'Computer Science and Engineering', 'PES University'),
(2, 'ECE', 'Electronics and Communication Engineering', 'PES University'),
(3, 'AIML', 'Artificial Intelligence and Machine Learning', 'PES University'),
(4, 'ISE', 'Information Science and Engineering', 'PES University')
ON DUPLICATE KEY UPDATE department_name = VALUES(department_name);

-- 3. Companies
INSERT INTO company (company_id, company_name, website_url, industry) VALUES
(1, 'Google', 'https://about.google', 'Technology & AI'),
(2, 'Amazon', 'https://aboutamazon.com', 'Cloud Computing & E-Commerce'),
(3, 'Microsoft', 'https://microsoft.com', 'Enterprise Software & Cloud'),
(4, 'Cisco Systems', 'https://cisco.com', 'Networking & Security'),
(5, 'Goldman Sachs', 'https://goldmansachs.com', 'Financial Technology')
ON DUPLICATE KEY UPDATE company_name = VALUES(company_name);

-- 4. Skills Catalogue
INSERT INTO skill (skill_id, skill_name, category, description) VALUES
(1, 'Python', 'Programming Languages', 'Core Python, concurrency, object-oriented design and async programming.'),
(2, 'SQL & RDBMS', 'Databases', 'Relational design, indexing, transactions, stored procedures and query optimization.'),
(3, 'Machine Learning', 'Artificial Intelligence', 'Supervised/unsupervised algorithms, evaluation metrics and feature engineering.'),
(4, 'MLOps & CI/CD', 'DevOps & AI', 'Pipeline automation, model registry, containerization and tracking.'),
(5, 'Docker', 'Containers & Infrastructure', 'Container creation, multi-stage builds, and compose orchestration.'),
(6, 'Kubernetes', 'Cloud Infrastructure', 'Container orchestration, deployments, services and cluster administration.'),
(7, 'AWS', 'Cloud Providers', 'EC2, S3, RDS, Lambda, VPC and IAM architecture.'),
(8, 'React', 'Frontend Development', 'Component architecture, state management, hooks and Next.js integration.'),
(9, 'FastAPI', 'Backend Development', 'High-performance asynchronous Python API framework with Pydantic.'),
(10, 'Distributed Systems', 'System Architecture', 'Consensus, caching strategies, replication and high-availability patterns.'),
(11, 'Data Structures & Algorithms', 'Foundations', 'Algorithm analysis, tree/graph traversal, and technical interview prep.'),
(12, 'Neo4j & Graph DB', 'Databases', 'Graph modeling, Cypher query optimization, and traversal algorithms.')
ON DUPLICATE KEY UPDATE skill_name = VALUES(skill_name);

-- 5. Mentorship Domains
INSERT INTO mentorship_domain (domain_id, domain_name, description) VALUES
(1, 'Machine Learning & AI', 'Predictive modeling, deep learning, computer vision, NLP and generative models.'),
(2, 'Cloud Computing & DevOps', 'Cloud architecture, Kubernetes orchestration, infrastructure as code and SRE.'),
(3, 'Full-Stack Web Engineering', 'Modern frontend architectures, REST/GraphQL APIs, relational modeling and auth.'),
(4, 'Distributed Systems & Microservices', 'High-scale architectures, event-driven systems, caching and consistency.'),
(5, 'Data Engineering & Analytics', 'ETL pipelines, data warehousing, stream processing and analytics workflows.')
ON DUPLICATE KEY UPDATE domain_name = VALUES(domain_name);

-- 6. Demo Users (Password: Password123!)
-- Bcrypt Hash: $2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a

-- Admin Account (User ID 1)
INSERT INTO user_account (user_id, role_id, email, password_hash, display_name, account_status) VALUES
(1, 1, 'admin@alumniconnect.edu', '$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a', 'Dr. Radhika Sen (Admin)', 'ACTIVE')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

-- Mentor 1: Rohit Verma (Google ML Engineer, User ID 2)
INSERT INTO user_account (user_id, role_id, email, password_hash, display_name, account_status) VALUES
(2, 2, 'rohit.verma@alumniconnect.edu', '$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a', 'Rohit Verma', 'ACTIVE')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

INSERT INTO mentor_profile (user_id, alumni_identifier, alumni_department_id, current_company_id, job_title, years_experience, max_active_mentees, accepting_requests, professional_summary) VALUES
(2, 'ALUM-2019-CSE-042', 1, 1, 'Senior Machine Learning Engineer', 5.5, 3, TRUE, 'Alumnus of CSE (Batch 2019). Currently working on large-scale machine learning and recommendation infrastructure at Google. Passionate about helping students crack technical interviews and master ML engineering fundamentals.')
ON DUPLICATE KEY UPDATE job_title = VALUES(job_title);

-- Mentor 2: Sneha Rao (Amazon Cloud Architect, User ID 3)
INSERT INTO user_account (user_id, role_id, email, password_hash, display_name, account_status) VALUES
(3, 2, 'sneha.rao@alumniconnect.edu', '$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a', 'Sneha Rao', 'ACTIVE')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

INSERT INTO mentor_profile (user_id, alumni_identifier, alumni_department_id, current_company_id, job_title, years_experience, max_active_mentees, accepting_requests, professional_summary) VALUES
(3, 'ALUM-2018-ISE-108', 4, 2, 'Principal Solutions Architect', 6.5, 2, TRUE, 'Alumna of ISE (Batch 2018). Cloud systems and Kubernetes specialist at AWS. Helping students with distributed systems architecture, cloud infrastructure, and career transitions into DevOps/SRE.')
ON DUPLICATE KEY UPDATE job_title = VALUES(job_title);

-- Mentor 3: Vikram Joshi (Microsoft Full-Stack Lead, User ID 4)
INSERT INTO user_account (user_id, role_id, email, password_hash, display_name, account_status) VALUES
(4, 2, 'vikram.joshi@alumniconnect.edu', '$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a', 'Vikram Joshi', 'ACTIVE')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

INSERT INTO mentor_profile (user_id, alumni_identifier, alumni_department_id, current_company_id, job_title, years_experience, max_active_mentees, accepting_requests, professional_summary) VALUES
(4, 'ALUM-2020-CSE-091', 1, 3, 'Lead Software Engineer', 4.0, 2, TRUE, 'Full-stack software architect at Microsoft working on modern enterprise web applications and API platforms using Next.js and Python.')
ON DUPLICATE KEY UPDATE job_title = VALUES(job_title);

-- Student 1: Aarav Sharma (User ID 5)
INSERT INTO user_account (user_id, role_id, email, password_hash, display_name, account_status) VALUES
(5, 3, 'aarav.sharma@alumniconnect.edu', '$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a', 'Aarav Sharma', 'ACTIVE')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

INSERT INTO student_profile (user_id, student_number, department_id, programme, batch_year, expected_graduation_year, career_goal, bio) VALUES
(5, 'PES1UG22CS001', 1, 'B.Tech in Computer Science and Engineering', 2022, 2026, 'Aspiring Machine Learning and Systems Software Engineer targeting high-impact tech companies.', 'Third-year CSE student interested in machine learning algorithms, database internals, and backend microservices.')
ON DUPLICATE KEY UPDATE career_goal = VALUES(career_goal);

-- Student 2: Priya Patel (User ID 6)
INSERT INTO user_account (user_id, role_id, email, password_hash, display_name, account_status) VALUES
(6, 3, 'priya.patel@alumniconnect.edu', '$2b$12$ihdRxBXWIfqRX9FBMzxwq.0yJx8qwghzNp8l9O5l2usXB/OvG.L9a', 'Priya Patel', 'ACTIVE')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);

INSERT INTO student_profile (user_id, student_number, department_id, programme, batch_year, expected_graduation_year, career_goal, bio) VALUES
(6, 'PES1UG23AM015', 3, 'B.Tech in Artificial Intelligence and Machine Learning', 2023, 2027, 'Targeting roles in Cloud DevOps and scalable Machine Learning platforms.', 'Second-year AIML student working on computer vision and cloud infrastructure projects.')
ON DUPLICATE KEY UPDATE career_goal = VALUES(career_goal);

-- 7. Mentor Skills
-- Rohit Verma: Python (Expert, 5.5y), Machine Learning (Expert, 5.0y), MLOps (Advanced, 3.5y), Docker (Intermediate, 3.0y)
INSERT INTO mentor_skill (mentor_user_id, skill_id, proficiency_level, years_experience) VALUES
(2, 1, 'EXPERT', 5.5),
(2, 3, 'EXPERT', 5.0),
(2, 4, 'ADVANCED', 3.5),
(2, 5, 'INTERMEDIATE', 3.0)
ON DUPLICATE KEY UPDATE proficiency_level = VALUES(proficiency_level);

-- Sneha Rao: AWS (EXPERT, 6.5y), Kubernetes (EXPERT, 5.0y), Distributed Systems (ADVANCED, 4.5y), Docker (ADVANCED, 4.0y)
INSERT INTO mentor_skill (mentor_user_id, skill_id, proficiency_level, years_experience) VALUES
(3, 7, 'EXPERT', 6.5),
(3, 6, 'EXPERT', 5.0),
(3, 10, 'ADVANCED', 4.5),
(3, 5, 'ADVANCED', 4.0)
ON DUPLICATE KEY UPDATE proficiency_level = VALUES(proficiency_level);

-- Vikram Joshi: React (EXPERT, 4.0y), FastAPI (ADVANCED, 3.5y), SQL & RDBMS (ADVANCED, 4.0y), Python (ADVANCED, 3.5y)
INSERT INTO mentor_skill (mentor_user_id, skill_id, proficiency_level, years_experience) VALUES
(4, 8, 'EXPERT', 4.0),
(4, 9, 'ADVANCED', 3.5),
(4, 2, 'ADVANCED', 4.0),
(4, 1, 'ADVANCED', 3.5)
ON DUPLICATE KEY UPDATE proficiency_level = VALUES(proficiency_level);

-- 8. Mentor Domain Expertise
INSERT INTO mentor_domain_expertise (mentor_user_id, domain_id, expertise_level, years_experience, is_primary) VALUES
(2, 1, 'EXPERT', 5.5, TRUE),
(2, 5, 'ADVANCED', 3.5, FALSE),
(3, 2, 'EXPERT', 6.5, TRUE),
(3, 4, 'ADVANCED', 4.5, FALSE),
(4, 3, 'EXPERT', 4.0, TRUE),
(4, 4, 'INTERMEDIATE', 2.5, FALSE)
ON DUPLICATE KEY UPDATE expertise_level = VALUES(expertise_level);

-- 9. Student Skills
-- Aarav: Python (Intermediate), SQL & RDBMS (Intermediate), Machine Learning (Beginner)
INSERT INTO student_skill (student_user_id, skill_id, proficiency_level, years_experience) VALUES
(5, 1, 'INTERMEDIATE', 2.0),
(5, 2, 'INTERMEDIATE', 1.5),
(5, 3, 'BEGINNER', 1.0)
ON DUPLICATE KEY UPDATE proficiency_level = VALUES(proficiency_level);

-- Priya: Python (Intermediate), Cloud Computing (Beginner)
INSERT INTO student_skill (student_user_id, skill_id, proficiency_level, years_experience) VALUES
(6, 1, 'INTERMEDIATE', 1.5),
(6, 7, 'BEGINNER', 0.5)
ON DUPLICATE KEY UPDATE proficiency_level = VALUES(proficiency_level);

-- 10. Student Domain Interests
-- Aarav: Priority 1 Machine Learning & AI, Priority 2 Cloud Computing & DevOps
INSERT INTO student_domain_interest (student_user_id, domain_id, priority_order, interest_notes) VALUES
(5, 1, 1, 'Wants to master production ML engineering and MLOps deployment.'),
(5, 2, 2, 'Interested in deploying scalable ML models on cloud infrastructure.')
ON DUPLICATE KEY UPDATE interest_notes = VALUES(interest_notes);

-- Priya: Priority 1 Cloud Computing & DevOps
INSERT INTO student_domain_interest (student_user_id, domain_id, priority_order, interest_notes) VALUES
(6, 2, 1, 'Focusing on Kubernetes and microservices orchestration.')
ON DUPLICATE KEY UPDATE interest_notes = VALUES(interest_notes);

-- 11. Initial Sample Availability Slots for Mentor Rohit Verma (User ID 2)
INSERT INTO mentor_availability (availability_id, mentor_user_id, starts_at, ends_at, slot_status) VALUES
(1, 2, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 2 DAY), DATE_ADD(DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 2 DAY), INTERVAL 45 MINUTE), 'OPEN'),
(2, 2, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 4 DAY), DATE_ADD(DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 4 DAY), INTERVAL 45 MINUTE), 'OPEN'),
(3, 3, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 3 DAY), DATE_ADD(DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 3 DAY), INTERVAL 60 MINUTE), 'OPEN')
ON DUPLICATE KEY UPDATE slot_status = VALUES(slot_status);

SET FOREIGN_KEY_CHECKS = 1;

