from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class LoggingMiddleware(BaseHTTPMiddleware):
    def dispatch(self, request: Request, call_next):
        response = call_next(request)
        print(f"Request: {request.method} {request.url}")
        return response