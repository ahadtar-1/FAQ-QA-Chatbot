"""
The module comprises of the retrieval tool. 
"""

import os
import langchain
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, PineconeException
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
upstage_api_key = os.getenv("UPSTAGE_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
index_name = "faqsampleindex"
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=openai_api_key)


def retrieve_similar_docs(query: str)-> str:
    """
    Retrieves the question-answer pair with the highest similarity to the query sent by the user from the Pinecone Vector Database

    Parameters
    ----------
    query: str
        The query sent by the user

    similar_doc: str
        The document with the highest similarity
    
    """

    
    try:
        vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
        similar_docs = vectorstore.similarity_search_with_score(query, k=1)

        if similar_docs == None:
            return "No similar docs."
    
        for doc, score in similar_docs:
            print("Score: ", score)
            similar_doc = doc.page_content
            print("Highest score doc: ", "\n", similar_doc)
    
        return similar_doc
    
    except Exception as e:
        print(f"Error retrieving similar documents: {e}")
        return False


if __name__ == "__main__":
    question = "What is Windows Server 2012 Essentials?"
    retrieved_qa_pair = retrieve_similar_docs(question)
    print(retrieved_qa_pair)
    