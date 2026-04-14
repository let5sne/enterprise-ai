import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.orchestration.service import OrchestrationService
from app.schemas.chat import ChatAskRequest, ChatAskResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def get_orchestration_service() -> OrchestrationService:
    return OrchestrationService()


@router.post("/chat/ask", response_model=ChatAskResponse)
async def chat_ask(
    request: ChatAskRequest,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
) -> ChatAskResponse:
    # Generate or use provided session_id
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    try:
        execution_result = orchestration_service.run(request.message, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected orchestration error")
        raise HTTPException(status_code=500, detail="internal server error") from exc

    return ChatAskResponse(
        session_id=session_id,
        answer=execution_result.summary_text,
        capabilities_used=[step.capability_code for step in execution_result.step_results],
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        structured_result=execution_result.merged_structured_result,
    )
