"""
The module manages the request context for the incoming present HTTP request.
"""

import uuid
from contextvars import ContextVar, Token

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


def start_request_context()-> Token:
    """
    Starts a new request context

    Parameters
    ----------
    None
    
    Returns
    -------
    Token
        Token which is used to restore previous context    
    
    """


    request_id = str(uuid.uuid4())
    return request_id_context.set(request_id)


def end_request_context(token: Token)-> None:
    """
    Restores the previous request context

    Parameters
    ----------
    token: Token
        Token returned

    Returns
    -------
    None
    
    """ 

    
    request_id_context.reset(token)


def fetch_request_id()-> str:
    """
    Returns the present Request ID

    Parameters
    ----------
    None

    Returns
    -------
    str
    
    """


    return request_id_context.get()
