"""AlumniConnect Cache Service
Implements Redis Design Specification §4 (Read Caches), §7 (TTL Policies),
and §9 (Targeted Cache Invalidation).
"""

import json
import hashlib
from typing import Optional, Dict, Any, List
from app.core.redis_client import redis_client
from app.core.config import settings


class CacheService:
    @staticmethod
    def get_public_mentor_profile(mentor_id: int) -> Optional[Dict[str, Any]]:
        key = redis_client.build_key("mentor", "profile", mentor_id, "public")
        cached = redis_client.get(key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                return None
        return None

    @staticmethod
    def set_public_mentor_profile(mentor_id: int, profile_data: Dict[str, Any], ttl: int = 600):
        key = redis_client.build_key("mentor", "profile", mentor_id, "public")
        redis_client.set(key, json.dumps(profile_data, default=str), ex=ttl)

    @staticmethod
    def invalidate_mentor_profile(mentor_id: int):
        pattern = redis_client.build_key("mentor", "profile", mentor_id, "*")
        redis_client.delete_by_pattern(pattern)

    @staticmethod
    def get_skills_catalog() -> Optional[List[Dict[str, Any]]]:
        key = redis_client.build_key("catalog", "skills", "all")
        cached = redis_client.get(key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                return None
        return None

    @staticmethod
    def set_skills_catalog(skills: List[Dict[str, Any]], ttl: int = 3600):
        key = redis_client.build_key("catalog", "skills", "all")
        redis_client.set(key, json.dumps(skills), ex=ttl)

    @staticmethod
    def get_domains_catalog() -> Optional[List[Dict[str, Any]]]:
        key = redis_client.build_key("catalog", "domains", "all")
        cached = redis_client.get(key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                return None
        return None

    @staticmethod
    def set_domains_catalog(domains: List[Dict[str, Any]], ttl: int = 3600):
        key = redis_client.build_key("catalog", "domains", "all")
        redis_client.set(key, json.dumps(domains), ex=ttl)

    @staticmethod
    def build_rec_cache_key(student_id: int, filters: Dict[str, Any]) -> str:
        digest = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:8]
        return redis_client.build_key("rec", f"student:{student_id}", f"filters:{digest}")

    @staticmethod
    def get_cached_recommendations(student_id: int, filters: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        key = CacheService.build_rec_cache_key(student_id, filters)
        cached = redis_client.get(key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                return None
        return None

    @staticmethod
    def set_cached_recommendations(student_id: int, filters: Dict[str, Any], results: List[Dict[str, Any]], ttl: int = 300):
        key = CacheService.build_rec_cache_key(student_id, filters)
        redis_client.set(key, json.dumps(results, default=str), ex=ttl)

    @staticmethod
    def invalidate_student_recommendations(student_id: int):
        pattern = redis_client.build_key("rec", f"student:{student_id}", "*")
        redis_client.delete_by_pattern(pattern)

