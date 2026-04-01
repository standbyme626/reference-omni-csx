import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, '/home/kkk/Project/platform-sim/apps/ai-orchestrator')

from services.llm_config import LLMConfig
from services.llm_service import LLMService


def test_llm_config_get_api_keys():
    keys = LLMConfig.get_api_keys()
    assert len(keys) >= 1
    assert "sk-" in keys[0]


def test_llm_config_get_model_candidates():
    models = LLMConfig.get_model_candidates()
    assert len(models) >= 1
    assert "qwen" in models[0]


def test_llm_config_get_api_base():
    base = LLMConfig.get_api_base()
    assert "dashscope" in base or "openai" in base


@patch('services.llm_service.ChatOpenAI')
def test_llm_service_init(mock_chat_openai):
    mock_instance = MagicMock()
    mock_chat_openai.return_value = mock_instance

    service = LLMService()
    assert service.model_name is not None
    assert "qwen" in service.model_name


@patch('services.llm_service.ChatOpenAI')
def test_llm_service_chat(mock_chat_openai):
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = MagicMock(content="测试回复")
    mock_chat_openai.return_value = mock_instance

    service = LLMService()
    messages = [{"role": "user", "content": "你好"}]
    response = service.chat(messages, system_prompt="你是一个助手")

    assert response == "测试回复"
    assert mock_instance.invoke.called


@patch('services.llm_service.ChatOpenAI')
def test_llm_service_generate_suggestions(mock_chat_openai):
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = MagicMock(content="1. 建议1\n2. 建议2\n3. 建议3")
    mock_chat_openai.return_value = mock_instance

    service = LLMService()
    suggestions = service.generate_suggestions(
        order_status="shipped",
        platform="taobao",
        user_message="什么时候发货"
    )

    assert len(suggestions) == 3
    assert "建议1" in suggestions[0]


@patch('services.llm_service.ChatOpenAI')
def test_llm_service_classify_intent_refund(mock_chat_openai):
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = MagicMock(content="refund_request")
    mock_chat_openai.return_value = mock_instance

    service = LLMService()
    intent = service.classify_intent("我想申请退款")

    assert intent == "refund_request"


@patch('services.llm_service.ChatOpenAI')
def test_llm_service_classify_intent_shipment(mock_chat_openai):
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = MagicMock(content="shipment_inquiry")
    mock_chat_openai.return_value = mock_instance

    service = LLMService()
    intent = service.classify_intent("查询物流")

    assert intent == "shipment_inquiry"


@patch('services.llm_service.ChatOpenAI')
def test_llm_service_classify_intent_fallback(mock_chat_openai):
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = MagicMock(content="unknown response")
    mock_chat_openai.return_value = mock_instance

    service = LLMService()
    intent = service.classify_intent("随便问问")

    assert intent == "general_inquiry"
