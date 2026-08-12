from typing import Any

def success_response(data: Any = None, message: str = "") -> dict:
    return {
        "success": True,
        "data": data,
        "message": message,
        "errors": [],
    }

def error_response(message: str, errors: list | None = None) -> dict:
    return {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors or [],
    }