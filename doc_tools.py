"""
The module comprises of the tools to upload and parse PDFs. 
"""

import os
import json
import requests
import shutil
import gradio as gr
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
upstage_api_key = os.getenv("UPSTAGE_API_KEY")


def parse_doc(file_path: str):
    """
    Sends a request to Upstage AI api to parse the PDF

    Parameters
    ----------
    file_path : str
        The file path of the PDF

    Returns
    -------
    bool
        The state of the response from the api      
    
    
    
    """


    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {upstage_api_key}"}
    files = {"document": open(file_path, "rb")}
    data = {"ocr": "force", "base64_encoding": "['table']", "model": "document-parse", "output_formats": "['html', 'text']"}
    response = requests.post(url, headers=headers, files=files, data=data)
    print(response.status_code)
    if(response.status_code == 200):       
        json_response = response.json()
        name_of_file = os.path.basename(file_path)
        with open(f"./{name_of_file}.json", "w", encoding="utf-8") as f:
           json.dump(json_response, f, indent=4, ensure_ascii=False)
        return True
    else:
        return False


def upload_pdf(path: str):
    """
    Uploads a PDF file and stores it in a directory

    Parameters
    ----------
    path : str
        The file path set by Gradio for the PDF
    
    Returns
    -------
    dict
        The updated Textbox Gradio object
    
    """
    
    
    if path == None:
        return gr.update(value="No file uploaded.", visible=True)

    directory_path_to_save = "./uploaded_pdfdocs"
    os.makedirs(directory_path_to_save, exist_ok = True)

    file_name = os.path.basename(path)
    file_path = os.path.join(directory_path_to_save, file_name)
    if(os.path.exists(file_path)):
        return gr.update(value="This file has already been uploaded. Please upload a new file.", visible = True)
    else:
        shutil.copy(path, file_path)           
        return gr.update(value="PDF successfully processed", visible = True)
