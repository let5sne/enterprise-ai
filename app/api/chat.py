import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.orchestration.service import OrchestrationService
from app.schemas.chat import ChatAskRequest, ChatAskResponse, ResponseDebugInfo, TaskContextSnapshot

router = APIRouter()
logger = logging.getLogger(__name__)


def get_orchestration_service() -> OrchestrationService:
    return OrchestrationService()


@router.post("/chat/ask", response_model=ChatAskResponse)
async def chat_ask(
    request: ChatAskRequest,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
) -> ChatAskResponse:
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    try:
        execution_result = orchestration_service.run(request.message, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected orchestration error")
        raise HTTPException(status_code=500, detail="internal server error") from exc

    citations = execution_result.aggregated_citations
    artifacts = execution_result.aggregated_artifacts
    raw_sql = execution_result.aggregated_raw_sql

    task_context = TaskContextSnapshot(
        task_type=execution_result.intent,
        status="completed",
        summary=execution_result.summary_text,
        important_outputs={
            "latest_output_type": _infer_output_type(execution_result.intent),
            "followup_ready": True,
        },
    )

    debug = ResponseDebugInfo(
        intent=execution_result.intent,
        plan_steps=[step.capability_code for step in execution_result.step_results],
        raw_sql=raw_sql,
    )

    return ChatAskResponse(
        session_id=session_id,
        answer=execution_result.summary_text,
        capabilities_used=[step.capability_code for step in execution_result.step_results],
        citations=citations,
        artifacts=artifacts,
        task_context=task_context,
        trace_id=f"trace_{uuid.uuid4().hex[:12]}",
        debug=debug,
    )


def _infer_output_type(intent: str) -> str:
    if "knowledge" in intent:
        return "knowledge"
    if "data" in intent:
        return "data"
    if "content" in intent:
        return "content"
    return "mixed"
