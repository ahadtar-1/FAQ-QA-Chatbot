"""
The module comprises of the tools to upload and parse PDFs. 
"""

import os
import shutil
import gradio as gr


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
