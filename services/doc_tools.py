"""
The module comprises of the tools to upload, parse, and store embeddings of PDFs. 
"""

import os
import logging
import time 
import pandas as pd
import json
import csv
import re
import requests
import shutil
import base64
import langchain
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone.exceptions import PineconeException, PineconeApiException
from openai import OpenAIError, APIStatusError
from langchain.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
upstage_api_key = os.getenv("UPSTAGE_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
index_name = "faqsampleindexjuly2026"
logger = logging.getLogger("faq-qa-bot")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=openai_api_key)
llm = ChatOpenAI(model = "gpt-4.1", temperature = 0)
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


def validate_footer(text: str)-> bool:
    """
    Validates footer in the document

    Parameters
    ----------
    text: str
        The text to be checked

    Returns
    -------
    bool
        The state of the text
    
    """

    
    pattern = r"^\d+\n\d{4}-\d{1,2}-\d{1,2}\nhttps?://[^\s]+$"
    if re.match(pattern, text):
        return True
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

    summary_gen_start_time = time.perf_counter() 
    logger.info("Starting OpenAI summary generation") 
    try:
        response = llm.invoke([message])
        elapsed_time = time.perf_counter() - summary_gen_start_time 
        logger.info("Table summary generated successfully | Time = %.3fs", elapsed_time)
        return response.content
    except Exception as e:
        elapsed_time = time.perf_counter() - summary_gen_start_time 
        logger.exception("Open AI summary generation failed | Time = %.3fs", elapsed_time) 
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
                if(file_elements[index]["content"]["text"] in file_contents["headings"] or (file_elements[index]["content"]["text"] in file_contents["subheadings"] or file_elements[index]["content"]["text"].upper() in file_contents["subheadings"])):
                    continue
                if(file_elements[index]["content"]["text"] not in file_contents["headings"] or file_elements[index]["content"]["text"] not in file_contents["subheadings"]):
                    file_contents["headings"].append(file_elements[index]["content"]["text"])
            if(file_elements[index]["category"] == "list" or file_elements[index]["category"] == "index"):
                table_of_contents = file_elements[index]["content"]["text"].split("\n")
                new_table_of_contents = []
                for row in table_of_contents:
                    if(not row.startswith("Q") and not row[0].isdigit() and "?" not in row):
                        file_contents["subheadings"].append(clean_subheadings(row))
                    else:
                        new_table_of_contents.append(row)        
                refined_table_of_contents = clean_table_of_contents(new_table_of_contents)
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
                         "answers": [],
                         "page_number": []
                        }
    
    questions_started = False
    questions_ended = False
    answer = ""   
    file_contents = extract_headings_and_tableofcontents(file_path)
    with open(file_path, 'r') as file:
        file_parsed_data = json.loads(file.read())
        file_elements = file_parsed_data["elements"]               
        for index, element in enumerate(file_elements):
            if((element["category"] != "footer" and element["category"] != "figure") and (validate_footer(element["content"]["text"]) == False)):
                if(element["content"]["text"] == ""):
                    continue
                if(element["content"]["text"].replace("\n", " ") in file_contents["table_of_contents"]):
                    questions_started = True
                    if(answer != ""):
                        questions_answers["answers"].append("Answer: "+answer.strip())
                        answer = ""
                    questions_answers["questions"].append(element["content"]["text"].replace("\n", " "))
                    questions_answers["page_number"].append(element["page"])
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
                        questions_answers["page_number"].append(element["page"])
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
                        elif(element["category"] == "list"):
                            final_bullet_points = []
                            index = 0
                            count_check = 0
                            bullet_points = element["content"]["text"].split("\n")
                            number_of_bullet_points = len(bullet_points)
                            for bullet_point in bullet_points:
                                if((bullet_point[0].isdigit() and bullet_point[1] == ".") or bullet_point[0] == "·"):
                                    count_check = count_check + 1
                            if(count_check == number_of_bullet_points):
                                for bullet_point in bullet_points:
                                    answer = answer + bullet_point + "\n"
                            if(count_check == 0):
                                for bullet_point in bullet_points:
                                    answer = answer + bullet_point + "\n"
                            if(count_check != 0 and count_check != number_of_bullet_points):
                                for bullet_point in bullet_points:
                                    if((bullet_point[0].isdigit() and bullet_point[1] == ".") or bullet_point[0] == "·"):
                                        final_bullet_points.insert(index, bullet_point)
                                        index = index + 1
                                    else:
                                        previous_bullet_point = final_bullet_points[index - 1]
                                        new_bullet_point = previous_bullet_point + " " + bullet_point
                                        final_bullet_points[index - 1] = new_bullet_point
                                for final_bullet_point in final_bullet_points:
                                    answer = answer + final_bullet_point + "\n"
                        elif(element["category"] == "footnote"):
                            continue 
                        elif("\n" not in element["content"]["text"]): 
                            presence_check = False 
                            for heading in file_contents["headings"]:
                                if("\n" in heading):
                                    splitted_headings = heading.split("\n")
                                    for splitted_heading in splitted_headings:
                                        if(element["content"]["text"] == splitted_heading):
                                            presence_check = True
                                else:
                                    if(element["content"]["text"] == heading):
                                        presence_check = True
                            if(presence_check == False):
                                answer = answer + element["content"]["text"] + "\n"
                        else:
                            answer = answer + element["content"]["text"].replace('-\n', '-').replace("\n", " ") + "\n"
                if(questions_ended == True):
                    footer_follows_check = 0
                    if(answer != ""):
                        remaining_file_contents = file_elements[index+1:]
                        for value in remaining_file_contents:
                            if(value["category"] != "footer"):
                                if(validate_footer(value["content"]["text"]) == True):
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
    pd.DataFrame(questions_answers).rename(columns={"questions": "question", "answers": "answer", "page_numbers": "page"}).to_csv(csv_file_path, index=False)
    df = pd.read_csv("./pdf_log.csv")
    df.loc[df["parsed_json_link"] == file_path, "questions_answers_extracted"] = csv_file_path
    df.to_csv("./pdf_log.csv", index=False)
        
    return questions_answers


def store_embeddings(file_path: str, question_answers: dict)-> bool:
    """
    Stores question-answer pairs in the Pinecone Vector Database

    Parameters
    ----------
    file_path: str
        The fle path

    question_answers: dict
        The question answer pairs with page numbers
    
    Returns
    -------
    bool
        The state of the storing request

    """


    file_name = os.path.basename(file_path)
    questions = question_answers.get("questions", [])
    answers = question_answers.get("answers", [])
    page_numbers = question_answers.get("page_number", [])
    qa_list = []
    metadata_list = []
    for q, a, page in zip(questions, answers, page_numbers):
        pair = f"{q}\n{a}"
        qa_list.append(pair)

        metadata_list.append({"file_name": file_name, "page_number": page})
    
    embedding_storage_start_time = time.perf_counter()
    logger.info("Starting Pinecone embedding generation and storage") 
    try:
        vectorstore = PineconeVectorStore.from_texts(
            texts=qa_list, 
            embedding=embeddings, 
            index_name=index_name,
            metadatas=metadata_list
            )

        elapsed_time = time.perf_counter() - embedding_storage_start_time 
        logger.info("Pinecone embedding generation and storage completed successfully | Time=%.3fs", elapsed_time)
        #Recording embeddings for PDF already created to avoid creating embeddings for the same PDF
        df = pd.read_csv("./pdf_log.csv")
        df.loc[df["uploaded_pdf_link"] == file_path, "embeddings_created"] = "created"
        df.to_csv("./pdf_log.csv", index=False)
        return True
    except APIStatusError as oae:
        logger.exception("OpenAI API error during embedding generation") 
        return f"OpenAIAPI-{oae.message}"
    except OpenAIError as oae:
        logger.exception("OpenAI API communication error") 
        return f"OpenAI-500-{str(oae)}"
    except PineconeApiException as pae:
        logger.exception("Pinecone API error") 
        return f"Pinecone-{str(pae)}"
    except PineconeException as pe:
        logger.exception("Pinecone communication error") 
        return f"Pinecone-500-{str(pe)}"
    except Exception as e:
        logger.exception("Connection error") 
        return f"Connection-{str(e)}"


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


    parsing_start_time = time.perf_counter() 
    logger.info("Starting Upstage PDF Parsing") 
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {upstage_api_key}"}
    files = {"document": open(file_path, "rb")}
    data = {"ocr": "force", "base64_encoding": "['table']", "model": "document-parse-260128", "output_formats": "['html', 'text', 'markdown']"}
    response = requests.post(url, headers=headers, files=files, data=data)
    elapsed_time = time.perf_counter() - parsing_start_time 
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
           logger.info("Upstage AI PDF Parsing completed successfully | Time=%.3fs", elapsed_time) 
        return True
    else:
        logger.error("Upstage AI PDF Parsing failed", response.status_code, elapsed_time)
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
    
    
    pdf_processing_start_time = time.perf_counter() 
    logger.info("Start PDF Processing pipeline") 
    if path == None:
        logger.warning("No file uploaded") 
        return {
        "success": False,
        "status_code": 400,
        "message": "No file uploaded."
        }

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
        logger.warning("File already uploaded and embedded") 
        return {
        "success": False,
        "status_code": 409,
        "message": "This file has already been uploaded and embedded. Please upload a new file."
        }
    if(os.path.exists(file_path) and pd.isna(json_parsed_link_created)):
        result = parse_doc(file_path)
        if(result == False):
            logger.error("PDF Processing failed during UpstageAI parsing") 
            return {
            "success": False,
            "status_code": 503,
            "message": "PDF not successfully processed. The Upstage API is not working."
            }
        else:
            qa_pairs = extract_questions_answers(json_file_path)
            if(qa_pairs == "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."):
                logger.error("PDF Processing failed due to Open AI API") 
                return {
                "success": False,
                "status_code": 503,
                "message": "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."
                }
            else:
                result = store_embeddings(file_path, qa_pairs)
                if(isinstance(result, str)):
                    logger.error("PDF Processing failed during embedding storage") 
                    if "OpenAIAPI" in result:
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. There was an error in the OpenAI API."
                        }
                    if "OpenAI-500" in result:
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. OpenAI Communication issue. Please try again."
                        }
                    if "Pinecone" in result:
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. There was an error in the Pinecone API."
                        }
                    if "Pinecone-500" in result:
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. Pinecone communication issue. Please try again."
                        }
                    if "Connection" in result:                           
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. Connection issue. Please try again."
                        }
                else:
                    total_time = time.perf_counter() - pdf_processing_start_time 
                    logger.info("PDF Processing pipeline completed successfully | Total Time=%.3fs", total_time) 
                    return {
                    "success": True,
                    "message": "PDF successfully stored in Vector Database."
                    }
    if(os.path.exists(file_path) and isinstance(json_parsed_link_created, str) and pd.isna(qa_pairs_extracted)):
        qa_pairs = extract_questions_answers(json_parsed_link_created)
        if(qa_pairs == "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."):
            logger.error("PDF Processing failed due to Open AI API") 
            return {
            "success": False,
            "status_code": 503,
            "message": "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."
            }
        else:
            result = store_embeddings(file_path, qa_pairs)
            if(isinstance(result, str)):
                logger.error("PDF Processing failed due to embeddding storage") 
                if "OpenAIAPI" in result:
                    return {
                    "success": False,
                    "status_code": 503,
                    "message": "We are unable to provide an answer at the moment. There was an error in the OpenAI API."
                    }
                if "OpenAI-500" in result:
                    return {
                    "success": False,
                    "status_code": 503,
                    "message": "We are unable to provide an answer at the moment. OpenAI Communication issue. Please try again."
                    }
                if "Pinecone" in result:
                    return {
                    "success": False,
                    "status_code": 503,
                    "message": "We are unable to provide an answer at the moment. There was an error in the Pinecone API."
                    }
                if "Pinecone-500" in result:
                    return {
                    "success": False,
                    "status_code": 503,
                    "message": "We are unable to provide an answer at the moment. Pinecone communication issue. Please try again."
                    }
                if "Connection" in result:
                    return {
                    "success": False,
                    "status_code": 503,
                    "message": "We are unable to provide an answer at the moment. Connection issue. Please try again."
                    }
            else:
                total_time = time.perf_counter() - pdf_processing_start_time
                logger.info("PDF Processing pipeline completed successfully | Total Time=%.3fs", total_time) 
                return {
                "success": True,
                "message": "PDF successfully stored in Vector Database."
                }
    if(os.path.exists(file_path) and isinstance(json_parsed_link_created, str) and isinstance(qa_pairs_extracted, str) and pd.isna(embeddings_created)):
        df_qa = pd.read_csv(qa_pairs_extracted)
        qa_pairs = {"questions": df_qa["question"].tolist(), "answers": df_qa["answer"].tolist(), "page_number": df_qa["page_number"].tolist()}
        result = store_embeddings(file_path, qa_pairs)
        if(isinstance(result, str)):
            logger.error("PDF Processing failed during embedding generation")
            if "OpenAIAPI" in result:
                return {
                "success": False,
                "status_code": 503,
                "message": "We are unable to provide an answer at the moment. There was an error in the OpenAI API."
                }
            if "OpenAI-500" in result:
                return {
                "success": False,
                "status_code": 503,
                "message": "We are unable to provide an answer at the moment. OpenAI Communication issue. Please try again."
                }
            if "Pinecone" in result:
                return {
                "success": False,
                "status_code": 503,
                "message": "We are unable to provide an answer at the moment. There was an error in the Pinecone API."
                }
            if "Pinecone-500" in result:
                return {
                "success": False,
                "status_code": 503,
                "message": "We are unable to provide an answer at the moment. Pinecone communication issue. Please try again."
                }
            if "Connection" in result:
                return {
                "success": False,
                "status_code": 503,
                "message": "We are unable to provide an answer at the moment. Connection issue. Please try again."
                }
        else:
            total_time = time.perf_counter() - pdf_processing_start_time 
            logger.info("PDF Processing pipeline completed successfully | Total Time=%.3fs", total_time)  
            return {
            "success": True,
            "message": "PDF successfully stored in Vector Database."
            }
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
            logger.error("PDF Processing failed during Upstage AI parsing")
            return {
            "success": False,
            "status_code": 503,
            "message": "PDF not successfully processed. The Upstage API is not working."
            }
        else:
            qa_pairs = extract_questions_answers(json_file_path)
            if(qa_pairs == "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."):
                logger.error("PDF Processing failed due to Open AI API")
                return {
                "success": False,
                "status_code": 503,
                "message": "There was an error in the Open AI API. Unable to extract questions and answers from the PDF."
                }    
            else:
                result = store_embeddings(file_path, qa_pairs)
                if(isinstance(result, str)):
                    logger.error("PDF Processing failed during embedding storage")
                    if "OpenAIAPI" in result:
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. There was an error in the OpenAI API."
                        }
                    if "OpenAI-500" in result:
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. OpenAI Communication issue. Please try again."
                        }
                    if "Pinecone" in result:
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. There was an error in the Pinecone API."
                        }
                    if "Pinecone-500" in result:
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. Pinecone communication issue. Please try again."
                        }
                    if "Connection" in result:                    
                        return {
                        "success": False,
                        "status_code": 503,
                        "message": "We are unable to provide an answer at the moment. Connection issue. Please try again."
                        }
                else:
                    total_time = time.perf_counter() - pdf_processing_start_time 
                    logger.info("PDF Processing pipeline completed successfully | Total Time=%.3fs", total_time) 
                    return {
                    "success": True,
                    "message": "PDF successfully stored in Vector Database."
                    }
