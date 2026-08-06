# FAQ-QA-Chatbot

This project implements an FAQ Retrieval Augmented Generation Chatbot for the purpose of answering FAQ Questions for the documents NIST RMF Categorize Step-FAQs.pdf and ws2012_licensing-pricing_faq.pdf. The application is deployed on Railway and is accessible through the link below.

### Problem Statement

Problem: Context loss in PDFs for RAG Systems

For unstructured data such as PDFs, standard python libraries are unable to successfully parse such data accurately, extract text, maintain reading order, and preserve tables. For Frequently Asked Questions (FAQ) documents standard chunking methods such as token based splitting and recursive character text splitting are not aware of the document structure and are unable to create chunks to preserve context.

### Solution

Approach: Layout aware parsing and Document Specific Chunking

This project implements layout aware parsing using Upstage AI's document parsing model inorder to preserve PDF data and structure. It also incorporates document specific chunking using a custom-built function inorder to create independent chunks for each question-answer pair to preserve context, avoid mixing context in between questions, and fulfill user requirements by providing desired answers.

### Set up and Installation

This project can be run in a development enviroment which facilitates Python. For that purpose a conda environment should be created (**python 3.13**) to preserve the packages and dependencies. The requirements file should be executed after the conda environment is created to import the specific dependencies needed to run the project. Once the dependencies are imported then a .env file should be created and an Upstage API Key, Google AI API Key, Open AI API Key, and Pinecone API Key must be inserted. 

```bash
conda create -n faqrag python=3.13

conda activate faqrag

pip install -r requirements.txt
```

### Architecture

```text

                 Uvicorn (FastAPI)
                         |
         ________________|_______________
        |                                |
        |                                |
  REST Client                     Gradio Interface
        |                                |
 FastAPI Endpoints                Gradio Callbacks
        |                                |
        |________________________________|
                       |
	          Business Logic              
                       │
              External Services

```

The application follows a layered architecture built around FastAPI with Gradio mounted into the FastAPI application. This allows Gradio and the RestAPI to be served from a single FastAPI application. The Gradio Interface acts as the presentation layer and front-end. The backend contains two server-side execution layers. The Gradio callback layer handles user interactions through the Gradio Interface while the FastAPI REST API layer exposes endpoints to external clients. Both layers invoke the same underlying business logic.

### Case 1 - Run the application

```bash
python app.py
```

### Case 2 - Run the application through external client

```bash
python app.py
```

#### APIs

#### Upload File

A post request would be sent to the FastAPI application. It would comprise of the FAQ PDF file. The response sent back from the fastapi application would be the status of the file upload.

#### API Endpoint

```
0.0.0.0:8000/uploadfile/ 
```

#### Payload
```
{
    "file" : NIST RMF Categorize Step-FAQs.pdf

    key must be the string "file"
    value must be the file
}
```

#### Generate Answer

A post request would be sent to the FastAPI application. It would comprise of a user query. The response sent back from the fastapi application would be the response to the user's query.

#### API Endpoint

```
0.0.0.0:8000/generateanswer/ 
```

#### Payload
```
{
    "query" : What information is needed to categorize a system

    key must be the string "query"
    value must be the query 
}
```

### Evaluation

The evaluation for the FAQ-QA-Chatbot is implemented using three evaluation metrics. Retriever Recall, Answer Correctness, and Contextual Recall. Answer Correctness and Contextual Recall are implemented using DeepEval that implement the LLM-as-a-Judge evaluation approach. GPT-5 was used as the LLM for the respective evaluations. The evaluation results can be displayed by executing the following files. The results for the metric Retriever Recall are recorded for each individual question along with two paraphrased versions of the respective question in the file **Vector Database Retrieval Results - Retriever Recall.docx** present in the folder named evaluation.

#### Answer Correctness 

```bash
cd evaluation

python answer_correctness.py
```
#### Contextual Recall 

```bash
cd evaluation

python contextual_recall.py
```

### Results

| Metric                               | Number of Questions                       | Result          |
|--------------------------------------|-------------------------------------------|-----------------|
| Retriever Recall @k=1                | 219 (73 original + 2 paraphrased versions)| 100% / 1.00     |
| DeepEval G-Eval Answer Correctness   | 73  (original only)                       | 98% / 0.98      |
| DeepEval Contextual Recall           | 73  (original only)                       | 100% / 1.00     |

### Tools and Technologies

* Python
* Langchain
* Gradio
* Pinecone
* Upstage AI Document Parser
* DeepEval (LLM Evals)
* Google Gemini 3.1 Flash-Lite (Answer Generation)
* OpenAI GPT-5 (Evaluation)
* OpenAI GPT-4.1 (Table Summary Generation for tables present in FAQ Questions) 
* OpenAI text-embedding-3 large
* FastAPI (API Endpoints, Middleware)

### Note

Currently both pdf files have been parsed and embedded into the Pinecone Vector Database. To test the storage pipeline for the respective PDFs their record will have to be removed from **pdf_log.csv**, a new index on the Pinecone console will be required to be created. In the present conditions if the same PDFs are uploaded a message stating "This file has already been uploaded and embedded. Please upload a new file." will appear.
After opening the gradio interface, at the moment, any FAQ question can be asked of the two specific PDFs and the relevant answer will be generated. The test results for all of the FAQ questions of the two PDFs are recorded in **final_generated_answers.csv** present in the folder named evaluation.  
