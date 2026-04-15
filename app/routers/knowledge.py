"""
知识模块 - API 路由
Knowledge module - API router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["知识管理"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: str | None
    category: str | None

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    title: str
    content: str
    source: str | None = None
    tags: str | None = None


class DocumentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    source: str | None = None
    tags: str | None = None


class DocumentOut(BaseModel):
    id: int
    knowledge_base_id: int
    title: str
    content: str
    source: str | None
    tags: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# KnowledgeBase endpoints
# ---------------------------------------------------------------------------


@router.get("/bases", response_model=list[KnowledgeBaseOut])
def list_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return knowledge_service.list_knowledge_bases(db, skip=skip, limit=limit)


@router.post("/bases", response_model=KnowledgeBaseOut, status_code=201)
def create_base(body: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    return knowledge_service.create_knowledge_base(
        db, name=body.name, description=body.description, category=body.category
    )


@router.get("/bases/{kb_id}", response_model=KnowledgeBaseOut)
def get_base(kb_id: int, db: Session = Depends(get_db)):
    kb = knowledge_service.get_knowledge_base(db, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.put("/bases/{kb_id}", response_model=KnowledgeBaseOut)
def update_base(kb_id: int, body: KnowledgeBaseUpdate, db: Session = Depends(get_db)):
    kb = knowledge_service.update_knowledge_base(
        db, kb_id, name=body.name, description=body.description, category=body.category
    )
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete("/bases/{kb_id}", status_code=204)
def delete_base(kb_id: int, db: Session = Depends(get_db)):
    ok = knowledge_service.delete_knowledge_base(db, kb_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


# ---------------------------------------------------------------------------
# Document endpoints
# ---------------------------------------------------------------------------


@router.get("/bases/{kb_id}/documents", response_model=list[DocumentOut])
def list_documents(
    kb_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if not knowledge_service.get_knowledge_base(db, kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return knowledge_service.list_documents(db, kb_id, skip=skip, limit=limit)


@router.post("/bases/{kb_id}/documents", response_model=DocumentOut, status_code=201)
def create_document(kb_id: int, body: DocumentCreate, db: Session = Depends(get_db)):
    kb = knowledge_service.get_knowledge_base(db, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return knowledge_service.create_document(
        db,
        kb_id=kb_id,
        title=body.title,
        content=body.content,
        source=body.source,
        tags=body.tags,
    )


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = knowledge_service.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.put("/documents/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: int, body: DocumentUpdate, db: Session = Depends(get_db)):
    doc = knowledge_service.update_document(
        db, doc_id, title=body.title, content=body.content, source=body.source, tags=body.tags
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    ok = knowledge_service.delete_document(db, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/search", response_model=list[DocumentOut])
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return knowledge_service.search_documents(db, keyword=q, limit=limit)
