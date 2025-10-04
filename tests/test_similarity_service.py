from types import SimpleNamespace

from apps.api.src.services.similarity_service import SimilarityService


class _FakePipeline:
    def __init__(self, id_: str, version: str):
        self.id = id_
        self.version = version


class _FakeQuery:
    def __init__(self, pipeline):
        self._pipeline = pipeline

    def filter(self, *args, **kwargs):  # signature compatibility
        return self

    def first(self):
        return self._pipeline


class _FakeDB:
    def __init__(self, pipeline):
        self._pipeline = pipeline

    def query(self, *args, **kwargs):  # signature compatibility
        return _FakeQuery(self._pipeline)

    def close(self):
        pass


class _FakeSessionLocal:
    def __init__(self, pipeline):
        self._pipeline = pipeline

    def __call__(self):
        return _FakeDB(self._pipeline)


def test_similarity_exact_match_monkeypatched(monkeypatch):
    # Arrange a pipeline that should be returned on exact hash path
    p = _FakePipeline(id_="pip-1", version="1.2.3")
    fake_session_factory = _FakeSessionLocal(p)
    # Monkeypatch the SessionLocal used inside SimilarityService
    monkeypatch.setattr(
        "apps.api.src.services.similarity_service.SessionLocal", fake_session_factory, raising=False
    )
    svc = SimilarityService(threshold=0.99)
    candidate_json = {"name": "x", "stages": []}
    # Act: user_message contains pipeline JSON -> should go through exact match branch and return score=1.0
    out = svc.find_candidate("flow-1", {"content": candidate_json})
    assert out is not None
    assert out["pipeline_id"] == "pip-1"
    assert out["version"] == "1.2.3"
    assert out["score"] == 1.0
