from __future__ import annotations

from functools import lru_cache
from typing import Sequence

SUPPORTED_ORDER_PLATFORMS = ("taobao", "douyin_shop", "jd", "xhs", "kuaishou")

_LEGACY_ORDER_ID_EQUIVALENTS: dict[str, Sequence[Sequence[str]]] = {
    "taobao": (("12345678901234",),),
    "douyin_shop": (("6912558345648290211",),),
    "jd": (
        ("98765432101234",),
        ("98765432101237",),
    ),
    "xhs": (("XHS12345678901234",),),
    "kuaishou": (
        ("KS12345678901234",),
        ("KS12345678901235",),
    ),
}


@lru_cache(maxsize=1)
def _load_fixture_equivalents() -> dict[str, tuple[tuple[str, ...], ...]]:
    from providers.utils.fixture_loader import FixtureLoader

    equivalents: dict[str, tuple[tuple[str, ...], ...]] = {}

    for platform in SUPPORTED_ORDER_PLATFORMS:
        groups: list[tuple[str, ...]] = []
        for user_id in FixtureLoader.list_users(platform):
            try:
                user_data = FixtureLoader.load_user(platform, user_id)
            except FileNotFoundError:
                continue

            for order in user_data.get("orders", []):
                order_id = str(order.get("order_id", "")).strip()
                external_order_id = str(order.get("external_order_id", "")).strip()
                if not order_id:
                    continue

                identifiers: list[str] = [order_id]
                if external_order_id and external_order_id != order_id:
                    identifiers.append(external_order_id)

                deduped = tuple(dict.fromkeys(identifiers))
                if deduped not in groups:
                    groups.append(deduped)

        if groups:
            equivalents[platform] = tuple(groups)

    return equivalents


def _equivalents_for_platform(platform: str) -> Sequence[Sequence[str]]:
    normalized_platform = str(platform).strip().lower()
    fixture_equivalents = _load_fixture_equivalents().get(normalized_platform)
    if fixture_equivalents:
        return fixture_equivalents
    return _LEGACY_ORDER_ID_EQUIVALENTS.get(normalized_platform, ())


def iter_order_id_aliases(platform: str, order_id: str) -> list[str]:
    normalized_order_id = str(order_id)
    candidates = [normalized_order_id]
    for equivalent_ids in _equivalents_for_platform(platform):
        normalized = [str(item) for item in equivalent_ids]
        if normalized_order_id in normalized:
            candidates.extend(item for item in normalized if item != normalized_order_id)

    deduped: list[str] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def get_primary_order_id(platform: str, order_id: str) -> str:
    normalized_order_id = str(order_id)
    for equivalent_ids in _equivalents_for_platform(platform):
        normalized = [str(item) for item in equivalent_ids]
        if normalized_order_id in normalized:
            return normalized[-1]
    return normalized_order_id


def build_canonical_order_id(platform: str, order_id: str) -> str:
    return f"{str(platform).strip().lower()}:{get_primary_order_id(platform, order_id)}:order"


def build_canonical_shipment_id(platform: str, order_id: str) -> str:
    return f"{str(platform).strip().lower()}:{get_primary_order_id(platform, order_id)}:shipment"


def build_canonical_after_sale_id(platform: str, order_id: str) -> str:
    return f"{str(platform).strip().lower()}:{get_primary_order_id(platform, order_id)}:after_sale"


def parse_canonical_after_sale_id(platform: str, after_sale_id: str) -> str | None:
    normalized_platform = str(platform).strip().lower()
    normalized_id = str(after_sale_id).strip()
    prefix = f"{normalized_platform}:"
    suffix = ":after_sale"
    if not normalized_id.startswith(prefix) or not normalized_id.endswith(suffix):
        return None
    order_id = normalized_id[len(prefix) : -len(suffix)]
    return order_id or None
