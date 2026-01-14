"""
The module comprises of the API Endpoints for FastAPI. 
"""

import os
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, File, UploadFile
from functions_fastapi import generate_answer_for_query, upload_pdf_to_storage
import uvicorn
import shutil

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile)-> str:
    """
    The API endpoint for uploading a file to storage

    Parameters
    ----------
    file: UploadFile
        The upload file object that contains the file
    
    Returns
    -------
    str
        The file upload status
    
    """
    
    
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    result = upload_pdf_to_storage(file_path)
    return result


@app.post("/generateanswer/")
async def generate_query_answer(query: str)-> str:
    """
    The API endpoint for answering the user's query

    Parameters
    ----------
    query: str
        The query sent by the user

    Returns
    -------
    str
        The response to the user's query

    """


    result = generate_answer_for_query(query)
    return result



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
