"""AlumniConnect Neo4j Graph Client & Resilient In-Memory Graph Fallback
Implements the Neo4j Graph Design Specification:
- Node labels: User, Student, Mentor, Skill, Domain, Company, Department
- Edge labels: HAS_STUDENT_PROFILE, HAS_MENTOR_PROFILE, HAS_SKILL, SPECIALIZES_IN,
  INTERESTED_IN, WORKS_AT, BELONGS_TO, MENTORED_BY
Uses official neo4j driver if connected; otherwise falls back to a high-performance NetworkX graph
to guarantee that graph traversal and relationship-based candidate discovery always succeed.
"""

import logging
from typing import Any, Dict, List, Optional, Set
import networkx as nx

from app.core.config import settings

logger = logging.getLogger("alumniconnect.graph")


class InMemoryGraphEngine:
    """NetworkX-powered graph engine mirroring AlumniConnect Neo4j schema & traversals."""
    def __init__(self):
        self.g = nx.DiGraph()

    def clear(self):
        self.g.clear()

    # --- Schema & Upsert Operations ---

    def upsert_user(self, user_id: int, display_name: str, account_status: str):
        node_id = f"User:{user_id}"
        self.g.add_node(
            node_id,
            label="User",
            userId=user_id,
            displayName=display_name,
            accountStatus=account_status
        )

    def upsert_student(self, student_id: int, user_id: int, department_id: int,
                       programme: str = "", graduation_year: int = 0):
        s_node = f"Student:{student_id}"
        u_node = f"User:{user_id}"
        dept_node = f"Department:{department_id}"

        self.g.add_node(
            s_node,
            label="Student",
            studentId=student_id,
            userId=user_id,
            programme=programme,
            graduationYear=graduation_year
        )
        if self.g.has_node(u_node):
            self.g.add_edge(u_node, s_node, type="HAS_STUDENT_PROFILE")
        if self.g.has_node(dept_node):
            self.g.add_edge(s_node, dept_node, type="BELONGS_TO")

    def upsert_mentor(self, mentor_id: int, user_id: int, department_id: int,
                      company_id: Optional[int] = None, job_title: str = "",
                      years_experience: float = 0.0):
        m_node = f"Mentor:{mentor_id}"
        u_node = f"User:{user_id}"
        dept_node = f"Department:{department_id}"

        self.g.add_node(
            m_node,
            label="Mentor",
            mentorId=mentor_id,
            userId=user_id,
            jobTitle=job_title,
            yearsExperience=years_experience
        )
        if self.g.has_node(u_node):
            self.g.add_edge(u_node, m_node, type="HAS_MENTOR_PROFILE")
        if self.g.has_node(dept_node):
            self.g.add_edge(m_node, dept_node, type="BELONGS_TO")
        if company_id:
            comp_node = f"Company:{company_id}"
            if self.g.has_node(comp_node):
                self.g.add_edge(m_node, comp_node, type="WORKS_AT", jobTitle=job_title)

    def upsert_skill(self, skill_id: int, name: str, category: str = ""):
        node_id = f"Skill:{skill_id}"
        self.g.add_node(node_id, label="Skill", skillId=skill_id, name=name, category=category)

    def upsert_domain(self, domain_id: int, name: str, description: str = ""):
        node_id = f"Domain:{domain_id}"
        self.g.add_node(node_id, label="Domain", domainId=domain_id, name=name, description=description)

    def upsert_department(self, department_id: int, name: str, code: str = ""):
        node_id = f"Department:{department_id}"
        self.g.add_node(node_id, label="Department", departmentId=department_id, name=name, code=code)

    def upsert_company(self, company_id: int, name: str, industry: str = ""):
        node_id = f"Company:{company_id}"
        self.g.add_node(node_id, label="Company", companyId=company_id, name=name, industry=industry)

    def set_student_skill(self, student_id: int, skill_id: int, proficiency: str, years: float = 0.0):
        s_node = f"Student:{student_id}"
        sk_node = f"Skill:{skill_id}"
        if self.g.has_node(s_node) and self.g.has_node(sk_node):
            self.g.add_edge(s_node, sk_node, type="HAS_SKILL", proficiency=proficiency, yearsExperience=years)

    def set_mentor_skill(self, mentor_id: int, skill_id: int, proficiency: str, years: float = 0.0):
        m_node = f"Mentor:{mentor_id}"
        sk_node = f"Skill:{skill_id}"
        if self.g.has_node(m_node) and self.g.has_node(sk_node):
            self.g.add_edge(m_node, sk_node, type="HAS_SKILL", proficiency=proficiency, yearsExperience=years)

    def set_student_domain_interest(self, student_id: int, domain_id: int, priority: int = 1):
        s_node = f"Student:{student_id}"
        d_node = f"Domain:{domain_id}"
        if self.g.has_node(s_node) and self.g.has_node(d_node):
            self.g.add_edge(s_node, d_node, type="INTERESTED_IN", priorityOrder=priority)

    def set_mentor_domain_expertise(self, mentor_id: int, domain_id: int, level: str = "EXPERT", is_primary: bool = False):
        m_node = f"Mentor:{mentor_id}"
        d_node = f"Domain:{domain_id}"
        if self.g.has_node(m_node) and self.g.has_node(d_node):
            self.g.add_edge(m_node, d_node, type="SPECIALIZES_IN", expertiseLevel=level, isPrimary=is_primary)

    def record_mentored_by(self, student_id: int, mentor_id: int, allocation_id: int):
        s_node = f"Student:{student_id}"
        m_node = f"Mentor:{mentor_id}"
        if self.g.has_node(s_node) and self.g.has_node(m_node):
            self.g.add_edge(s_node, m_node, type="MENTORED_BY", allocationId=allocation_id)

    # --- Core Cypher Traversal Equivalents (Neo4j Graph Design §10) ---

    def find_shared_skill_candidates(self, student_id: int) -> List[Dict[str, Any]]:
        """Finds mentors who share one or more skills with the student:
        MATCH (s:Student {studentId: $id})-[:HAS_SKILL]->(k:Skill)<-[:HAS_SKILL]-(m:Mentor)
        """
        s_node = f"Student:{student_id}"
        if not self.g.has_node(s_node):
            return []

        student_skills = set()
        for _, target, data in self.g.out_edges(s_node, data=True):
            if data.get("type") == "HAS_SKILL":
                student_skills.add(target)

        candidates: Dict[int, Dict[str, Any]] = {}
        for m_node in [n for n, d in self.g.nodes(data=True) if d.get("label") == "Mentor"]:
            matched_skills = []
            for _, target, data in self.g.out_edges(m_node, data=True):
                if data.get("type") == "HAS_SKILL" and target in student_skills:
                    skill_name = self.g.nodes[target].get("name", "")
                    matched_skills.append({
                        "skill_id": self.g.nodes[target].get("skillId"),
                        "skill_name": skill_name,
                        "mentor_proficiency": data.get("proficiency", "INTERMEDIATE"),
                        "mentor_years": data.get("yearsExperience", 0.0)
                    })
            if matched_skills:
                m_data = self.g.nodes[m_node]
                candidates[m_data["mentorId"]] = {
                    "mentor_id": m_data["mentorId"],
                    "shared_skills": matched_skills,
                    "shared_skill_count": len(matched_skills)
                }
        return list(candidates.values())

    def find_domain_aligned_candidates(self, student_id: int) -> List[Dict[str, Any]]:
        """Finds mentors specialized in domains the student is interested in:
        MATCH (s:Student)-[:INTERESTED_IN]->(d:Domain)<-[:SPECIALIZES_IN]-(m:Mentor)
        """
        s_node = f"Student:{student_id}"
        if not self.g.has_node(s_node):
            return []

        student_domains = {}
        for _, target, data in self.g.out_edges(s_node, data=True):
            if data.get("type") == "INTERESTED_IN":
                student_domains[target] = data.get("priorityOrder", 1)

        candidates: Dict[int, Dict[str, Any]] = {}
        for m_node in [n for n, d in self.g.nodes(data=True) if d.get("label") == "Mentor"]:
            matched_domains = []
            for _, target, data in self.g.out_edges(m_node, data=True):
                if data.get("type") == "SPECIALIZES_IN" and target in student_domains:
                    d_data = self.g.nodes[target]
                    matched_domains.append({
                        "domain_id": d_data.get("domainId"),
                        "domain_name": d_data.get("name"),
                        "expertise_level": data.get("expertiseLevel", "ADVANCED"),
                        "student_priority": student_domains[target],
                        "is_primary": data.get("isPrimary", False)
                    })
            if matched_domains:
                m_data = self.g.nodes[m_node]
                candidates[m_data["mentorId"]] = {
                    "mentor_id": m_data["mentorId"],
                    "matched_domains": matched_domains,
                    "matched_domain_count": len(matched_domains)
                }
        return list(candidates.values())

    def find_alumni_from_same_department(self, student_id: int) -> List[int]:
        """MATCH (s:Student)-[:BELONGS_TO]->(d:Department)<-[:BELONGS_TO]-(m:Mentor)"""
        s_node = f"Student:{student_id}"
        if not self.g.has_node(s_node):
            return []

        s_depts = [t for _, t, d in self.g.out_edges(s_node, data=True) if d.get("type") == "BELONGS_TO"]
        if not s_depts:
            return []

        dept = s_depts[0]
        mentors = []
        for m_node, _, d in self.g.in_edges(dept, data=True):
            if d.get("type") == "BELONGS_TO" and self.g.nodes[m_node].get("label") == "Mentor":
                mentors.append(self.g.nodes[m_node]["mentorId"])
        return mentors


class GraphManager:
    """Manages Neo4j driver connection with transparent fallback to in-memory graph."""
    def __init__(self):
        self._driver = None
        self._is_live = False
        self.engine = InMemoryGraphEngine()
        self._init_connection()

    def _init_connection(self):
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                connection_timeout=1.0
            )
            driver.verify_connectivity()
            self._driver = driver
            self._is_live = True
            logger.info("Connected successfully to Neo4j database.")
        except Exception as e:
            logger.warning(f"Neo4j unavailable ({e}). Using resilient in-memory graph engine.")
            self._driver = None
            self._is_live = False

    @property
    def is_live(self) -> bool:
        return self._is_live and self._driver is not None

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if self.is_live:
            try:
                with self._driver.session() as session:
                    result = session.run(query, parameters or {})
                    return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Neo4j query execution failed ({e}).")
        return []


graph_client = GraphManager()

