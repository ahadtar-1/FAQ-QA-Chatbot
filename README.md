# FAQ-QA-Chatbot

This project implements an FAQ Retrieval Augmented Generation Chatbot for the purpose of answering FAQ Questions for the documents NIST RMF Categorize Step-FAQs.pdf and ws2012_licensing-pricing_faq.pdf

# Set up and Installation

This project can be run in a development enviroment which facilitates Python. For that purpose a conda environment should be created (**python 3.10**) to preserve the packages and dependencies. The requirements file should be executed after the conda environment is created to import the specific dependencies needed to run the project. Once the dependencies are imported then a .env file should be created and an Upstage API Key, Open AI API Key, and Pinecone API Key must be inserted. 

```bash
conda create -n faqrag python=3.10

conda activate faqrag

pip install -r requirements.txt
```
### Testing Application

```bash
python gradio_frontend.py
```