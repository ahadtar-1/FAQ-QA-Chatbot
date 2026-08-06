"""
The module comprises of the API Endpoints for FastAPI. 
"""

import os
import gradio as gr
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, File, UploadFile
from fastapi import HTTPException
from models import QueryRequest, AnswerResponse, UploadResponse
from middleware import request_logging_middleware
from retrieval_pipeline import refine_answer
from doc_tools import upload_pdf
from gradio_frontend import demo
import shutil

app = FastAPI()
app.middleware("http")(request_logging_middleware)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/uploadfile/", response_model=UploadResponse)
async def create_upload_file(file: UploadFile):
    """
    The API endpoint for uploading a file to storage

    Parameters
    ----------
    file: UploadFile
        The upload file object that contains the file
    
    Returns
    -------
    UploadResponse
        The file upload status
    
    """
    

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=415,
            detail="Only PDF files are supported."
        )
    
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    result = upload_pdf(str(file_path))
    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )
    
    return UploadResponse(message=result["message"])


@app.post("/generateanswer/", response_model=AnswerResponse)
async def generate_query_answer(request: QueryRequest):
    """
    The API endpoint for answering the user's query

    Parameters
    ----------
    request: QueryRequest
        The request containing the user's query

    Returns
    -------
    AnswerResponse
        The response to the user's query

    """


    result = refine_answer(request.query)
    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return AnswerResponse(answer=result["answer"], source=result["source"])


app = gr.mount_gradio_app(
    app,
    demo,
    path="/"
)
