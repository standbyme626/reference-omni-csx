"""Shipment query service.

Only handles shipment retrieval and normalization.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.platform_gateway_service import PlatformGatewayService
from app.models.unified import Platform

from providers.utils.sim_identity import (
    build_canonical_order_id,
    build_canonical_shipment_id,
    get_primary_order_id,
)


_STATUS_TEXT = {
    "pending": "待发货", "shipped": "已发货", "in_transit": "运输中",
    "delivered": "已签收", "signed": "已签收", "returned": "已退回",
    "unknown": "未知",
}


class ShipmentService:
    """Slim shipment-query service."""

    def __init__(self, gateway: PlatformGatewayService):
        self.gateway = gateway

    def get_shipment(
        self,
        platform: str,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        platform_enum = Platform(platform)
        raw_data = self.gateway.get_shipment(
            platform_enum, order_id, official_run_id=official_run_id,
        )
        return self._normalize(raw_data, platform, order_id)

    def get_shipment_nodes(
        self, platform: str, order_id: str,
        official_run_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        shipment = self.get_shipment(platform, order_id, official_run_id=official_run_id)
        return shipment.get("nodes", [])

    def batch_get_shipments(self, requests: List[Dict[str, str]]) -> Dict[str, Any]:
        shipments: List[Dict[str, Any]] = []
        for req in requests:
            try:
                shipments.append(self.get_shipment(
                    req["platform"], req["order_id"],
                    official_run_id=req.get("official_run_id"),
                ))
            except Exception:
                pass
        return {"shipments": shipments, "total": len(shipments)}

    def _normalize(self, raw: Dict[str, Any], platform: str, order_id: str) -> Dict[str, Any]:
        nodes = self._extract_nodes(raw)
        ext_oid = str(raw.get("external_order_id") or raw.get("order_id") or order_id)
        return {
            "shipment_id": raw.get("shipment_id") or raw.get("sid") or f"SHIP_{order_id}",
            "order_id": order_id, "platform": platform,
            "status": raw.get("status", "unknown"),
            "status_text": _STATUS_TEXT.get(raw.get("status", "unknown"), raw.get("status", "未知")),
            "company": raw.get("company") or raw.get("company_name") or raw.get("logisticsCompany"),
            "tracking_no": raw.get("tracking_no") or raw.get("out_sid") or raw.get("logisticsCode"),
            "nodes": nodes,
            "created_at": raw.get("created_at") or raw.get("send_time") or datetime.now().isoformat(),
            "updated_at": raw.get("updated_at") or datetime.now().isoformat(),
            "requested_order_id": order_id,
            "external_order_id": get_primary_order_id(platform, ext_oid),
            "canonical_order_id": build_canonical_order_id(platform, ext_oid),
            "canonical_shipment_id": build_canonical_shipment_id(platform, ext_oid),
        }

    def _extract_nodes(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        if "nodes" in raw:
            return [{"node": n.get("node") or n.get("status", ""), "time": n.get("time") or n.get("timestamp"),
                     "description": n.get("description") or n.get("desc")}
                    for n in raw["nodes"]]
        if "trace_list" in raw:
            return [{"node": t.get("action", ""), "time": t.get("time"),
                     "description": t.get("desc", "")} for t in raw["trace_list"]]
        return []
