"""
The file comprises of the User Interface for the FAQ QA Chatbot.
"""

import gradio as gr
from doc_tools import upload_pdf


with gr.Blocks(theme=gr.themes.Glass(primary_hue="slate")) as demo:
    
    gr.Markdown("<h1 style='text-align: center;'>FAQ QA Chatbot</h1>")

    file_input = gr.File(type="filepath", file_types=[".pdf"], label="Upload")
    upload_button = gr.Button("📤 Process PDF")
    output = gr.Textbox(label = "Output", visible = False, lines = 1)
            
    upload_button.click(
        upload_pdf,
        inputs = file_input,
        outputs = [output] 
    )

    with gr.Row():
        question_box = gr.Textbox(label="Question", placeholder="Enter your question here...", lines = 4)
    
    send_button = gr.Button("Send")
    qa_output = gr.Textbox(label="Answer", visible=False, lines=4)

demo.launch(share = True)
