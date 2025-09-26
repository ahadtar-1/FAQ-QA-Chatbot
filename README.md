# FAQ-QA-Chatbot

This project implements an FAQ Retrieval Augmented Generation Chatbot for the purpose of answering FAQ Questions for the documents NIST RMF Categorize Step-FAQs.pdf and ws2012_licensing-pricing_faq.pdf

### Set up and Installation

This project can be run in a development enviroment which facilitates Python. For that purpose a conda environment should be created (**python 3.10**) to preserve the packages and dependencies. The requirements file should be executed after the conda environment is created to import the specific dependencies needed to run the project. Once the dependencies are imported then a .env file should be created and an Upstage API Key, Open AI API Key, and Pinecone API Key must be inserted. 

```bash
conda create -n faqrag python=3.10

conda activate faqrag

pip install -r requirements.txt
```

### Run the application

```bash
python gradio_frontend.py
```

### Storage pipeline

Currently both pdf files have been parsed and embedded into the Pinecone Vector Database. To test the storage pipeline for the respective PDFs their record will have to be removed from **pdf_log.csv**, a new index on the Pinecone console will be required to be created, and the index_name variable in the **doc_tools.py** will be required to be changed with the new index name. In the present conditions if the same PDFs are uploaded on the Gradio Interface a message stating "This file has already been uploaded and embedded. Please upload a new file." will appear.

### Retrieval and Answer Generation pipeline

After opening the gradio interface, at the moment, any FAQ question can be asked of the two specific PDFs and a relevant answer will be generated. The test results for all of the FAQ questions of the two PDFs are recorded in **Final Generated Answers Statistics.docx**. The **Vector Database Retrieval Results - Completed.docx** contains the results of the FAQ pair being retrieved, as context from the Pinecone Vector Database, for each FAQ question along with two paraphrased versions of each question.  