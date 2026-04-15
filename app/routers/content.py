"""
内容模块 - API 路由
Content module - API router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services import content_service

router = APIRouter(prefix="/content", tags=["内容管理"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class TemplateCreate(BaseModel):
    name: str
    template_type: str
    prompt_template: str
    description: str | None = None
    variables: str | None = None


class TemplateUpdate(BaseModel):
    name: str | None = None
    template_type: str | None = None
    prompt_template: str | None = None
    description: str | None = None
    variables: str | None = None


class TemplateOut(BaseModel):
    id: int
    name: str
    template_type: str
    prompt_template: str
    description: str | None
    variables: str | None

    model_config = {"from_attributes": True}


class ContentCreate(BaseModel):
    title: str
    body: str
    content_type: str
    template_id: int | None = None
    status: str = "draft"
    author: str | None = None
    tags: str | None = None


class ContentUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    content_type: str | None = None
    status: str | None = None
    author: str | None = None
    tags: str | None = None


class ContentOut(BaseModel):
    id: int
    title: str
    body: str
    content_type: str
    template_id: int | None
    status: str
    author: str | None
    tags: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Template endpoints
# ---------------------------------------------------------------------------


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return content_service.list_templates(db, skip=skip, limit=limit)


@router.post("/templates", response_model=TemplateOut, status_code=201)
def create_template(body: TemplateCreate, db: Session = Depends(get_db)):
    return content_service.create_template(
        db,
        name=body.name,
        template_type=body.template_type,
        prompt_template=body.prompt_template,
        description=body.description,
        variables=body.variables,
    )


@router.get("/templates/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = content_service.get_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=TemplateOut)
def update_template(template_id: int, body: TemplateUpdate, db: Session = Depends(get_db)):
    template = content_service.update_template(
        db,
        template_id,
        name=body.name,
        template_type=body.template_type,
        prompt_template=body.prompt_template,
        description=body.description,
        variables=body.variables,
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    ok = content_service.delete_template(db, template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")


# ---------------------------------------------------------------------------
# Content endpoints
# ---------------------------------------------------------------------------


@router.get("/items", response_model=list[ContentOut])
def list_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return content_service.list_contents(db, skip=skip, limit=limit)


@router.post("/items", response_model=ContentOut, status_code=201)
def create_content(body: ContentCreate, db: Session = Depends(get_db)):
    return content_service.create_content(
        db,
        title=body.title,
        body=body.body,
        content_type=body.content_type,
        template_id=body.template_id,
        status=body.status,
        author=body.author,
        tags=body.tags,
    )


@router.get("/items/{content_id}", response_model=ContentOut)
def get_content(content_id: int, db: Session = Depends(get_db)):
    content = content_service.get_content(db, content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.put("/items/{content_id}", response_model=ContentOut)
def update_content(content_id: int, body: ContentUpdate, db: Session = Depends(get_db)):
    content = content_service.update_content(
        db,
        content_id,
        title=body.title,
        body=body.body,
        content_type=body.content_type,
        status=body.status,
        author=body.author,
        tags=body.tags,
    )
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.delete("/items/{content_id}", status_code=204)
def delete_content(content_id: int, db: Session = Depends(get_db)):
    ok = content_service.delete_content(db, content_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Content not found")


@router.post("/items/{content_id}/publish", response_model=ContentOut)
def publish_content(content_id: int, db: Session = Depends(get_db)):
    content = content_service.publish_content(db, content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return content
