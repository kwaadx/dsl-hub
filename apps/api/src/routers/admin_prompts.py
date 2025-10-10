from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from ..deps import prompt_repo

router = APIRouter(prefix="/admin/prompts", tags=["admin"])

class PromptUpsertIn(BaseModel):
    version: int = Field(ge=1)
    content: Dict[str, Any]
    is_active: bool = True

@router.get("/{key}")
def list_prompts(key: str, repo = Depends(prompt_repo)) -> List[Dict[str, Any]]:
    return list(repo.list(key))

@router.get("/{key}/active")
def get_active_prompt(key: str, repo = Depends(prompt_repo)) -> Dict[str, Any] | None:
    return repo.get_active(key)

@router.post("/{key}")
def upsert_prompt(key: str, body: PromptUpsertIn, repo = Depends(prompt_repo)) -> Dict[str, Any]:
    return repo.upsert(key, body.version, body.content, body.is_active)