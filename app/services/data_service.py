"""
数据模块 - 业务服务
Data module - Business service layer
"""
import datetime

from sqlalchemy.orm import Session

from app.models.data import DataJob, Dataset, DataSource


# ---------------------------------------------------------------------------
# DataSource CRUD
# ---------------------------------------------------------------------------


def list_data_sources(db: Session, skip: int = 0, limit: int = 20) -> list[DataSource]:
    return db.query(DataSource).offset(skip).limit(limit).all()


def get_data_source(db: Session, source_id: int) -> DataSource | None:
    return db.query(DataSource).filter(DataSource.id == source_id).first()


def create_data_source(
    db: Session,
    name: str,
    source_type: str,
    connection_info: str | None = None,
    description: str | None = None,
) -> DataSource:
    source = DataSource(
        name=name,
        source_type=source_type,
        connection_info=connection_info,
        description=description,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def update_data_source(
    db: Session,
    source_id: int,
    name: str | None = None,
    source_type: str | None = None,
    connection_info: str | None = None,
    description: str | None = None,
    status: str | None = None,
) -> DataSource | None:
    source = get_data_source(db, source_id)
    if source is None:
        return None
    if name is not None:
        source.name = name
    if source_type is not None:
        source.source_type = source_type
    if connection_info is not None:
        source.connection_info = connection_info
    if description is not None:
        source.description = description
    if status is not None:
        source.status = status
    db.commit()
    db.refresh(source)
    return source


def delete_data_source(db: Session, source_id: int) -> bool:
    source = get_data_source(db, source_id)
    if source is None:
        return False
    db.delete(source)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Dataset CRUD
# ---------------------------------------------------------------------------


def list_datasets(
    db: Session, source_id: int, skip: int = 0, limit: int = 20
) -> list[Dataset]:
    return (
        db.query(Dataset)
        .filter(Dataset.data_source_id == source_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_dataset(db: Session, dataset_id: int) -> Dataset | None:
    return db.query(Dataset).filter(Dataset.id == dataset_id).first()


def create_dataset(
    db: Session,
    source_id: int,
    name: str,
    description: str | None = None,
    schema_info: str | None = None,
) -> Dataset:
    dataset = Dataset(
        data_source_id=source_id,
        name=name,
        description=description,
        schema_info=schema_info,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def delete_dataset(db: Session, dataset_id: int) -> bool:
    dataset = get_dataset(db, dataset_id)
    if dataset is None:
        return False
    db.delete(dataset)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# DataJob CRUD
# ---------------------------------------------------------------------------


def list_jobs(db: Session, dataset_id: int, skip: int = 0, limit: int = 20) -> list[DataJob]:
    return (
        db.query(DataJob)
        .filter(DataJob.dataset_id == dataset_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_job(db: Session, job_id: int) -> DataJob | None:
    return db.query(DataJob).filter(DataJob.id == job_id).first()


def create_job(db: Session, dataset_id: int, job_type: str) -> DataJob:
    job = DataJob(dataset_id=dataset_id, job_type=job_type)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job_status(
    db: Session,
    job_id: int,
    status: str,
    result: str | None = None,
    error_message: str | None = None,
) -> DataJob | None:
    job = get_job(db, job_id)
    if job is None:
        return None
    job.status = status
    if result is not None:
        job.result = result
    if error_message is not None:
        job.error_message = error_message
    if status == "running":
        job.started_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    if status in ("completed", "failed"):
        job.finished_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(job)
    return job
