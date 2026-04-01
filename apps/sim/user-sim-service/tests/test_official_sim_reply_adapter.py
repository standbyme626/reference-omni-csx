from nodes.reply.official_sim import OfficialSimReplyAdapter


def test_order_status_reply_from_official_sim(monkeypatch):
    adapter = OfficialSimReplyAdapter(base_url="http://localhost:8000")

    def fake_call(**kwargs):
        return {"data": {"order": {"status": "wait_ship"}}}

    monkeypatch.setattr(adapter, "_call_official_sim", fake_call)

    result = adapter.get_reply(
        run_id="run_1",
        user_message="订单怎么样了",
        context={"platform": "taobao", "order_id": "ORDER_001", "intent": "ask_order_status"},
    )

    assert result["source"] == "official-sim"
    assert "ORDER_001" in result["text"]
    assert "wait_ship" in result["text"]


def test_shipment_reply_from_official_sim(monkeypatch):
    adapter = OfficialSimReplyAdapter(base_url="http://localhost:8000")

    def fake_call(**kwargs):
        return {
            "data": {
                "shipment": {
                    "status": "in_transit",
                    "tracking_no": "SF1234567890",
                }
            }
        }

    monkeypatch.setattr(adapter, "_call_official_sim", fake_call)

    result = adapter.get_reply(
        run_id="run_2",
        user_message="物流到哪里了",
        context={"platform": "taobao", "order_id": "ORDER_002", "intent": "ask_shipment"},
    )

    assert result["source"] == "official-sim"
    assert "in_transit" in result["text"]
    assert "SF1234567890" in result["text"]


def test_refund_reply_from_official_sim(monkeypatch):
    adapter = OfficialSimReplyAdapter(base_url="http://localhost:8000")

    def fake_call(**kwargs):
        return {
            "data": {
                "after_sale": {
                    "status": "refund_pending",
                    "refund_amount": "88.00",
                }
            }
        }

    monkeypatch.setattr(adapter, "_call_official_sim", fake_call)

    result = adapter.get_reply(
        run_id="run_3",
        user_message="退款进度",
        context={"platform": "taobao", "order_id": "ORDER_003", "intent": "ask_refund"},
    )

    assert result["source"] == "official-sim"
    assert "refund_pending" in result["text"]
    assert "88.00" in result["text"]


def test_missing_order_id_falls_back_to_stub():
    adapter = OfficialSimReplyAdapter(base_url="http://localhost:8000")

    result = adapter.get_reply(
        run_id="run_4",
        user_message="帮我查一下",
        context={"platform": "taobao", "intent": "ask_order_status"},
    )

    assert result["fallback_to_stub"] is True
    assert result["source"] == "official-sim"
