"""
The module comprises of the HTTP middleware for request logging.
"""

import time
import uuid
import logging
from fastapi import Request, Response
from core.request_context import start_request_context, end_request_context, fetch_request_id

logger = logging.getLogger("faq-qa-bot")


async def request_logging_middleware(request: Request, call_next: callable)-> Response:
    """
    Generates a RequestID and logs every HTTP request and response

    Parameters
    ----------
    request: Request
        The HTTP request
    
    call_next: Callable
        The next endpoint handler in the request processing pipeline

    Returns
    -------
    Response
        The HTTP Response

    """

    
    token = start_request_context()
    request.state.request_id = fetch_request_id()
    start_time = time.perf_counter()
    response = await call_next(request)
    time_elapsed = time.perf_counter() - start_time
    response.headers["X-Request-ID"] = fetch_request_id()
    client_ip = (request.client.host if request.client is not None else "Unknown")
    logger.info(
        "Client=%s | %s %s | Status=%d | Time=%.3fs",
        client_ip,
        request.method,
        request.url.path,
        response.status_code,
        time_elapsed
    )
    end_request_context(token)
    return response
