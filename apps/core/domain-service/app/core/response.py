from typing import Any, Dict, Optional


def success_response(data: Any, code: str = "0", message: str = "success") -> Dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data,
    }


def error_response(code: str, message: str) -> Dict[str, Any]:
    return {
        "code": code,
        "message": message,
    }
