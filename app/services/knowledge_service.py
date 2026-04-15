"""
知识模块 - 业务服务
Knowledge module - Business service layer
"""
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeBase, KnowledgeDocument


# ---------------------------------------------------------------------------
# KnowledgeBase CRUD
# ---------------------------------------------------------------------------


def list_knowledge_bases(db: Session, skip: int = 0, limit: int = 20) -> list[KnowledgeBase]:
    return db.query(KnowledgeBase).offset(skip).limit(limit).all()


def get_knowledge_base(db: Session, kb_id: int) -> KnowledgeBase | None:
    return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()


def create_knowledge_base(
    db: Session, name: str, description: str | None = None, category: str | None = None
) -> KnowledgeBase:
    kb = KnowledgeBase(name=name, description=description, category=category)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


def update_knowledge_base(
    db: Session,
    kb_id: int,
    name: str | None = None,
    description: str | None = None,
    category: str | None = None,
) -> KnowledgeBase | None:
    kb = get_knowledge_base(db, kb_id)
    if kb is None:
        return None
    if name is not None:
        kb.name = name
    if description is not None:
        kb.description = description
    if category is not None:
        kb.category = category
    db.commit()
    db.refresh(kb)
    return kb


def delete_knowledge_base(db: Session, kb_id: int) -> bool:
    kb = get_knowledge_base(db, kb_id)
    if kb is None:
        return False
    db.delete(kb)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# KnowledgeDocument CRUD
# ---------------------------------------------------------------------------


def list_documents(
    db: Session, kb_id: int, skip: int = 0, limit: int = 20
) -> list[KnowledgeDocument]:
    return (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.knowledge_base_id == kb_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_document(db: Session, doc_id: int) -> KnowledgeDocument | None:
    return db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()


def create_document(
    db: Session,
    kb_id: int,
    title: str,
    content: str,
    source: str | None = None,
    tags: str | None = None,
) -> KnowledgeDocument:
    doc = KnowledgeDocument(
        knowledge_base_id=kb_id,
        title=title,
        content=content,
        source=source,
        tags=tags,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document(
    db: Session,
    doc_id: int,
    title: str | None = None,
    content: str | None = None,
    source: str | None = None,
    tags: str | None = None,
) -> KnowledgeDocument | None:
    doc = get_document(db, doc_id)
    if doc is None:
        return None
    if title is not None:
        doc.title = title
    if content is not None:
        doc.content = content
    if source is not None:
        doc.source = source
    if tags is not None:
        doc.tags = tags
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, doc_id: int) -> bool:
    doc = get_document(db, doc_id)
    if doc is None:
        return False
    db.delete(doc)
    db.commit()
    return True


def search_documents(db: Session, keyword: str, limit: int = 20) -> list[KnowledgeDocument]:
    """Full-text keyword search across title and content."""
    pattern = f"%{keyword}%"
    return (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.title.ilike(pattern)
            | KnowledgeDocument.content.ilike(pattern)
        )
        .limit(limit)
        .all()
    )
