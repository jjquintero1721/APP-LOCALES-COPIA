import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configurar logger
logger = logging.getLogger("app")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de todas las peticiones HTTP.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Duration: {duration:.2f}s"
        )

        return response
