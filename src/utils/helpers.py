from typing import Optional
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from src.utils.logger import get_logger

logger = get_logger()


def generate_http_success_response(
    status_code: int = 200, detail: Optional[str] = "", data: list | dict = {}
):
    try:
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
                "data": data,
            },
        )
    except Exception as e:
        logger.error(f"Error while prepring json response. {e}", exc_info=e)
        raise HTTPException(status_code=500)


def generate_http_error_response(
    status_code: int = 400, detail: Optional[str] = "", data: list | dict = {}
):
    try:
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail, "data": data},
        )
    except Exception as e:
        logger.error(f"Error while prepring json response. {e}", exc_info=e)
        raise HTTPException(status_code=500)
