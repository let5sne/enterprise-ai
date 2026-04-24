from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.orchestration.service import OrchestrationService


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.orchestration_service = OrchestrationService()
    yield


app = FastAPI(title="Enterprise AI Backend", lifespan=lifespan)
app.include_router(chat_router, prefix="/api/v1")
