import pytest
from types import SimpleNamespace

from ..routers.upgrades import create_upgrade_plan, UpgradePlanCreate
from ..models import SchemaDef


class DummyDB:
    def get(self, model, id_):
        # Pretend both schema defs exist
        if model is SchemaDef:
            return SimpleNamespace(id=id_)
        return None

    # Following methods are not used for invalid strategy path
    def add(self, obj):
        pass

    def flush(self):
        pass


def test_upgrade_plan_invalid_strategy_400():
    db = DummyDB()
    body = UpgradePlanCreate(
        from_schema_def_id="a",
        to_schema_def_id="b",
        strategy="invalid_strategy",
        transform_spec=None,
    )
    with pytest.raises(Exception) as ex:
        create_upgrade_plan(body=body, db=db)  # type: ignore[arg-type]
    # FastAPI raises HTTPException; we only check that it's raised
    assert "Invalid strategy" in str(ex.value)
