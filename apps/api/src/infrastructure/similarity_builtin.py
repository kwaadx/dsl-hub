from __future__ import annotations

import math
from typing import Dict
from collections import Counter

def _tf(text: str) -> Dict[str, float]:
    toks = [t.lower() for t in text.split() if t.strip()]
    c = Counter(toks)
    total = sum(c.values()) or 1
    return {k: v/total for k, v in c.items()}

class BuiltinSimilarity:
    def score(self, a: str, b: str) -> float:
        A, B = _tf(a), _tf(b)
        keys = set(A) | set(B)
        num = sum(A.get(k,0)*B.get(k,0) for k in keys)
        den = math.sqrt(sum(v*v for v in A.values())) * math.sqrt(sum(v*v for v in B.values()))
        return float(num/den) if den else 0.0