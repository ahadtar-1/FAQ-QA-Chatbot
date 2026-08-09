"""
The file comprises of the User Interface for the FAQ QA Chatbot.
"""

import os
import logging
import gradio as gr
from core.request_context import start_request_context, end_request_context
from services.doc_tools import upload_pdf
from services.retrieval_pipeline import refine_answer

logger = logging.getLogger("faq-qa-bot")


def ask_query(query):

    
    token = start_request_context()
    try:
        result = refine_answer(query)
        if result["success"]:
            return (result["answer"], gr.update(value=result["source"]), gr.update(visible=True))

        return (result["message"], gr.update(value=""), gr.update(visible=False))
    finally:
        end_request_context(token)


def process_pdf(file_path):

    
    token = start_request_context() #Aug9th
    try: #Aug9th
        if file_path is None: #Aug9th
            logger.warning("No file uploaded")
            return "No file uploaded." #Aug9th

        result = upload_pdf(file_path) #Aug9th
        return result["message"] #Aug9th
    finally: #Aug9th
        end_request_context(token) #Aug9th


with gr.Blocks(theme=gr.themes.Glass(primary_hue="slate")) as demo:
    
    gr.Markdown("<h1 style='text-align: center;'>FAQ QA Chatbot</h1>")

    file_input = gr.File(type="filepath", file_types=[".pdf"], label="Upload")
    upload_button = gr.Button("📤 Process PDF")
    output = gr.Textbox(label = "PDF Status", visible = True, lines = 1)
            
    upload_button.click(
        process_pdf,
        inputs = file_input,
        outputs = [output] 
    )

    with gr.Row():
        question_box = gr.Textbox(label="Question", placeholder="Enter your question here...", lines = 4)
    
    send_button = gr.Button("Send")
    qa_output = gr.Textbox(label="Answer", visible=True, lines=6)

    with gr.Accordion("Source", open=False, visible=False) as source_selection:
        source_output = gr.Textbox(label= "Source", interactive=False)

    send_button.click(
        ask_query,
        inputs = question_box,
        outputs = [qa_output, source_output, source_selection]
        )
