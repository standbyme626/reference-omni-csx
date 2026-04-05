from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.platform_gateway_service import PlatformGatewayService
from models.unified import Platform

from providers.utils.sim_identity import (
    build_canonical_order_id,
    build_canonical_shipment_id,
    get_primary_order_id,
)


class ShipmentDomainService:
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
            platform_enum,
            order_id,
            official_run_id=official_run_id,
        )
        
        return self._normalize_shipment(raw_data, platform, order_id)
    
    def get_shipment_nodes(
        self,
        platform: str,
        order_id: str,
        official_run_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        shipment = self.get_shipment(platform, order_id, official_run_id=official_run_id)
        return shipment.get("nodes", [])
    
    def batch_get_shipments(self, requests: List[Dict[str, str]]) -> Dict[str, Any]:
        shipments = []
        for req in requests:
            try:
                shipment = self.get_shipment(
                    req["platform"],
                    req["order_id"],
                    official_run_id=req.get("official_run_id"),
                )
                shipments.append(shipment)
            except Exception:
                pass
        
        return {
            "shipments": shipments,
            "total": len(shipments),
        }
    
    def _normalize_shipment(
        self,
        raw: Dict[str, Any],
        platform: str,
        order_id: str,
    ) -> Dict[str, Any]:
        nodes = []
        
        if "nodes" in raw:
            nodes = [
                {
                    "node": n.get("node") or n.get("status", ""),
                    "time": n.get("time") or n.get("timestamp"),
                    "description": n.get("description") or n.get("desc"),
                }
                for n in raw.get("nodes", [])
            ]
        elif "trace_list" in raw:
            for trace in raw.get("trace_list", []):
                nodes.append({
                    "node": trace.get("action", ""),
                    "time": trace.get("time"),
                    "description": trace.get("desc", ""),
                })
        
        return {
            "shipment_id": raw.get("shipment_id") or raw.get("sid") or f"SHIP_{order_id}",
            "order_id": order_id,
            "platform": platform,
            "status": raw.get("status", "unknown"),
            "status_text": self._get_status_text(raw.get("status", "unknown")),
            "company": raw.get("company") or raw.get("company_name") or raw.get("logisticsCompany"),
            "tracking_no": raw.get("tracking_no") or raw.get("out_sid") or raw.get("logisticsCode"),
            "nodes": nodes,
            "created_at": raw.get("created_at") or raw.get("send_time") or datetime.now().isoformat(),
            "updated_at": raw.get("updated_at") or datetime.now().isoformat(),
            "requested_order_id": order_id,
            "external_order_id": get_primary_order_id(
                platform,
                str(raw.get("external_order_id") or raw.get("order_id") or order_id),
            ),
            "canonical_order_id": build_canonical_order_id(
                platform,
                str(raw.get("external_order_id") or raw.get("order_id") or order_id),
            ),
            "canonical_shipment_id": build_canonical_shipment_id(
                platform,
                str(raw.get("external_order_id") or raw.get("order_id") or order_id),
            ),
        }
    
    def _get_status_text(self, status: str) -> str:
        status_map = {
            "pending": "待发货",
            "shipped": "已发货",
            "in_transit": "运输中",
            "delivered": "已签收",
            "signed": "已签收",
            "returned": "已退回",
            "unknown": "未知",
        }
        return status_map.get(status, status)
