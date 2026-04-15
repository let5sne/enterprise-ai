"""
数据模块 - API 路由
Data module - API router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services import data_service

router = APIRouter(prefix="/data", tags=["数据管理"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    connection_info: str | None = None
    description: str | None = None


class DataSourceUpdate(BaseModel):
    name: str | None = None
    source_type: str | None = None
    connection_info: str | None = None
    description: str | None = None
    status: str | None = None


class DataSourceOut(BaseModel):
    id: int
    name: str
    source_type: str
    connection_info: str | None
    description: str | None
    status: str

    model_config = {"from_attributes": True}


class DatasetCreate(BaseModel):
    name: str
    description: str | None = None
    schema_info: str | None = None


class DatasetOut(BaseModel):
    id: int
    data_source_id: int
    name: str
    description: str | None
    schema_info: str | None
    row_count: int
    status: str

    model_config = {"from_attributes": True}


class DataJobCreate(BaseModel):
    job_type: str


class DataJobStatusUpdate(BaseModel):
    status: str
    result: str | None = None
    error_message: str | None = None


class DataJobOut(BaseModel):
    id: int
    dataset_id: int
    job_type: str
    status: str
    result: str | None
    error_message: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# DataSource endpoints
# ---------------------------------------------------------------------------


@router.get("/sources", response_model=list[DataSourceOut])
def list_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return data_service.list_data_sources(db, skip=skip, limit=limit)


@router.post("/sources", response_model=DataSourceOut, status_code=201)
def create_source(body: DataSourceCreate, db: Session = Depends(get_db)):
    return data_service.create_data_source(
        db,
        name=body.name,
        source_type=body.source_type,
        connection_info=body.connection_info,
        description=body.description,
    )


@router.get("/sources/{source_id}", response_model=DataSourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = data_service.get_data_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source


@router.put("/sources/{source_id}", response_model=DataSourceOut)
def update_source(source_id: int, body: DataSourceUpdate, db: Session = Depends(get_db)):
    source = data_service.update_data_source(
        db,
        source_id,
        name=body.name,
        source_type=body.source_type,
        connection_info=body.connection_info,
        description=body.description,
        status=body.status,
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    ok = data_service.delete_data_source(db, source_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Data source not found")


# ---------------------------------------------------------------------------
# Dataset endpoints
# ---------------------------------------------------------------------------


@router.get("/sources/{source_id}/datasets", response_model=list[DatasetOut])
def list_datasets(
    source_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if not data_service.get_data_source(db, source_id):
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_service.list_datasets(db, source_id, skip=skip, limit=limit)


@router.post("/sources/{source_id}/datasets", response_model=DatasetOut, status_code=201)
def create_dataset(source_id: int, body: DatasetCreate, db: Session = Depends(get_db)):
    source = data_service.get_data_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_service.create_dataset(
        db,
        source_id=source_id,
        name=body.name,
        description=body.description,
        schema_info=body.schema_info,
    )


@router.get("/datasets/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = data_service.get_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/datasets/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ok = data_service.delete_dataset(db, dataset_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dataset not found")


# ---------------------------------------------------------------------------
# DataJob endpoints
# ---------------------------------------------------------------------------


@router.get("/datasets/{dataset_id}/jobs", response_model=list[DataJobOut])
def list_jobs(
    dataset_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if not data_service.get_dataset(db, dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found")
    return data_service.list_jobs(db, dataset_id, skip=skip, limit=limit)


@router.post("/datasets/{dataset_id}/jobs", response_model=DataJobOut, status_code=201)
def create_job(dataset_id: int, body: DataJobCreate, db: Session = Depends(get_db)):
    dataset = data_service.get_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return data_service.create_job(db, dataset_id=dataset_id, job_type=body.job_type)


@router.put("/jobs/{job_id}/status", response_model=DataJobOut)
def update_job_status(job_id: int, body: DataJobStatusUpdate, db: Session = Depends(get_db)):
    job = data_service.update_job_status(
        db, job_id, status=body.status, result=body.result, error_message=body.error_message
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
