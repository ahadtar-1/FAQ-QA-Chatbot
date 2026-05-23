# FAQ-QA-Chatbot

This project implements an FAQ Retrieval Augmented Generation Chatbot for the purpose of answering FAQ Questions for the documents NIST RMF Categorize Step-FAQs.pdf and ws2012_licensing-pricing_faq.pdf. The application is deployed on Railway and is accessible through the link below.

### Deployment Link

https://faq-qa-chatbot-production.up.railway.app/

### Problem Statement

Problem: Context loss in PDFs for RAG Systems

For unstructured data such as PDFs, standard python libraries are unable to successfully parse such data accurately, extract text, maintain reading order, and preserve tables. For Frequently Asked Questions (FAQ) documents standard chunking methods such as token based splitting and recursive character text splitting are not aware of the document structure and are unable to create chunks to preserve context.

### Solution

Approach: Layout aware parsing and Document Specific Chunking

This project implements layout aware parsing using Upstage AI's document parsing model inorder to preserve PDF data and structure. It also incorporates document specific chunking using a custom-built function inorder to create independent chunks for each question-answer pair to preserve context, avoid mixing context in between questions, and fulfill user requirements by providing desired answers.

### Set up and Installation

This project can be run in a development enviroment which facilitates Python. For that purpose a conda environment should be created (**python 3.13**) to preserve the packages and dependencies. The requirements file should be executed after the conda environment is created to import the specific dependencies needed to run the project. Once the dependencies are imported then a .env file should be created and an Upstage API Key, Open AI API Key, and Pinecone API Key must be inserted. 

```bash
conda create -n faqrag python=3.13

conda activate faqrag

pip install -r requirements.txt
```

#### Case 1 - Run the application through Gradio

```bash
python gradio_frontend.py
```

#### Case 2 - Run the application through FastAPI

```bash
python routes.py
```

## APIs

### Upload File

A post request would be sent to the fastapi application. It would comprise of the FAQ pdf file. The response sent back from the fastapi application would be the status of the file upload.

#### API Endpoint

```
127.0.0.1:8000/uploadfile/ 
```

#### Payload
```
{
    "file" : NIST RMF Categorize Step-FAQs.pdf

    key must be the string "file"
    value must be the file
}
```

### Generate Answer

A post request would be sent to the fastpi application. It would comprise of a user query. The response sent back from the fastapi application would be the response to the user's query.

#### API Endpoint

```
127.0.0.1:8000/generateanswer/ 
```

#### Payload
```
{
    "query" : What information is needed to categorize a system

    key must be the string "query"
    value must be the query 
}
```

### Results

| Metric               | Number of Questions                       | Result          |
|----------------------|-------------------------------------------|-----------------|
| Retriever Recall @k=1| 219 (73 original + 2 paraphrased versions)| 99.54%          |
| Generator Accuracy   | 73  (original only)                       | 97.26%          |

### Tools and Technologies

Python
Langchain
Gradio
Pinecone
Upstage AI Document Parser
OpenAI GPT-4o
FastAPI 

### Note

Currently both pdf files have been parsed and embedded into the Pinecone Vector Database. To test the storage pipeline for the respective PDFs their record will have to be removed from **pdf_log.csv**, a new index on the Pinecone console will be required to be created, and the index_name variable in the **doc_tools.py** will be required to be changed with the new index name. In the present conditions if the same PDFs are uploaded on the Gradio Interface a message stating "This file has already been uploaded and embedded. Please upload a new file." will appear.
After opening the gradio interface, at the moment, any FAQ question can be asked of the two specific PDFs and a relevant answer will be generated. The test results for all of the FAQ questions of the two PDFs are recorded in **Final Generated Answers Statistics.docx**. The **Vector Database Retrieval Results - Completed.docx** contains the results of the FAQ pair being retrieved, as context from the Pinecone Vector Database, for each FAQ question along with two paraphrased versions of each question.  
