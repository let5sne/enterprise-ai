"""
内容模块 - 业务服务
Content module - Business service layer
"""
from sqlalchemy.orm import Session

from app.models.content import Content, ContentTemplate


# ---------------------------------------------------------------------------
# ContentTemplate CRUD
# ---------------------------------------------------------------------------


def list_templates(db: Session, skip: int = 0, limit: int = 20) -> list[ContentTemplate]:
    return db.query(ContentTemplate).offset(skip).limit(limit).all()


def get_template(db: Session, template_id: int) -> ContentTemplate | None:
    return db.query(ContentTemplate).filter(ContentTemplate.id == template_id).first()


def create_template(
    db: Session,
    name: str,
    template_type: str,
    prompt_template: str,
    description: str | None = None,
    variables: str | None = None,
) -> ContentTemplate:
    template = ContentTemplate(
        name=name,
        template_type=template_type,
        prompt_template=prompt_template,
        description=description,
        variables=variables,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_template(
    db: Session,
    template_id: int,
    name: str | None = None,
    template_type: str | None = None,
    prompt_template: str | None = None,
    description: str | None = None,
    variables: str | None = None,
) -> ContentTemplate | None:
    template = get_template(db, template_id)
    if template is None:
        return None
    if name is not None:
        template.name = name
    if template_type is not None:
        template.template_type = template_type
    if prompt_template is not None:
        template.prompt_template = prompt_template
    if description is not None:
        template.description = description
    if variables is not None:
        template.variables = variables
    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, template_id: int) -> bool:
    template = get_template(db, template_id)
    if template is None:
        return False
    db.delete(template)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Content CRUD
# ---------------------------------------------------------------------------


def list_contents(db: Session, skip: int = 0, limit: int = 20) -> list[Content]:
    return db.query(Content).offset(skip).limit(limit).all()


def get_content(db: Session, content_id: int) -> Content | None:
    return db.query(Content).filter(Content.id == content_id).first()


def create_content(
    db: Session,
    title: str,
    body: str,
    content_type: str,
    template_id: int | None = None,
    status: str = "draft",
    author: str | None = None,
    tags: str | None = None,
) -> Content:
    content = Content(
        title=title,
        body=body,
        content_type=content_type,
        template_id=template_id,
        status=status,
        author=author,
        tags=tags,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


def update_content(
    db: Session,
    content_id: int,
    title: str | None = None,
    body: str | None = None,
    content_type: str | None = None,
    status: str | None = None,
    author: str | None = None,
    tags: str | None = None,
) -> Content | None:
    content = get_content(db, content_id)
    if content is None:
        return None
    if title is not None:
        content.title = title
    if body is not None:
        content.body = body
    if content_type is not None:
        content.content_type = content_type
    if status is not None:
        content.status = status
    if author is not None:
        content.author = author
    if tags is not None:
        content.tags = tags
    db.commit()
    db.refresh(content)
    return content


def delete_content(db: Session, content_id: int) -> bool:
    content = get_content(db, content_id)
    if content is None:
        return False
    db.delete(content)
    db.commit()
    return True


def publish_content(db: Session, content_id: int) -> Content | None:
    return update_content(db, content_id, status="published")
