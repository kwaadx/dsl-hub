from typing import Optional, Dict, Any
from sqlalchemy import func, literal_column
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json, hashlib

from ..database import SessionLocal
from ..models import Pipeline
from ..config import settings

class SimilarityService:
    def __init__(self, threshold: float | None = None):
        self.threshold = float(threshold) if threshold is not None else float(settings.SIMILARITY_THRESHOLD)

    @staticmethod
    def _canonical_hash(data: Any) -> bytes | None:
        try:
            if isinstance(data, (dict, list)):
                canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                return hashlib.sha256(canonical).digest()
        except (TypeError, ValueError, UnicodeError):
            return None
        return None

    def find_candidate(self, flow_id: str, user_message) -> Optional[Dict[str, Any]]:
        """
        Strategy:
        1) If user_message contains a JSON pipeline candidate under keys ['content', 'pipeline'],
           compute SHA-256 canonical hash and look for exact match in this flow via pipeline.content_hash.
        2) Otherwise, or if not found, use pg_trgm similarity on generated column pipeline.content_text.
        Returns a suggestion dict when score >= threshold or when exact match is found (score=1.0).
        Gracefully returns None if pg_trgm is unavailable or no hit passes the threshold.
        """
        db: Session = SessionLocal()
        try:
            # 1) Exact match by content_hash (if a JSON object is present)
            candidate_json = None
            if isinstance(user_message, dict):
                if isinstance(user_message.get("content"), (dict, list)):
                    candidate_json = user_message.get("content")
                elif isinstance(user_message.get("pipeline"), (dict, list)):
                    candidate_json = user_message.get("pipeline")
            if candidate_json is not None:
                h = self._canonical_hash(candidate_json)
                if h is not None:
                    p = (
                        db.query(Pipeline)
                        .filter(Pipeline.flow_id == flow_id, Pipeline.content_hash == h)
                        .first()
                    )
                    if p:
                        return dict(pipeline_id=str(p.id), version=p.version, score=1.0)

            # 2) TRGM similarity on generated content_text column
            query_text = str(user_message)
            if not query_text:
                return None
            if len(query_text) > 4000:
                query_text = query_text[:4000]

            # Use literal_column to reference generated column 'pipeline.content_text'
            content_text_col = literal_column("pipeline.content_text")
            score = func.similarity(content_text_col, query_text)
            q = (
                db.query(Pipeline, score.label("score"))
                .filter(Pipeline.flow_id == flow_id)
                .order_by(score.desc())
                .limit(5)
            )
            best: Optional[tuple[Pipeline, float]] = None
            for p, s in q:
                try:
                    s_val = float(s) if s is not None else 0.0
                except (TypeError, ValueError):
                    s_val = 0.0
                if best is None or s_val > best[1]:
                    best = (p, s_val)
            if best and best[1] >= self.threshold:
                p, s_val = best
                return dict(pipeline_id=str(p.id), version=p.version, score=round(s_val, 4))
            return None
        except SQLAlchemyError:
            # pg_trgm or similarity() may not be available — fallback to no suggestion
            return None
        finally:
            db.close()
