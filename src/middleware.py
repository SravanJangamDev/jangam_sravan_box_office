from fastapi import HTTPException, Request
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from uuid import uuid4
from utils.helpers import generate_http_error_response
from utils.logger import get_logger

logger = get_logger()


class GatekeeperMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        try:
            start_time = time.time()
            request_id = str(uuid4())
            response = await call_next(request)
            duration = time.time() - start_time
            response.headers["response-time"] = f"{duration:.4f}s"
            response.headers["request-id"] = request_id
            return response

        except HTTPException as exc:
            logger.error(f"HTTPException: {exc.detail}", exc_info=exc)
            return JSONResponse(
                content={"detail": exc.detail}, status_code=exc.status_code
            )

        except Exception as exc:
            logger.error("Unhandled Exception in GatekeeperMiddleware", exc_info=exc)
            return generate_http_error_response(
                status_code=500, detail=f"Internal Server Error. {exc}"
            )
