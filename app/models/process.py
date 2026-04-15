"""
流程模块 - ORM 模型
Process module - ORM models
"""
import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class Workflow(Base):
    """工作流定义"""

    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    instances: Mapped[list["WorkflowInstance"]] = relationship(
        "WorkflowInstance", back_populates="workflow", cascade="all, delete-orphan"
    )


class WorkflowInstance(Base):
    """工作流实例"""

    __tablename__ = "workflow_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workflows.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="running")
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="instances")
    tasks: Mapped[list["WorkflowTask"]] = relationship(
        "WorkflowTask", back_populates="instance", cascade="all, delete-orphan"
    )


class WorkflowTask(Base):
    """工作流任务"""

    __tablename__ = "workflow_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    instance_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workflow_instances.id"), nullable=False
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance", back_populates="tasks"
    )
