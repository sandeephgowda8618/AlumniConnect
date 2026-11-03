"""AlumniConnect Recommendation Run & History Repository
Implements Recommendation Design §11 history persistence in MySQL.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.entities import RecommendationRun, RecommendedMentor, MentorProfile, UserAccount


class RecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_run(self, student_user_id: int, algorithm_version: str,
                 input_goal: Optional[str] = None, filter_snapshot: Optional[Dict[str, Any]] = None,
                 profile_version: Optional[str] = "v1") -> RecommendationRun:
        run = RecommendationRun(
            student_user_id=student_user_id,
            input_goal=input_goal,
            algorithm_version=algorithm_version,
            profile_version=profile_version,
            filter_snapshot=filter_snapshot,
            executed_at=datetime.utcnow()
        )
        self.db.add(run)
        self.db.flush()
        return run

    def save_candidates(self, run_id: int, candidates: List[Dict[str, Any]]) -> List[RecommendedMentor]:
        saved = []
        for cand in candidates:
            row = RecommendedMentor(
                run_id=run_id,
                mentor_user_id=cand["mentor_user_id"],
                rank_position=cand["rank_position"],
                score=cand["overall_score"],
                eligibility_status=cand.get("eligibility_status", "ELIGIBLE"),
                explanation_text=cand.get("explanation_text", ""),
                created_at=datetime.utcnow()
            )
            self.db.add(row)
            saved.append(row)
        self.db.flush()
        return saved

    def get_latest_student_run(self, student_user_id: int) -> Optional[RecommendationRun]:
        return (
            self.db.query(RecommendationRun)
            .options(
                joinedload(RecommendationRun.recommendations).joinedload(RecommendedMentor.mentor).joinedload(MentorProfile.user)
            )
            .filter(RecommendationRun.student_user_id == student_user_id)
            .order_by(RecommendationRun.executed_at.desc())
            .first()
        )

