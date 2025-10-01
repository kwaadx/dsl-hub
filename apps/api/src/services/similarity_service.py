from typing import Optional, Dict, Any
# NOTE: Placeholder similarity using naive heuristic; replace with TRGM SQL or embeddings.

class SimilarityService:
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold

    def find_candidate(self, flow_id: str, user_message) -> Optional[Dict[str, Any]]:
        # TODO: query pipelines by TRGM and score
        return None
