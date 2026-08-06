"""
The module comprises of the Pydantic models.
"""

from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

class AnswerResponse(BaseModel):
    answer: str
    source: str

class UploadResponse(BaseModel):
    message: str
    