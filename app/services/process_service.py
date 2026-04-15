"""
流程模块 - 业务服务
Process module - Business service layer
"""
import datetime

from sqlalchemy.orm import Session

from app.models.process import Workflow, WorkflowInstance, WorkflowTask


# ---------------------------------------------------------------------------
# Workflow CRUD
# ---------------------------------------------------------------------------


def list_workflows(db: Session, skip: int = 0, limit: int = 20) -> list[Workflow]:
    return db.query(Workflow).offset(skip).limit(limit).all()


def get_workflow(db: Session, workflow_id: int) -> Workflow | None:
    return db.query(Workflow).filter(Workflow.id == workflow_id).first()


def create_workflow(
    db: Session,
    name: str,
    description: str | None = None,
    definition: str | None = None,
) -> Workflow:
    workflow = Workflow(name=name, description=description, definition=definition)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def update_workflow(
    db: Session,
    workflow_id: int,
    name: str | None = None,
    description: str | None = None,
    definition: str | None = None,
    status: str | None = None,
) -> Workflow | None:
    workflow = get_workflow(db, workflow_id)
    if workflow is None:
        return None
    if name is not None:
        workflow.name = name
    if description is not None:
        workflow.description = description
    if definition is not None:
        workflow.definition = definition
        workflow.version += 1
    if status is not None:
        workflow.status = status
    db.commit()
    db.refresh(workflow)
    return workflow


def delete_workflow(db: Session, workflow_id: int) -> bool:
    workflow = get_workflow(db, workflow_id)
    if workflow is None:
        return False
    db.delete(workflow)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# WorkflowInstance CRUD
# ---------------------------------------------------------------------------


def list_instances(
    db: Session, workflow_id: int, skip: int = 0, limit: int = 20
) -> list[WorkflowInstance]:
    return (
        db.query(WorkflowInstance)
        .filter(WorkflowInstance.workflow_id == workflow_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_instance(db: Session, instance_id: int) -> WorkflowInstance | None:
    return db.query(WorkflowInstance).filter(WorkflowInstance.id == instance_id).first()


def create_instance(
    db: Session, workflow_id: int, input_data: str | None = None
) -> WorkflowInstance:
    instance = WorkflowInstance(workflow_id=workflow_id, input_data=input_data)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def finish_instance(
    db: Session,
    instance_id: int,
    status: str,
    output_data: str | None = None,
    error_message: str | None = None,
) -> WorkflowInstance | None:
    instance = get_instance(db, instance_id)
    if instance is None:
        return None
    instance.status = status
    if output_data is not None:
        instance.output_data = output_data
    if error_message is not None:
        instance.error_message = error_message
    instance.finished_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(instance)
    return instance


# ---------------------------------------------------------------------------
# WorkflowTask CRUD
# ---------------------------------------------------------------------------


def list_tasks(
    db: Session, instance_id: int, skip: int = 0, limit: int = 50
) -> list[WorkflowTask]:
    return (
        db.query(WorkflowTask)
        .filter(WorkflowTask.instance_id == instance_id)
        .order_by(WorkflowTask.sequence)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_task(db: Session, task_id: int) -> WorkflowTask | None:
    return db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()


def create_task(
    db: Session,
    instance_id: int,
    task_name: str,
    task_type: str,
    sequence: int = 0,
    input_data: str | None = None,
) -> WorkflowTask:
    task = WorkflowTask(
        instance_id=instance_id,
        task_name=task_name,
        task_type=task_type,
        sequence=sequence,
        input_data=input_data,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(
    db: Session,
    task_id: int,
    status: str,
    output_data: str | None = None,
    error_message: str | None = None,
) -> WorkflowTask | None:
    task = get_task(db, task_id)
    if task is None:
        return None
    task.status = status
    if output_data is not None:
        task.output_data = output_data
    if error_message is not None:
        task.error_message = error_message
    if status == "running":
        task.started_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    if status in ("completed", "failed"):
        task.finished_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(task)
    return task
