import pytest
import sys

sys.path.insert(0, '/home/kkk/Project/platform-sim/apps/ai-orchestrator')

from graphs.orchestrator import OrchestratorGraph
from nodes.state import OrchestratorState


class TestLLME2E:
    def test_taobao_refund_scenario(self):
        orch = OrchestratorGraph()
        result = orch.run(
            order_id='TB_ORDER_001',
            platform='taobao',
            unified_order={
                'order_id': 'TB_ORDER_001',
                'status': 'shipped',
                'user_message': '我想申请退款，商品损坏'
            }
        )
        state = OrchestratorState(**result) if isinstance(result, dict) else result
        assert state.current_order_id == 'TB_ORDER_001'
        assert state.current_platform == 'taobao'
        assert state.selected_action == 'refund_request'
        assert len(state.suggestions) >= 1
        print(f"\n✅ 淘宝退款场景: action={state.selected_action}, suggestions={len(state.suggestions)}")

    def test_douyin_shipment_inquiry(self):
        orch = OrchestratorGraph()
        result = orch.run(
            order_id='DS_ORDER_001',
            platform='douyin_shop',
            unified_order={
                'order_id': 'DS_ORDER_001',
                'status': 'shipped',
                'user_message': '查询物流到哪了'
            }
        )
        state = OrchestratorState(**result) if isinstance(result, dict) else result
        assert state.current_order_id == 'DS_ORDER_001'
        assert state.current_platform == 'douyin_shop'
        assert state.selected_action == 'shipment_inquiry'
        assert len(state.suggestions) >= 1
        print(f"\n✅ 抖店物流查询: action={state.selected_action}, suggestions={len(state.suggestions)}")

    def test_wecom_general_inquiry(self):
        orch = OrchestratorGraph()
        result = orch.run(
            order_id='WECOM_CONV_001',
            platform='wecom_kf',
            unified_order={
                'order_id': 'WECOM_CONV_001',
                'status': 'in_session',
                'user_message': '你们的产品怎么样'
            }
        )
        state = OrchestratorState(**result) if isinstance(result, dict) else result
        assert state.current_order_id == 'WECOM_CONV_001'
        assert state.current_platform == 'wecom_kf'
        assert len(state.suggestions) >= 1
        print(f"\n✅ 企微会话: suggestions={len(state.suggestions)}")

    def test_jd_order_cancellation(self):
        orch = OrchestratorGraph()
        result = orch.run(
            order_id='JD_ORDER_001',
            platform='jd',
            unified_order={
                'order_id': 'JD_ORDER_001',
                'status': 'wait_ship',
                'user_message': '我想取消订单'
            }
        )
        state = OrchestratorState(**result) if isinstance(result, dict) else result
        assert state.current_order_id == 'JD_ORDER_001'
        assert state.selected_action == 'order_cancellation'
        print(f"\n✅ 京东取消订单: action={state.selected_action}")

    def test_xhs_refund_scenario(self):
        orch = OrchestratorGraph()
        result = orch.run(
            order_id='XHS_ORDER_001',
            platform='xhs',
            unified_order={
                'order_id': 'XHS_ORDER_001',
                'status': 'delivered',
                'user_message': '商品有问题要退款'
            }
        )
        state = OrchestratorState(**result) if isinstance(result, dict) else result
        assert state.current_order_id == 'XHS_ORDER_001'
        assert state.selected_action == 'refund_request'
        print(f"\n✅ 小红书退款: action={state.selected_action}")

    def test_kuaishou_shipment_inquiry(self):
        orch = OrchestratorGraph()
        result = orch.run(
            order_id='KS_ORDER_001',
            platform='kuaishou',
            unified_order={
                'order_id': 'KS_ORDER_001',
                'status': 'delivering',
                'user_message': '包裹到哪了'
            }
        )
        state = OrchestratorState(**result) if isinstance(result, dict) else result
        assert state.current_order_id == 'KS_ORDER_001'
        assert state.selected_action == 'shipment_inquiry'
        print(f"\n✅ 快手物流查询: action={state.selected_action}")
