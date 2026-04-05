import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from nodes.conversation import ConversationContext
from nodes.conversation_studio import ConversationStudioGraph
from nodes.reply.base import ReplyAdapterError
from pydantic import BaseModel
from services.official_sim_client import OfficialSimClient, OfficialSimClientError

router = APIRouter(prefix="/conversation-studio", tags=["conversation-studio"])
logger = logging.getLogger(__name__)

_studio_instances: Dict[str, ConversationStudioGraph] = {}
_contexts: Dict[str, ConversationContext] = {}


class CreateRunRequest(BaseModel):
    platform: str
    user_id: Optional[str] = None
    order_id: Optional[str] = None
    conversation_id: Optional[str] = None
    scenario_name: str = "default"
    emotion: str = "calm"
    max_turns: int = 5
    use_official_sim: bool = True
    allow_stub_fallback: bool = False


class CreateRunResponse(BaseModel):
    run_id: str
    official_run_id: Optional[str] = None
    conversation_id: str
    platform: str
    status: str


class NextTurnRequest(BaseModel):
    override_intent: Optional[str] = None
    override_emotion: Optional[str] = None


class NextTurnResponse(BaseModel):
    run_id: str
    official_run_id: Optional[str] = None
    user_id: Optional[str] = None
    order_id: Optional[str] = None
    turn_no: int
    user_message: str
    reply_message: str
    reply_source: str
    intent: str
    emotion: str
    tool_calls: List[Dict[str, Any]]
    continue_suggested: bool
    escalation_to_human: bool = False
    escalation_reason: Optional[str] = None
    error_injected: bool = False
    error_response: Optional[Dict[str, Any]] = None
    official_current_step: Optional[int] = None


class RunSummaryResponse(BaseModel):
    run_id: str
    official_run_id: Optional[str] = None
    official_run_code: Optional[str] = None
    official_current_step: Optional[int] = None
    platform: str
    user_id: str
    order_id: str
    conversation_id: str
    current_turn: int
    max_turns: int
    status: str
    end_reason: Optional[str]
    total_messages: int
    created_at: str
    updated_at: str


class DebugResponse(BaseModel):
    run_id: str
    official_run_id: Optional[str] = None
    current_facts: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    reply_adapter_mode: str


class ReportResponse(BaseModel):
    run_id: str
    official_run_id: Optional[str] = None
    platform: str
    scenario_name: str
    status: str
    end_reason: Optional[str]
    summary: Dict[str, Any]
    escalation: Dict[str, Any]
    errors: Dict[str, Any]
    artifacts_count: int
    open_issues: List[str]
    injected_errors: List[Dict[str, Any]]
    observed_errors: List[Dict[str, Any]]
    official_sim_report: Optional[Dict[str, Any]] = None


def _build_official_client() -> OfficialSimClient:
    return OfficialSimClient()


@router.post("/runs", response_model=CreateRunResponse)
async def create_run(request: CreateRunRequest):
    studio = ConversationStudioGraph(
        use_official_sim=request.use_official_sim,
        allow_stub_fallback=request.allow_stub_fallback,
        platform=request.platform,
    )

    context = studio.create_run(
        platform=request.platform,
        user_id=request.user_id,
        order_id=request.order_id,
        conversation_id=request.conversation_id,
        scenario_name=request.scenario_name,
        emotion=request.emotion,
        max_turns=request.max_turns,
    )

    if request.use_official_sim:
        client = _build_official_client()
        try:
            official_run = client.create_run(
                platform=request.platform,
                scenario_name=request.scenario_name,
                metadata={
                    "user_sim_run_id": context.run_id,
                    "conversation_id": context.conversation_id,
                    "order_id": context.order_id,
                    "user_id": context.user_id,
                },
            )
        except OfficialSimClientError as exc:
            raise HTTPException(status_code=502, detail=str(exc))

        context.official_run_id = official_run.get("run_id")
        context.official_run_code = official_run.get("run_code")

        logger.info(
            "bound user-sim run to official-sim run user_sim_run_id=%s official_run_id=%s platform=%s scenario_name=%s",
            context.run_id,
            context.official_run_id,
            context.platform,
            context.scenario_name,
        )

    _contexts[context.run_id] = context
    _studio_instances[context.run_id] = studio

    return CreateRunResponse(
        run_id=context.run_id,
        official_run_id=context.official_run_id,
        conversation_id=context.conversation_id,
        platform=context.platform,
        status="created",
    )


@router.post("/runs/{run_id}/next", response_model=NextTurnResponse)
async def next_turn(run_id: str, request: NextTurnRequest = None):
    if run_id not in _contexts:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    context = _contexts[run_id]
    studio = _studio_instances.get(run_id)

    if not studio:
        raise HTTPException(status_code=500, detail=f"Studio for run {run_id} not found")

    override_intent = request.override_intent if request else None
    override_emotion = request.override_emotion if request else None

    try:
        turn_output = studio.next_turn(
            context,
            override_intent=override_intent,
            override_emotion=override_emotion,
        )
    except ReplyAdapterError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if context.official_run_id:
        client = _build_official_client()
        try:
            client.write_artifact(
                run_id=context.official_run_id,
                artifact_kind="user_message_payload",
                turn_no=turn_output.turn_no,
                payload={
                    "run_id": run_id,
                    "official_run_id": context.official_run_id,
                    "turn_no": turn_output.turn_no,
                    "platform": context.platform,
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "order_id": context.order_id,
                    "user_message": turn_output.user_message,
                    "intent": turn_output.intent,
                    "emotion": turn_output.emotion,
                },
            )
            client.write_artifact(
                run_id=context.official_run_id,
                artifact_kind="conversation_turn_payload",
                turn_no=turn_output.turn_no,
                payload={
                    "run_id": run_id,
                    "official_run_id": context.official_run_id,
                    "turn_no": turn_output.turn_no,
                    "platform": context.platform,
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "order_id": context.order_id,
                    "user_message": turn_output.user_message,
                    "reply_message": turn_output.reply_message,
                    "reply_source": turn_output.reply_source,
                    "tool_calls": turn_output.tool_calls,
                    "conversation_status": "closed" if not turn_output.continue_suggested else "running",
                    "escalation_to_human": turn_output.escalation_to_human,
                    "escalation_reason": turn_output.escalation_reason,
                },
            )
            client.write_artifact(
                run_id=context.official_run_id,
                artifact_kind="reply_recommendation_payload",
                turn_no=turn_output.turn_no,
                payload={
                    "run_id": run_id,
                    "official_run_id": context.official_run_id,
                    "turn_no": turn_output.turn_no,
                    "platform": context.platform,
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "order_id": context.order_id,
                    "recommended_reply": turn_output.reply_message,
                    "reply_source": turn_output.reply_source,
                },
            )
            advance_result = client.advance_run(
                run_id=context.official_run_id,
                event_type="conversation_turn",
            )
            context.official_current_step = int(
                advance_result.get("current_step", context.official_current_step)
            )
        except OfficialSimClientError as exc:
            raise HTTPException(status_code=502, detail=str(exc))

    return NextTurnResponse(
        run_id=run_id,
        official_run_id=context.official_run_id,
        user_id=context.user_id,
        order_id=context.order_id,
        turn_no=turn_output.turn_no,
        user_message=turn_output.user_message,
        reply_message=turn_output.reply_message,
        reply_source=turn_output.reply_source,
        intent=turn_output.intent,
        emotion=turn_output.emotion,
        tool_calls=turn_output.tool_calls,
        continue_suggested=turn_output.continue_suggested,
        escalation_to_human=turn_output.escalation_to_human,
        escalation_reason=turn_output.escalation_reason,
        error_injected=turn_output.error_injected,
        error_response=turn_output.error_response,
        official_current_step=context.official_current_step or None,
    )


@router.get("/runs/{run_id}", response_model=RunSummaryResponse)
async def get_run(run_id: str):
    if run_id not in _contexts:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    context = _contexts[run_id]
    summary = context.to_summary()

    return RunSummaryResponse(**summary)


@router.get("/runs/{run_id}/debug", response_model=DebugResponse)
async def get_debug(run_id: str):
    if run_id not in _contexts:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    context = _contexts[run_id]
    studio = _studio_instances.get(run_id)

    reply_mode = "unknown"
    if studio:
        modes = studio.reply_adapter.get_available_modes()
        if modes.get("use_official_sim"):
            reply_mode = (
                "official-sim+stub-fallback"
                if modes.get("allow_stub_fallback")
                else "official-sim-strict"
            )
        else:
            reply_mode = "stub"

    return DebugResponse(
        run_id=run_id,
        official_run_id=context.official_run_id,
        current_facts=context.get_current_facts(),
        conversation_history=[
            {"role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in context.conversation_history
        ],
        tool_results=context.tool_results,
        reply_adapter_mode=reply_mode,
    )


@router.get("/runs/{run_id}/messages")
async def get_messages(run_id: str):
    if run_id not in _contexts:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    context = _contexts[run_id]

    return {
        "run_id": run_id,
        "official_run_id": context.official_run_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "intent": m.intent,
                "emotion": m.emotion,
                "timestamp": m.timestamp,
            }
            for m in context.conversation_history
        ],
        "total": len(context.conversation_history),
    }


@router.get("/runs/{run_id}/report", response_model=ReportResponse)
async def get_report(run_id: str):
    if run_id not in _contexts:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    context = _contexts[run_id]
    report = context.to_report()
    official_report: Optional[Dict[str, Any]] = None

    if context.official_run_id:
        client = _build_official_client()
        try:
            official_report = client.get_report(context.official_run_id)
        except OfficialSimClientError as exc:
            official_report = {"error": str(exc)}

    report["official_sim_report"] = official_report
    return ReportResponse(**report)
