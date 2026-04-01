from typing import Dict, Any, List, Optional
from .state import OrchestratorState, AgentStatus

try:
    from services.llm_service import LLMService
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    LLMService = None


ORDER_STATUS_SUGGESTIONS: Dict[str, Dict[str, List[str]]] = {
    "taobao": {
        "wait_pay": [
            "亲爱的买家，您的订单已创建，请尽快完成付款哦～",
            "您的订单等待付款中，付款后可立即发货",
        ],
        "wait_ship": [
            "您的订单已付款，商家正在准备发货中",
            "商家正在打包商品，预计24小时内发货",
        ],
        "shipped": [
            "您的包裹已发货，正在运送途中",
            "包裹已发出，预计3-5天送达",
        ],
        "finished": [
            "交易已完成，感谢您的购买！",
            "欢迎再次光临本店～",
        ],
    },
    "douyin_shop": {
        "paid": [
            "订单已付款，商家准备发货中",
            "您的商品正在打包准备发出",
        ],
        "shipped": [
            "包裹已发货，路上注意查收",
            "配送中，预计很快送达",
        ],
        "refunding": [
            "您的退款申请已收到，商家正在处理",
            "退款申请处理中，请耐心等待",
        ],
    },
    "wecom_kf": {
        "pending": [
            "欢迎来到客服中心，请稍候～",
            "正在为您接入客服，请稍等",
        ],
        "in_session": [
            "客服正在为您服务，请描述您的问题",
        ],
        "closed": [
            "会话已结束，感谢您的咨询",
        ],
    },
}


SUGGESTION_RULES = {
    "refund_request": [
        "您希望申请退款，请问是什么原因呢？",
        "了解您的退款需求，请问方便说明一下原因吗？",
    ],
    "shipment_inquiry": [
        "我来帮您查询一下物流信息",
        "正在为您查看包裹位置",
    ],
    "order_cancellation": [
        "了解您想取消订单，请问是有什么问题吗？",
        "如需取消订单，请确认是否已付款",
    ],
    "退款": "refund_request",
    "退款申请": "refund_request",
    "物流": "shipment_inquiry",
    "取消订单": "order_cancellation",
}


def get_suggestion_node(state: OrchestratorState, use_llm: bool = True) -> OrchestratorState:
    order_status = state.unified_order.get("status", "") if state.unified_order else ""
    platform = state.current_platform or ""
    user_message = state.unified_order.get("user_message", "") if state.unified_order else ""

    suggestions = []

    if use_llm and LLM_AVAILABLE and user_message:
        try:
            llm = LLMService()
            suggestions = llm.generate_suggestions(
                order_status=order_status,
                platform=platform,
                user_message=user_message,
            )
            state.messages.append({
                "role": "assistant",
                "content": f"LLM Suggestions: {suggestions}"
            })
        except Exception:
            suggestions = _get_rule_based_suggestions(platform, order_status)
    else:
        suggestions = _get_rule_based_suggestions(platform, order_status)

    if not suggestions:
        suggestions = [
            "您好，请问有什么可以帮助您的？",
            "请问您想了解订单的什么信息？",
        ]

    state.suggestions = suggestions
    state.next_node = "rule_check"
    return state


def _get_rule_based_suggestions(platform: str, order_status: str) -> List[str]:
    if platform in ORDER_STATUS_SUGGESTIONS:
        platform_suggestions = ORDER_STATUS_SUGGESTIONS[platform]
        if order_status in platform_suggestions:
            return platform_suggestions[order_status]
    return []


def rule_check_node(state: OrchestratorState, use_llm: bool = True) -> OrchestratorState:
    user_message = state.unified_order.get("user_message", "") if state.unified_order else ""

    action = "general_inquiry"

    if use_llm and LLM_AVAILABLE and user_message:
        try:
            llm = LLMService()
            action = llm.classify_intent(user_message)
        except Exception:
            action = _rule_based_classify(user_message)
    else:
        action = _rule_based_classify(user_message)

    state.selected_action = action
    state.messages.append({
        "role": "system",
        "content": f"Action selected: {action}"
    })
    state.next_node = "end"
    return state


def _rule_based_classify(user_message: str) -> str:
    keywords = {k: v for k, v in SUGGESTION_RULES.items() if k in ["退款", "退款申请", "物流", "取消订单"]}
    for keyword, rule_action in keywords.items():
        if keyword in user_message:
            return rule_action
    return "general_inquiry"
