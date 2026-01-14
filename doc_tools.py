"""
The module comprises of the tools to upload, parse, and store embeddings of PDFs. 
"""

import os
import pandas as pd
import json
import csv
import requests
import shutil
import base64
import langchain
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, PineconeException
from langchain.messages import SystemMessage, HumanMessage
import gradio as gr
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
upstage_api_key = os.getenv("UPSTAGE_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
index_name = "faqsampleindex"
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=openai_api_key)
llm = ChatOpenAI(model = "gpt-4o", temperature = 0)
df = pd.read_csv("./pdf_log.csv")


def ends_with_digit(text: str)-> bool:
    """
    Checks if the text ends with a digit

    Parameters
    ----------
    text: str
        The text to be checked
    
    Returns
    -------
    bool
        The state of the text
    
    """
    
    
    if(text[-1].isdigit() == True):
        return True
    else:
        return False


def second_check_question(text: str)-> bool:
    """
    Second checks if the text is a question or not

    Parameters
    ----------
    text: str
        The text to be checked

    Returns
    -------
    bool
        The state of the text
    
    """

    
    if(text.startswith("Q") == True and text.endswith("?") == True):
        return True
    if(text[0].isdigit() == True and text.endswith("?") == True):
        return True
    else:
        return False


def clean_table_of_contents(data: list)-> list:
    """
    Cleans the table of contents

    Parameters
    ----------
    data: list
        The table of contents extracted from the PDF
    
    Returns
    -------
    cleaned_table_of_contents: str
        The cleaned table of contents
    
    """


    cleaned_table_of_contents = []
    double_lined_questions = 0
    
    for q in data:
        idx = q.rfind('?')
        if(idx == -1):
            double_lined_questions += 1
            cleaned_table_of_contents.append(q)
        else:
            cleaned_q = q[:idx+1]
            cleaned_table_of_contents.append(cleaned_q)

    if(double_lined_questions > 0):
        cleaned_table_of_contents_doublelined = []
        doubled_lined_q = ""
        for q in cleaned_table_of_contents:
            doubled_lined_q += q
            if q.endswith("?"):
                cleaned_table_of_contents_doublelined.append(doubled_lined_q)
                doubled_lined_q = ""
            else:
                doubled_lined_q += " "
        return cleaned_table_of_contents_doublelined

    return cleaned_table_of_contents


def clean_subheadings(text: str)-> str:
    """
    Cleans the extracted subheadings

    Parameters
    ----------
    text: str
        The extracted subheading from the PDF

    Returns
    -------
    text: str
        The cleaned subheading
       
    """

    
    sub_heading = text
    text = text.rstrip("0123456789")
    text = text.strip()
    if(text != sub_heading and text.endswith(".")):
        text = text.rstrip(".")    
    
    return text


def get_table_description(text: str)-> str:
    """
    Extracts table descriptions from the parsed PDF using GPT-4o

    Parameters
    ---------
    text: str
        The extracted table text from the parsed PDF

    Returns
    -------
    response.content: str
        The table description

    """

    
    message = HumanMessage(
    content_blocks=[
        {
            "type": "text", 
            "text": "Your task is to provide an explanation of the specific information in the table. The explanation must be of moderate length, written in neat and tidy English, and include the specific details. The explanation must not start with (The table .. or This table ..) and there must be no special characters."
        },
        {
            "type": "image",
            "base64": f"{text}",
            "mime_type": "image/jpeg"
        }
    ]
    )

    try:
        response = llm.invoke([message])
        return response.content
    except Exception as e:
        return None


def extract_headings_and_tableofcontents(file_path: str)-> dict:
    """
    Extracts headings, subheadings, and table of contents from the parsed PDF

    Parameters
    ----------
    file_path: str
        The json file path of the parsed PDF

    Returns
    -------
    file_contents: dict
        The extracted headings, subheadings, and table of contents
        
    """


    file_contents = {"headings": [],
                     "subheadings": [],
                     "table_of_contents": []   
                    }
    sample_tuple = ("list", "index")
    
    with open(file_path, 'r') as file:
        file_parsed_data = json.loads(file.read())
        file_elements = file_parsed_data["elements"]               
        for index in range(0, len(file_elements)):
            if(file_elements[index]["category"] == "heading1"):
                if(file_elements[index]["content"]["text"].replace("\n", " ") in file_contents["table_of_contents"]):
                    break
                if(file_elements[index]["content"]["text"] in file_contents["headings"] or file_elements[index]["content"]["text"] in file_contents["subheadings"]):
                    continue
                if(file_elements[index]["content"]["text"] not in file_contents["headings"] or file_elements[index]["content"]["text"] not in file_contents["subheadings"]):
                    file_contents["headings"].append(file_elements[index]["content"]["text"])
            if(file_elements[index]["category"] == "list" or file_elements[index]["category"] == "index"):
                table_of_contents = file_elements[index]["content"]["text"].split("\n")
                refined_table_of_contents = clean_table_of_contents(table_of_contents)
                for question in refined_table_of_contents:
                    file_contents["table_of_contents"].append(question)
            if(file_elements[index]["category"] == "paragraph"):
                if(file_elements[index]["content"]["text"].replace("\n", " ") in file_contents["table_of_contents"]):
                    break
                if(file_elements[index+1]["category"] in sample_tuple or file_elements[index-1]["category"] in sample_tuple):
                    result = ends_with_digit(file_elements[index]["content"]["text"])
                    if(result == True):
                        file_contents["subheadings"].append(clean_subheadings(file_elements[index]["content"]["text"]))
        
        return file_contents


def extract_questions_answers(file_path: str)-> dict:
    """
    Extracts questions and answers from the parsed PDF

    Parameters
    ----------
    file_path: str
        The json file path of the parsed PDF

    Returns
    -------
    questions_answers: dict
        The extracted questions answers
    
    """

    
    questions_answers = {"questions": [],
                         "answers": []
                        }
    
    questions_started = False
    questions_ended = False
    answer = ""   
    file_contents = extract_headings_and_tableofcontents(file_path)
    with open(file_path, 'r') as file:
        file_parsed_data = json.loads(file.read())
        file_elements = file_parsed_data["elements"]               
        for index, element in enumerate(file_elements):
            if(element["category"] != "footer" and element["category"] != "figure"):
                if(element["content"]["text"].replace("\n", " ") in file_contents["table_of_contents"]):
                    questions_started = True
                    if(answer != ""):
                        questions_answers["answers"].append("Answer: "+answer.strip())
                        answer = ""
                    questions_answers["questions"].append(element["content"]["text"].replace("\n", " "))
                    if(len(questions_answers["questions"]) == len(file_contents["table_of_contents"])):
                        questions_ended = True
                if(element["content"]["text"].replace("\n", " ") not in file_contents["table_of_contents"] and element["content"]["text"] not in file_contents["headings"]):
                    if(second_check_question(element["content"]["text"].replace("\n", " ")) == True):
                        if(questions_started != True):
                            questions_started = True
                        if(answer != ""):
                            questions_answers["answers"].append("Answer: "+answer.strip())
                            answer = ""
                        questions_answers["questions"].append(element["content"]["text"].replace("\n", " "))
                        if(len(questions_answers["questions"]) == len(file_contents["table_of_contents"])):
                            questions_ended = True
                        continue
                    if("\n" in element["content"]["text"]):                        
                        extracted_text = element["content"]["text"].split("\n")
                        check_heading = True
                        for sample in extracted_text:
                            if sample not in file_contents["headings"]:
                                check_heading = False
                                break
                        if(check_heading == True):
                            file_contents["headings"].append(element["content"]["text"])
                            continue
                    if((element["content"]["text"] not in file_contents["subheadings"] and element["content"]["text"].upper() not in file_contents["subheadings"]) and questions_started == True):
                        element_keys = element.keys()
                        if("base64_encoding" in element_keys):
                            table_description = get_table_description(element["base64_encoding"])
                            if(table_description == None):
                                return "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."
                            else:
                                answer = answer + "\n" + table_description + "\n"
                        else:
                            answer = answer + element["content"]["text"].replace("\n", " ") + "\n"
                if(questions_ended == True):
                    footer_follows_check = 0
                    if(answer != ""):
                        remaining_file_contents = file_elements[index+1:]
                        for value in remaining_file_contents:
                            if(value["category"] != "footer"):
                                footer_follows_check = footer_follows_check + 1
                        if(footer_follows_check == 0):
                            questions_answers["answers"].append("Answer: "+answer.strip())
                            answer = "" 
                            break
                if(questions_ended == True and element["content"]["text"] in file_contents["subheadings"]):
                    if(answer != ""):
                        questions_answers["answers"].append("Answer: "+answer.strip())
                        answer = ""
                        break

    #Creating CSV file of question-answer pairs for record
    name_of_file = os.path.basename(file_path)
    csv_file_name = name_of_file.replace(".json", ".csv")
    csv_file_path = "./extracted_qa_pairs/" + csv_file_name
    pd.DataFrame(questions_answers).rename(columns={"questions": "question", "answers": "answer"}).to_csv(csv_file_path, index=False)
    df = pd.read_csv("./pdf_log.csv")
    df.loc[df["parsed_json_link"] == file_path, "questions_answers_extracted"] = csv_file_path
    df.to_csv("./pdf_log.csv", index=False)
        
    return questions_answers


def store_embeddings(file_path: str, question_answers: dict)-> bool:
    """
    Stores question-answer pairs in the Pinecone Vector Database

    Parameters
    ----------
    question_answers: dict
        The question answer pairs
    
    Returns
    -------
    bool
        The state of the storing request

    """


    questions = question_answers.get("questions", [])
    answers = question_answers.get("answers", [])
    qa_list = []
    for q, a in zip(questions, answers):
        pair = f"{q}\n{a}"
        qa_list.append(pair)
    
    try:
        vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
        vectorstore.from_texts(texts=qa_list, embedding=embeddings, index_name=index_name)

        #Recording embeddings for PDF already created to avoid creating embeddings for the same PDF
        df = pd.read_csv("./pdf_log.csv")
        df.loc[df["uploaded_pdf_link"] == file_path, "embeddings_created"] = "created"
        df.to_csv("./pdf_log.csv", index=False)
        return True
    except Exception as e:
        return False


def parse_doc(file_path: str)-> bool:
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
    if(response.status_code == 200):       
        json_response = response.json()
        name_of_file = os.path.basename(file_path)
        final_name_of_file = name_of_file.replace(".pdf", "")
        with open(f"./json_parsedoutputs/{final_name_of_file}.json", "w", encoding="utf-8") as f:
           json.dump(json_response, f, indent=4, ensure_ascii=False)
           
           #Recording PDF is already parsed to avoid api call again
           df = pd.read_csv("./pdf_log.csv")
           df.loc[df["uploaded_pdf_link"] == file_path, "parsed_json_link"] = f"./json_parsedoutputs/{final_name_of_file}.json"
           df.to_csv("./pdf_log.csv", index=False)
        return True
    else:
        return False


def upload_pdf(path: str)-> dict:
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
    json_output_dir = "./json_parsedoutputs"

    os.makedirs(directory_path_to_save, exist_ok = True)
    os.makedirs(json_output_dir, exist_ok = True)
    df = pd.read_csv("./pdf_log.csv")
    file_name = os.path.basename(path)
    file_path = os.path.join(directory_path_to_save, file_name)
    json_file_path = os.path.join(json_output_dir, file_name.replace(".pdf", ".json"))
    if(os.path.exists(file_path)):
        embeddings_created = df.loc[df["uploaded_pdf_link"] == file_path, "embeddings_created"].squeeze()
        json_parsed_link_created = df.loc[df["uploaded_pdf_link"] == file_path, "parsed_json_link"].squeeze()
        qa_pairs_extracted = df.loc[df["uploaded_pdf_link"] == file_path, "questions_answers_extracted"].squeeze()
    
    if(os.path.exists(file_path) and isinstance(embeddings_created, str)):
        return gr.update(value="This file has already been uploaded and embedded. Please upload a new file.", visible = True)
    if(os.path.exists(file_path) and pd.isna(json_parsed_link_created)):
        result = parse_doc(file_path)
        if(result == False):
            return gr.update(value="PDF not successfully processed. The Upstage API is not working.", visible = True)
        else:
            qa_pairs = extract_questions_answers(json_file_path)
            if(qa_pairs == "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."):
                return gr.update(value=qa_pairs, visible = True)
            else:
                result = store_embeddings(file_path, qa_pairs)
                if(result == False):
                    return gr.update(value="There was an error in the Pinecone API. Unable to store PDF.", visible = True)
                else:
                    return gr.update(value = "PDF successfully stored in Vector Database.", visible = True)
    if(os.path.exists(file_path) and isinstance(json_parsed_link_created, str) and pd.isna(qa_pairs_extracted)):
        qa_pairs = extract_questions_answers(json_parsed_link_created)
        if(qa_pairs == "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."):
            return gr.update(value=qa_pairs, visible = True)
        else:
            result = store_embeddings(file_path, qa_pairs)
            if(result == False):
                return gr.update(value="There was an error in the Pinecone API. Unable to store PDF.", visible = True)
            else:
                return gr.update(value = "PDF successfully stored in Vector Database.", visible = True)
    if(os.path.exists(file_path) and isinstance(json_parsed_link_created, str) and isinstance(qa_pairs_extracted, str) and pd.isna(embeddings_created)):
        df_qa = pd.read_csv(qa_pairs_extracted)
        qa_pairs = {"questions": df_qa["question"].tolist(), "answers": df_qa["answer"].tolist()}
        result = store_embeddings(file_path, qa_pairs)
        if(result == False):
            return gr.update(value="There was an error in the Pinecone API. Unable to store PDF.", visible = True)
        else:
            return gr.update(value = "PDF successfully stored in Vector Database.", visible = True) 
    else:
        shutil.copy(path, file_path)
        new_row = {
        "uploaded_pdf_link": file_path,
        "parsed_json_link": None,
        "question_answers_extracted": None,
        "embeddings_created": None
        }
        
        df_new = pd.DataFrame([new_row])
        df_new.to_csv("./pdf_log.csv", mode="a", index=False, header=not os.path.exists("./pdf_log.csv"))
        result = parse_doc(file_path)
        if(result == False):
            return gr.update(value="PDF not successfully processed. The Upstage API is not working.", visible = True)
        else:
            qa_pairs = extract_questions_answers(json_file_path)
            if(qa_pairs == "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."):
                return gr.update(value=qa_pairs, visible = True)
            else:
                result = store_embeddings(file_path, qa_pairs)
                if(result == False):
                    return gr.update(value="There was an error in the Pinecone API. Unable to store PDF.", visible = True)
                else:
                    return gr.update(value = "PDF successfully stored in Vector Database.", visible = True)
    