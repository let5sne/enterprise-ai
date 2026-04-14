"""
流程模块 - API 路由
Process module - API router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services import process_service

router = APIRouter(prefix="/process", tags=["流程管理"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    definition: str | None = None


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    definition: str | None = None
    status: str | None = None


class WorkflowOut(BaseModel):
    id: int
    name: str
    description: str | None
    definition: str | None
    status: str
    version: int

    model_config = {"from_attributes": True}


class InstanceCreate(BaseModel):
    input_data: str | None = None


class InstanceFinish(BaseModel):
    status: str
    output_data: str | None = None
    error_message: str | None = None


class InstanceOut(BaseModel):
    id: int
    workflow_id: int
    status: str
    input_data: str | None
    output_data: str | None
    error_message: str | None

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    task_name: str
    task_type: str
    sequence: int = 0
    input_data: str | None = None


class TaskStatusUpdate(BaseModel):
    status: str
    output_data: str | None = None
    error_message: str | None = None


class TaskOut(BaseModel):
    id: int
    instance_id: int
    task_name: str
    task_type: str
    status: str
    sequence: int
    input_data: str | None
    output_data: str | None
    error_message: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


@router.get("/workflows", response_model=list[WorkflowOut])
def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return process_service.list_workflows(db, skip=skip, limit=limit)


@router.post("/workflows", response_model=WorkflowOut, status_code=201)
def create_workflow(body: WorkflowCreate, db: Session = Depends(get_db)):
    return process_service.create_workflow(
        db, name=body.name, description=body.description, definition=body.definition
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowOut)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    wf = process_service.get_workflow(db, workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.put("/workflows/{workflow_id}", response_model=WorkflowOut)
def update_workflow(workflow_id: int, body: WorkflowUpdate, db: Session = Depends(get_db)):
    wf = process_service.update_workflow(
        db,
        workflow_id,
        name=body.name,
        description=body.description,
        definition=body.definition,
        status=body.status,
    )
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/workflows/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    ok = process_service.delete_workflow(db, workflow_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Workflow not found")


# ---------------------------------------------------------------------------
# WorkflowInstance endpoints
# ---------------------------------------------------------------------------


@router.get("/workflows/{workflow_id}/instances", response_model=list[InstanceOut])
def list_instances(
    workflow_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if not process_service.get_workflow(db, workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return process_service.list_instances(db, workflow_id, skip=skip, limit=limit)


@router.post("/workflows/{workflow_id}/instances", response_model=InstanceOut, status_code=201)
def create_instance(workflow_id: int, body: InstanceCreate, db: Session = Depends(get_db)):
    wf = process_service.get_workflow(db, workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return process_service.create_instance(db, workflow_id=workflow_id, input_data=body.input_data)


@router.get("/instances/{instance_id}", response_model=InstanceOut)
def get_instance(instance_id: int, db: Session = Depends(get_db)):
    instance = process_service.get_instance(db, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance


@router.put("/instances/{instance_id}/finish", response_model=InstanceOut)
def finish_instance(instance_id: int, body: InstanceFinish, db: Session = Depends(get_db)):
    instance = process_service.finish_instance(
        db,
        instance_id,
        status=body.status,
        output_data=body.output_data,
        error_message=body.error_message,
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance


# ---------------------------------------------------------------------------
# WorkflowTask endpoints
# ---------------------------------------------------------------------------


@router.get("/instances/{instance_id}/tasks", response_model=list[TaskOut])
def list_tasks(
    instance_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if not process_service.get_instance(db, instance_id):
        raise HTTPException(status_code=404, detail="Instance not found")
    return process_service.list_tasks(db, instance_id, skip=skip, limit=limit)


@router.post("/instances/{instance_id}/tasks", response_model=TaskOut, status_code=201)
def create_task(instance_id: int, body: TaskCreate, db: Session = Depends(get_db)):
    instance = process_service.get_instance(db, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    return process_service.create_task(
        db,
        instance_id=instance_id,
        task_name=body.task_name,
        task_type=body.task_type,
        sequence=body.sequence,
        input_data=body.input_data,
    )


@router.put("/tasks/{task_id}/status", response_model=TaskOut)
def update_task_status(task_id: int, body: TaskStatusUpdate, db: Session = Depends(get_db)):
    task = process_service.update_task_status(
        db,
        task_id,
        status=body.status,
        output_data=body.output_data,
        error_message=body.error_message,
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
