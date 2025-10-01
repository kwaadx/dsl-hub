from fastapi import APIRouter, Depends, Path, Body, status, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..models.database import get_db
from ..controllers import schema_controller
from ..middleware.error import HTTPException

router = APIRouter()

class SchemaCreate(BaseModel):
    name: str
    version: str = Field(..., regex=r"^\d+\.\d+\.\d+$", description="semver X.Y.Z")
    json: Dict[str, Any]

class SchemaResponse(BaseModel):
    id: str
    name: str
    version: str
    json: Dict[str, Any]

    class Config:
        orm_mode = True

@router.get("/", response_model=List[SchemaResponse])
async def list_schemas(
    db: Session = Depends(get_db),
    name: Optional[str] = None,
    version: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    pageSize: int = 100,
):
    """
    List schemas with optional filters and pagination (returns page items only).
    """
    return schema_controller.list(db, name=name, version=version, status=status, page=page, page_size=pageSize)

@router.post("/", response_model=SchemaResponse, status_code=status.HTTP_201_CREATED)
async def create_schema(schema: SchemaCreate = Body(...), db: Session = Depends(get_db)):
    """
    Create a new schema.
    """
    return schema_controller.create(db, schema)

@router.get("/{id}", response_model=SchemaResponse)
async def get_schema(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Get a schema by ID.
    """
    schema = schema_controller.get(db, id)
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Schema not found")
    return schema

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schema(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Delete a schema by ID.
    """
    ok = schema_controller.remove(db, id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Schema not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
