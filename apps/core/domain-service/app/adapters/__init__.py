"""Unified adapter layer.

Each platform gets dedicated adapter classes implementing the protocol
interfaces defined in ``protocols.py``.  The ``registry.py`` module
bundles them into a central ``AdapterRegistry``.
"""

# Protocol interfaces
from .protocols import AfterSaleAdapter, ConversationAdapter, OrderAdapter, ShipmentAdapter

# Registry
from .registry import AdapterRegistry, bootstrap_default_registry

# Platform adapters
from .taobao import TaobaoOrderAdapter
from .douyin import DouyinAfterSaleAdapter, DouyinOrderAdapter, DouyinShipmentAdapter
from .jd import JDAfterSaleAdapter, JDOrderAdapter, JDShipmentAdapter
from .xhs import XHSAfterSaleAdapter, XHSOrderAdapter, XHSShipmentAdapter
from .kuaishou import KuaishouAfterSaleAdapter, KuaishouOrderAdapter, KuaishouShipmentAdapter
from .wecom_kf import WeComKfConversationAdapter

__all__ = [
    # Protocols
    "OrderAdapter",
    "ShipmentAdapter",
    "AfterSaleAdapter",
    "ConversationAdapter",
    # Registry
    "AdapterRegistry",
    "bootstrap_default_registry",
    # Platform adapters
    "TaobaoOrderAdapter",
    "DouyinOrderAdapter",
    "DouyinShipmentAdapter",
    "DouyinAfterSaleAdapter",
    "JDOrderAdapter",
    "JDShipmentAdapter",
    "JDAfterSaleAdapter",
    "XHSOrderAdapter",
    "XHSShipmentAdapter",
    "XHSAfterSaleAdapter",
    "KuaishouOrderAdapter",
    "KuaishouShipmentAdapter",
    "KuaishouAfterSaleAdapter",
    "WeComKfConversationAdapter",
]
