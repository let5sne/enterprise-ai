"""
企业AI能力后端 - 主入口
Enterprise AI Backend - Main entry point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.config import settings
from app.database.db import init_db
from app.orchestration.service import OrchestrationService
from app.routers import content, data, knowledge, process


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    application.state.orchestration_service = OrchestrationService()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="企业AI能力后端，涵盖知识、数据、内容、流程四大模块。",
    lifespan=lifespan,
)


app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(process.router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/", tags=["健康检查"])
def root():
    return {"name": settings.app_name, "version": settings.app_version, "status": "ok"}


@app.get("/health", tags=["健康检查"])
def health():
    return {"status": "ok"}
