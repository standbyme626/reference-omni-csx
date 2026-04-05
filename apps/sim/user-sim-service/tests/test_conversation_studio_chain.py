import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

USER_SIM_ROOT = Path(__file__).resolve().parents[1]
if str(USER_SIM_ROOT) not in sys.path:
    sys.path.append(str(USER_SIM_ROOT))

from api.routes import conversation_studio as route_module
from nodes.conversation.context import ConversationContext
from nodes.conversation.context import EmotionType as ConversationEmotionType
from nodes.conversation_studio import ConversationStudioGraph, TurnOutput
from nodes.reply.base import ReplyAdapterError
from nodes.user_simulator import (
    EmotionType as SimulatorEmotionType,
)
from nodes.user_simulator import (
    IntentType as SimulatorIntentType,
)
from nodes.user_simulator import (
    ToolCall,
    UserMessageDecision,
    UserSimulator,
    UserSimulatorOutput,
)
from run_server import app


@pytest.fixture(autouse=True)
def clear_in_memory_state():
    route_module._contexts.clear()
    route_module._studio_instances.clear()
    yield
    route_module._contexts.clear()
    route_module._studio_instances.clear()


def test_create_run_binds_official_run_and_next_turn_syncs_artifacts(monkeypatch):
    recorded = {
        "create_calls": 0,
        "artifact_kinds": [],
        "advanced": 0,
    }

    class FakeOfficialSimClient:
        def create_run(self, platform, scenario_name, metadata=None, strict_mode=True, push_enabled=True):
            recorded["create_calls"] += 1
            return {
                "run_id": "00000000-0000-0000-0000-000000000123",
                "run_code": "run_test123",
                "platform": platform,
                "scenario_name": scenario_name,
            }

        def write_artifact(self, run_id, artifact_kind, payload, turn_no=None, step_no=None):
            recorded["artifact_kinds"].append(artifact_kind)
            return {"artifact_id": f"art_{artifact_kind}"}

        def advance_run(self, run_id, event_type="conversation_turn"):
            recorded["advanced"] += 1
            return {
                "run_id": run_id,
                "current_step": recorded["advanced"],
                "status": "running",
            }

        def get_report(self, run_id):
            return {"run_id": run_id, "status": "running", "total_steps": recorded["advanced"]}

    def fake_next_turn(self, context, override_intent=None, override_emotion=None):
        context.current_turn += 1
        return TurnOutput(
            turn_no=context.current_turn,
            user_message="用户消息",
            reply_message="建议回复",
            reply_source="domain-service",
            intent="ask_order_status",
            emotion="calm",
            tool_calls=[],
            continue_suggested=True,
            escalation_to_human=False,
            escalation_reason=None,
            error_injected=False,
            error_response=None,
        )

    monkeypatch.setattr(route_module, "_build_official_client", lambda: FakeOfficialSimClient())
    monkeypatch.setattr(ConversationStudioGraph, "next_turn", fake_next_turn)

    client = TestClient(app)

    create_resp = client.post(
        "/conversation-studio/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
            "max_turns": 3,
            "use_official_sim": True,
        },
    )
    assert create_resp.status_code == 200
    create_data = create_resp.json()
    assert create_data["official_run_id"] == "00000000-0000-0000-0000-000000000123"
    assert recorded["create_calls"] == 1

    run_id = create_data["run_id"]
    next_resp = client.post(f"/conversation-studio/runs/{run_id}/next", json={})
    assert next_resp.status_code == 200
    next_data = next_resp.json()
    assert next_data["official_run_id"] == "00000000-0000-0000-0000-000000000123"
    assert next_data["official_current_step"] == 1

    assert recorded["advanced"] == 1
    assert set(recorded["artifact_kinds"]) == {
        "user_message_payload",
        "conversation_turn_payload",
        "reply_recommendation_payload",
    }

    debug_resp = client.get(f"/conversation-studio/runs/{run_id}/debug")
    assert debug_resp.status_code == 200
    debug_data = debug_resp.json()
    assert debug_data["reply_adapter_mode"] == "official-sim-strict"

    report_resp = client.get(f"/conversation-studio/runs/{run_id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["official_run_id"] == "00000000-0000-0000-0000-000000000123"
    assert isinstance(report_data.get("official_sim_report"), dict)


def test_user_simulator_generate_respects_bound_order_id(monkeypatch):
    class FakeLLMService:
        def __init__(self, model_name=None):
            self.model_name = model_name

        def chat_with_tools(self, messages, system_prompt, tools):
            raise RuntimeError("skip llm")

    monkeypatch.setattr("nodes.user_simulator.LLMService", FakeLLMService)
    monkeypatch.setattr("nodes.user_simulator.random.choice", lambda seq: seq[0])

    simulator = UserSimulator()
    monkeypatch.setattr(
        simulator,
        "list_user_orders",
        lambda user_id, platform: [
            {"order_id": "JD_ORDER_001"},
            {"order_id": "JD_ORDER_003"},
        ],
    )
    monkeypatch.setattr(
        simulator,
        "get_order_summary",
        lambda order_id, platform: {"order_id": order_id, "status": "wait_pay"},
    )
    monkeypatch.setattr(simulator, "get_shipment_summary", lambda order_id, platform: None)
    monkeypatch.setattr(simulator, "get_refund_summary", lambda order_id, platform: None)

    result = simulator.generate(
        platform="wecom_kf",
        user_id="wecom_user_001",
        order_id="JD_ORDER_003",
        override_intent="ask_order_status",
        override_emotion="calm",
    )

    assert result.decision.selected_order_id == "JD_ORDER_003"
    assert "JD_ORDER_003" in result.user_message


def test_user_loop_keeps_existing_order_binding(monkeypatch):
    graph = ConversationStudioGraph(platform="wecom_kf")
    context = ConversationContext(
        run_id="cs_run_test",
        platform="wecom_kf",
        user_id="wecom_user_001",
        order_id="JD_ORDER_003",
        conversation_id="conv_test_001",
        scenario_name="basic_session",
        max_turns=3,
        emotion=ConversationEmotionType.CALM,
    )

    monkeypatch.setattr(
        graph.user_simulator,
        "get_order_summary",
        lambda order_id, platform: {"order_id": order_id, "status": "wait_pay"},
    )
    monkeypatch.setattr(graph.user_simulator, "get_shipment_summary", lambda order_id, platform: None)
    monkeypatch.setattr(graph.user_simulator, "get_refund_summary", lambda order_id, platform: None)

    def fake_generate(
        platform,
        user_id=None,
        order_id=None,
        conversation_id=None,
        override_emotion=None,
        override_intent=None,
    ):
        assert order_id == "JD_ORDER_003"
        return UserSimulatorOutput(
            decision=UserMessageDecision(
                selected_user_id="wecom_user_001",
                selected_order_id="JD_ORDER_001",
                intent=SimulatorIntentType.ASK_ORDER_STATUS,
                emotion=SimulatorEmotionType.CALM,
                tool_calls_used=[
                    ToolCall(
                        name="get_order_summary",
                        arguments={"order_id": "JD_ORDER_001", "platform": platform},
                    )
                ],
                reason="test-order-drift",
            ),
            user_message="我的订单 JD_ORDER_001 怎么样了",
        )

    monkeypatch.setattr(graph.user_simulator, "generate", fake_generate)

    user_loop = graph._user_loop(context)

    assert user_loop["intent"] == "ask_order_status"
    assert context.order_id == "JD_ORDER_003"
    assert context.user_id == "wecom_user_001"


def test_next_turn_returns_502_when_strict_official_sim_reply_fails(monkeypatch):
    class FakeOfficialSimClient:
        def create_run(self, platform, scenario_name, metadata=None, strict_mode=True, push_enabled=True):
            return {
                "run_id": "00000000-0000-0000-0000-000000000456",
                "run_code": "run_test456",
                "platform": platform,
                "scenario_name": scenario_name,
            }

    def fail_next_turn(self, context, override_intent=None, override_emotion=None):
        raise ReplyAdapterError("official-sim reply unavailable")

    monkeypatch.setattr(route_module, "_build_official_client", lambda: FakeOfficialSimClient())
    monkeypatch.setattr(ConversationStudioGraph, "next_turn", fail_next_turn)

    client = TestClient(app)

    create_resp = client.post(
        "/conversation-studio/runs",
        json={
            "platform": "taobao",
            "scenario_name": "wait_ship_basic",
            "max_turns": 3,
            "use_official_sim": True,
        },
    )
    assert create_resp.status_code == 200
    run_id = create_resp.json()["run_id"]

    next_resp = client.post(f"/conversation-studio/runs/{run_id}/next", json={})
    assert next_resp.status_code == 502
    assert next_resp.json()["detail"] == "official-sim reply unavailable"
