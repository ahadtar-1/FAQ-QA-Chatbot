"""
The module configures application logging.
"""

import logging
from request_context import fetch_request_id


class RequestIDFilter(logging.Filter):
    """
    Adds the present RequestID to each log record

    """

    
    def filter(self, record)-> bool:
        """
        Adds the Request ID in the context variable

        Parameters
        ----------
        record: logging.LogRecord
            The log record

        Returns
        -------
        bool

        """


        record.request_id = fetch_request_id()
        return True


def setup_logging()-> None:
    """
    Configures application logging

    Parameters
    ----------
    None

    Returns
    -------
    None
    """


    formatter = logging.Formatter("%(asctime)s | %(levelname)s | RequestID=%(request_id)s | %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
