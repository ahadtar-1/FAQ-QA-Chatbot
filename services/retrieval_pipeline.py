"""
The module comprises of the retrieval tool and answer refinement tool. 
"""

import os
import logging 
import time
import langchain
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone.exceptions import PineconeException, PineconeApiException
from openai import OpenAIError, APIStatusError
from langchain.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GOOGLE_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
index_name = "faqsampleindexjuly2026"
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=openai_api_key)
gemini_flash_llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=1.0, max_retries=2, thinking_level="high", include_thoughts=False, top_p=0.05)
logger = logging.getLogger("faq-qa-bot")


def retrieve_similar_docs(query: str)-> list:
    """
    Retrieves the question-answer pair with the highest similarity to the query sent by the user from the Pinecone Vector Database

    Parameters
    ----------
    query: str
        The query sent by the user

    Returns
    -------
    list
        The documents with the highest similarity
    
    """


    retrieval_start = time.perf_counter()
    try:
        logger.info("Starting OpenAI embedding generation")
        vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
        logger.info("OpenAI embedding generated")
        logger.info("Starting Pinecone similarity search")
        similar_docs = vectorstore.similarity_search_with_score(query, k=1)
        retrieval_time = time.perf_counter() - retrieval_start
        logger.info("Pinecone similarity search completed | k = %d | Time = %.3fs", 1, retrieval_time)

        if similar_docs == None:
            return "No similar docs."

        similar_docs_list = []
        for doc, score in similar_docs:
            doc_info = {
                "content": doc.page_content,
                "file_name": doc.metadata.get("file_name", "Unknown"),
                "page_number": int(doc.metadata.get("page_number", "Unknown")),
                "similarity_score": score
            }
            similar_docs_list.append(doc_info)
        
        return similar_docs_list
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


def refine_answer(query: str)-> dict:
    """
    Refines the answer retrieved from the Vector Database and generates the final answer

    Parameters
    ----------
    query: str
        The query sent by the user

    Returns
    -------
    dict
        The refined answer, source, and message status.
        
    """

    
    logger.info("Starting Answer generation")
    answer_generation = time.perf_counter()
    if(query == ""):
        logger.warning("Empty query received")
        return {
        "success": False,
        "status_code": 400,
        "message": "Please provide a question."
        }
    
    retrieved_text = retrieve_similar_docs(query)
    if(retrieved_text == "No similar docs."):
        logger.warning("No similar documents found in the Vector DB")
        return {
        "success": False,
        "status_code": 404,
        "message": "There is no available information on the question."
        }
    if(isinstance(retrieved_text, str)):
        if "OpenAIAPI" in retrieved_text:
            logger.error("OpenAI API error during embedding generation")
            return {
            "success": False,
            "status_code": 503,
            "message": "We are unable to provide an answer at the moment. There was an error in the OpenAI API."
            }
        if "OpenAI" in retrieved_text:
            logger.error("OpenAI communication error")
            return {
            "success": False,
            "status_code": 503,
            "message": "We are unable to provide an answer at the moment. OpenAI Communication issue. Please try again."
            }
        if "Pinecone" in retrieved_text:
            logger.error("Pinecone API error")
            return {
            "success": False,
            "status_code": 503,
            "message": "We are unable to provide an answer at the moment. There was an error in the Pinecone API."
            }
        if "Pinecone-500" in retrieved_text:
            logger.error("Pinecone communication error")
            return {
            "success": False,
            "status_code": 503,
            "message": "We are unable to provide an answer at the moment. Pinecone communication issue. Please try again."
            }
        if "Connection" in retrieved_text:
            logger.error("Connection error")
            return {
            "success": False,
            "status_code": 503,
            "message": "We are unable to provide an answer at the moment. Connection issue. Please try again."
            }

    system_message_content = """
        <role>
        You are a Text Assistant.
        </role>
        <task>
        Your task is to extract the answer ONLY from the given text and edit the answer as per the following instructions while preserving its exact structural identity.
        </task>

        <instructions>
        1. Only the answer from the given text is to be edited for output and not the question.
        2. Fix spelling mistakes and mathematical equations only.
        3. Remove non-text noise found exclusively at the absolute end of the input.
        4. Do not add extra blank lines between bullet points.
        5. Do not add extra commas or semicolons where they are not present in the answer.
        6. Combine split elements ONLY if they were accidentally broken mid-sentence.

        PRESERVATION RULES (DO NOT MODIFY):
        1. Word Choice: Never add, swap, or delete existing words.
        2. Paragraphs: Keep existing boundaries. Do not merge or split paragraphs.
        3. Sentences: Keep existing boundaries. Do not break or arbitrarily merge sentences.
        4. Punctuation: Retain all existing commas and semicolons exactly where they are.

        OUTPUT FORMAT:
        Output only the finalized and edited answer in text. Do not provide introductions, explanations, the question, or meta-commentary.
        If zero changes are required, output the original answer in the text exactly as it is.
        </instructions>
        """
    
    source = retrieved_text[0]["file_name"] + " Page: " + str(retrieved_text[0]["page_number"]) 
    messages = [
        ("system", system_message_content),
        ("human", retrieved_text[0]["content"])
        ]
    
    try:
        logger.info("Sending request to Gemini LLM")
        gemini_start = time.perf_counter()
        response = gemini_flash_llm.invoke(messages)
        gemini_time = time.perf_counter() - gemini_start
        logger.info("Gemini execution completed successfully | Time=%.3fs", gemini_time)
        total_time = time.perf_counter() - answer_generation
        logger.info("Answer Generation completed successfully | Total Time = %.3fs", total_time)
        if response and response.content:
            return {
            "success": True,
            "answer": response.text,
            "source": source
            }
    except Exception as e:
        logger.exception("Gemini API request failed")
        return {
            "success": False,
            "status_code": 503,
            "message": "We are unable to provide an answer at the moment. There was an error in the Google API."
            }
