"""
Helper untuk format response JSON yang konsisten di seluruh API.

Contoh penggunaan:
    return success_response(data=items, message="Data berhasil diambil")
    return created_response(data=new_item)
    return paginated_response(data=items, total=100, page=1, size=10)
"""
from typing import Any
from fastapi import status
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Berhasil",
    status_code: int = status.HTTP_200_OK,
) -> dict:
    return {"success": True, "message": message, "data": data}


def created_response(data: Any = None, message: str = "Data berhasil dibuat") -> JSONResponse:
    from fastapi.encoders import jsonable_encoder
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder({"success": True, "message": message, "data": data}),
    )


def paginated_response(
    data: Any,
    total: int,
    page: int,
    size: int,
    message: str = "Berhasil",
) -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        },
    }
