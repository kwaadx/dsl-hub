from typing import Optional, Dict, Any
from sqlalchemy import func, cast, String
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Pipeline
from ..config import settings

class SimilarityService:
    def __init__(self, threshold: float | None = None):
        self.threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD

    def find_candidate(self, flow_id: str, user_message) -> Optional[Dict[str, Any]]:
        """
        Try Postgres pg_trgm similarity on pipeline.content::text vs the user_message text.
        Gracefully return None if extension/function is unavailable or no hit passes the threshold.
        """
        query_text = str(user_message)
        if not query_text:
            return None
        # Safety limit
        if len(query_text) > 4000:
            query_text = query_text[:4000]
        db: Session = SessionLocal()
        try:
            score = func.similarity(cast(Pipeline.content, String), query_text)
            q = db.query(Pipeline, score.label("score")).\
                filter(Pipeline.flow_id == flow_id).\
                order_by(score.desc()).limit(5)
            best: Optional[tuple[Pipeline, float]] = None
            for p, s in q:  # may raise if similarity function missing; handled below
                try:
                    s_val = float(s) if s is not None else 0.0
                except Exception:
                    s_val = 0.0
                if best is None or s_val > best[1]:
                    best = (p, s_val)
            if best and best[1] >= float(self.threshold):
                p, s_val = best
                return {"pipeline_id": str(p.id), "version": p.version, "score": round(s_val, 4)}
            return None
        except Exception:
            # pg_trgm or similarity() may not be available — fallback to no suggestion
            return None
        finally:
            db.close()
