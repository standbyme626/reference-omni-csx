from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class OdooOrderLinkResolver:
    """Resolve simulated platform order IDs to stable Odoo order/picking links.

    There is no natural key between the platform-sim fixture order IDs and the
    imported Odoo dataset. This resolver creates a deterministic, persisted link
    so the middle platform can consistently enrich a platform order with ERP
    facts across restarts.
    """

    def __init__(self, client: Any, link_file: Optional[str | Path] = None):
        self.client = client
        self.link_file = Path(link_file) if link_file else self._default_link_file()

    def _default_link_file(self) -> Path:
        return Path(__file__).resolve().parents[3] / "data" / "runtime" / "odoo_order_links.json"

    def _load_links(self) -> Dict[str, Any]:
        if not self.link_file.exists():
            return {"links": {}}
        try:
            payload = json.loads(self.link_file.read_text(encoding="utf-8"))
        except Exception:
            return {"links": {}}
        if not isinstance(payload, dict):
            return {"links": {}}
        payload.setdefault("links", {})
        return payload

    def _save_links(self, payload: Dict[str, Any]) -> None:
        self.link_file.parent.mkdir(parents=True, exist_ok=True)
        self.link_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _make_key(self, platform: str, platform_order_id: str) -> str:
        return f"{platform}:{platform_order_id}"

    async def _list_sale_orders(self) -> List[Dict[str, Any]]:
        rows = await self.client.execute(
            "sale.order",
            "search_read",
            [[]],
            {
                "fields": ["id", "name"],
                "order": "id asc",
            },
        )
        return [row for row in (rows or []) if row.get("id") and row.get("name")]

    async def _find_picking_by_origin(self, origin: str) -> Optional[Dict[str, Any]]:
        rows = await self.client.execute(
            "stock.picking",
            "search_read",
            [[("origin", "=", origin)]],
            {
                "fields": ["id", "name", "origin"],
                "order": "id asc",
            },
        )
        for row in rows or []:
            if row.get("id") and row.get("name"):
                return row
        return None

    def _pick_deterministic_candidate(
        self,
        platform: str,
        platform_order_id: str,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        digest = hashlib.sha256(f"{platform}:{platform_order_id}".encode("utf-8")).hexdigest()
        index = int(digest[:16], 16) % len(candidates)
        return candidates[index]

    async def resolve_order_link(
        self,
        platform: str,
        platform_order_id: str,
    ) -> Optional[Dict[str, Any]]:
        payload = self._load_links()
        key = self._make_key(platform, platform_order_id)
        cached = payload["links"].get(key)
        if isinstance(cached, dict):
            return cached

        sale_orders = await self._list_sale_orders()
        if not sale_orders:
            return None

        pickings_by_origin: Dict[str, Dict[str, Any]] = {}
        for row in sale_orders:
            order_name = str(row.get("name", "")).strip()
            if not order_name:
                continue
            picking = await self._find_picking_by_origin(order_name)
            if picking is not None:
                pickings_by_origin[order_name] = picking

        picking_backed_orders = [row for row in sale_orders if row.get("name") in pickings_by_origin]
        candidate_pool = picking_backed_orders or sale_orders
        selected = self._pick_deterministic_candidate(platform, platform_order_id, candidate_pool)

        picking = pickings_by_origin.get(str(selected["name"]))
        link = {
            "platform": platform,
            "platform_order_id": platform_order_id,
            "odoo_order_id": str(selected["id"]),
            "odoo_order_name": str(selected["name"]),
            "odoo_picking_id": str(picking["id"]) if picking and picking.get("id") is not None else None,
            "odoo_picking_name": str(picking["name"]) if picking and picking.get("name") is not None else None,
            "odoo_picking_origin": str(picking["origin"]) if picking and picking.get("origin") is not None else None,
            "link_strategy": "deterministic_persisted",
        }

        payload["links"][key] = link
        self._save_links(payload)
        return link
