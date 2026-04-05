from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict


class ReplySource(str, Enum):
    OFFICIAL_SIM = "official-sim"
    STUB = "stub"
    UNIFIED = "unified"


class ReplyAdapterError(RuntimeError):
    """Raised when a reply adapter cannot produce a valid reply in strict mode."""


class ReplyAdapter(ABC):
    @abstractmethod
    def get_reply(
        self,
        run_id: str,
        user_message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_source(self) -> ReplySource:
        pass
