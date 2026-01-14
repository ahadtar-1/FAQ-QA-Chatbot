"""
The module comprises of the document grading tool. 
"""

import os
import time
import random
import json
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")


def document_grading(query :str, retrieved_docs: list)-> list:
    """
    Verifies the relevance and irrelevance of retrieved documents from the Vector Database

    Parameters
    ----------
    query: str
        The query sent by the user

    retrieved_docs: list
        The retrieved documents from the Vector Database

    relevant_docs: list
        The relevant docs with respect to the query 
        
    """


    user_message = f"Query:\n{query}\n\nRetrieved Documents:\n{retrieved_docs[0]}\n\n{retrieved_docs[1]}\n\n{retrieved_docs[2]}\n\n{retrieved_docs[3]}"

    try:
        response = client.responses.create(
            model="gpt-5",
            input=[
                {
                "role": "system",
                "content": [
                {
                    "type": "input_text",
                    "text": "You are a Document relevance evaluator. \nYour task is to evaluate retrieved documents, that have been retrieved from a vector database, and identify if these documents are relevant or irrelevant in relation to the specific query.\n\nImportant Instructions:\nThe output JSON object must be a key-value pair with the keys containing only two possible values \"relevant\" or \"irrelevant\" in string format and the values containing the documents in list format. \nIf a Query is word-by-word identical to any question word-by-word of any of the Retrieved documents or identical to a paraphrased version of any question of the Retrieved documents, then only that retrieved document is relevant and the other Retrieved documents are irrelevant.\nIf a Query is a long query which contains multiple questions in a single query and those multiple questions in the single query are word-by-word identical to any of the questions word-by-word of any of the Retrieved documents or identical to a paraphrased version of any of the questions of the Retrieved documents, then only those retrieved documents are relevant and the other Retrieved documents are irrelevant."
                }
                ]
                },
                {
                "role": "user",
                "content": [
                {
                    "type": "input_text",
                    "text": "Query:\nWhat is new in Windows Server 2012?\n\nRetrieved Documents:\nQ1. What is new in Windows Server 2012?\nAnswer: Windows Server 2012 brings our company's experience building and operating public clouds to the server platform for private clouds. The new licensing and packaging makes it easier to manage workloads in highly virtualized public and private cloud environments. Windows Server 2012 will move to a consistent licensing model and will have common features enabling the reduction of editions. These include\n· Two editions, Standard and Datacenter. · Single licenses that cover up to two physical processors. · Editions differentiated by virtualization rights only (two for Standard; unlimited for Datacenter).\n\nQ2. What is the difference between Windows Server 2012 Standard edition and Windows Server 2012 Datacenter edition?\nAnswer: Both Standard and Datacenter editions provide the same set of features; the only thing that differentiates the editions is the number of Virtual Machines (VMs). A Standard edition license will entitle you to run up to two VMs on up to two processors (subject to the VM use rights outlined in the Product Use Rights document). A Datacenter edition license will entitle you to run an unlimited number of VMs on up to two processors.\n\nQ10. Can I use one Standard license to cover a 1-processor server?\nAnswer: Yes. The Standard edition license will allow you to license up to two physical processors on a single server; however it does not require that the server has two physical processors.\n\nQ12. Can I assign a Windows Server 2012 license to a virtual machine?\nAnswer: No. A license is assigned to the physical server. Each license will cover up to two physical processors."
                }
                ]
                },
                {
                "role": "assistant",
                "content": [
                {
                    "type": "output_text",
                    "text": "{\"relevant\":[\"Q1. What is new in Windows Server 2012?\nAnswer: Windows Server 2012 brings our company's experience building and operating public clouds to the server platform for private clouds. The new licensing and packaging makes it easier to manage workloads in highly virtualized public and private cloud environments. Windows Server 2012 will move to a consistent licensing model and will have common features enabling the reduction of editions. These include\n· Two editions, Standard and Datacenter. · Single licenses that cover up to two physical processors. · Editions differentiated by virtualization rights only (two for Standard; unlimited for Datacenter).\"],\"irrelevant\":[\"Q2. What is the difference between Windows Server 2012 Standard edition and Windows Server 2012 Datacenter edition?\nAnswer: Both Standard and Datacenter editions provide the same set of features; the only thing that differentiates the editions is the number of Virtual Machines (VMs). A Standard edition license will entitle you to run up to two VMs on up to two processors (subject to the VM use rights outlined in the Product Use Rights document). A Datacenter edition license will entitle you to run an unlimited number of VMs on up to two processors.\",\"Q10. Can I use one Standard license to cover a 1-processor server? \nAnswer: Yes. The Standard edition license will allow you to license up to two physical processors on a single server; however it does not require that the server has two physical processors.\",\"Q12. Can I assign a Windows Server 2012 license to a virtual machine?\nAnswer: No. A license is assigned to the physical server. Each license will cover up to two physical processors.\"]}"
                }
                ]
                },
                {
                "role": "user",
                "content": [
                {
                    "type": "input_text",
                    "text": "Query:\nHow is the security category expressed and why is it important?\n\nRetrieved Documents:\n2. What is security categorization and why is it important?\nAnswer: Security categorization provides a structured way to determine the criticality of the information being processed, stored, and transmitted by a system. The purpose of the Categorize step is to inform organizational risk management processes and tasks by determining the adverse impact of the loss of confidentiality, integrity, and availability of organizational systems and information to the organization. The categorization determination results in the security category for the system, which is based on the potential adverse impact (worst case) to an organization should events occur that jeopardize the information and systems needed by the organization to accomplish its assigned mission, protect its assets and individuals, fulfill its legal responsibilities, and maintain its day- to-day functions. Before a security categorization decision can be made, the identification of the types of information that are or will be processed, stored, and transmitted by the system needs to be performed in the Prepare step (Task P-12, Information Types). Similarly, in addition to identifying the information types, each stage in the information life cycle for each type identified also needs to be identified and understood. This is also addressed in the Prepare step (Task P-13, Information Life Cycle).\nThe information owner or system owner identifies the types of information processed, stored, and transmitted by the system as part of Prepare step Task P-12 and assigns a security impact value (low, moderate, high) for the security objectives of confidentiality, integrity, or availability to each information type as part of Categorize step Task C-2. The high watermark concept is used to determine the security impact level of the system for the express purpose of prioritizing information security efforts among systems and selecting an initial set of controls from one of the three control baselines in NIST SP 800-53B [SP 800-53B]. According to the Federal Information Processing Standard (FIPS) Publication 199, Standards for Security Categorization for Federal Information and Information Systems [FIPS 199], security categorization promotes effective management and oversight of information security programs, including the coordination of information security efforts across the Federal Government, and reporting on the adequacy and effectiveness of information security policies, procedures, and practices. [Back to Table of Contents]\n\n12. How is the security category expressed?\nAnswer: The generalized format for expressing the security category, SC, of an information type is:\nSC information type {(confidentiality, impact), (integrity, impact), (availability, impact)}, =\nwhere the acceptable values for potential impact are low, moderate, high, or not applicable. The potential impact value of not applicable only applies to the security objective of confidentiality. For example, a security category for an information type that processes routine administrative information (non-PII) can be denoted as:\nSC administrative information = {(confidentiality, low), (integrity, low), (availability, low)}.\nThe generalized format for expressing the security category, SC, of a system is similar:\nSC = {(confidentiality, impact), (integrity, impact), (availability, impact)}, system\nwhere the acceptable values for potential impact are low, moderate, or high. The potential impact values assigned to the respective security objective (confidentiality, integrity, and availability) are the highest values (i.e., high water mark) from among those security categories that have been determined for each type of information resident on the system. The value of not applicable cannot be assigned to any security objective in the context of establishing a security category for a system. For example, a system that processes some information with a potential impact from a loss of confidentiality at moderate, some information with a potential impact from a loss of integrity at moderate, and all the information with a potential impact from a loss of availability at low, may have a security category expressed as:\nSC = {(confidentiality, moderate), (integrity, moderate), (availability, low)} [Back to Table of Contents] system\n\n4. Who is responsible for categorizing each system?\nAnswer: Ultimately, the information owner/system owner or an individual designated by the owner is responsible for categorizing a system. The information owner/system owner identifies all the information types stored in, processed by, or transmitted by the system as part of Prepare step Task P-12 and then determines the security category for the system by identifying the highest value (i.e., high water mark) for each security objective (confidentiality, integrity, and availability) and for each type of information resident on the system as part of Categorize step Task C-2. Subject matter experts may also be tapped by the information owner/system owner to assist with the system security categorization efforts. For systems that process personally identifiable information, the senior agency official for privacy reviews and approves the security categorization results and decision prior to the authorizing official's review.\nWhile the primary responsibility for categorization belongs to information owner/system owner, security categorizations are conducted as an organization-wide activity with the involvement of senior leadership (e.g., risk executive [function]) and system staff\n(e.g., system security officer and system privacy officer when PII is being processed). The authorizing official or designated representative reviews the categorization results and decisions from other organizational systems and then collaborates with senior leaders to ensure that the categorization decision for the system is consistent with the organizational risk management strategy and satisfies requirements for high-value assets. Senior leadership participation in the security categorization process is essential so that the Risk Management Framework can be carried out in an effective and consistent manner throughout the organization. The authorizing official or designated representative reviews the categorization results and decision from an organization-wide perspective, including how the decision aligns with categorization decisions for all other organizational systems. Back to Table of Contents]\n\n5. What is the role of privacy in the categorization process?\nAnswer: Privacy programs are responsible for managing the risks to individuals associated with the processing of personally identifiable information (PII) and for ensuring compliance with applicable privacy requirements. When a system processes PII, the information security program and the privacy program have a shared responsibility for managing the security risks for the PII in the system. Informed by the privacy risk assessment conducted under the Prepare step (Task P-14, Risk Assessment - System), the privacy program and the security program collaborate on determining the security category and overall security impact level for the system. The senior agency official for privacy reviews and approves the security categorization results and decision prior to the authorizing official's review."
                }
                ]
                },
                {
                "role": "user",
                "content": [
                {
                    "type": "input_text",
                    "text": user_message
                }
                ]
                }
            ],
            text={
                "format": {
                "type": "json_object"
                }
            },
            reasoning={
                "effort": "medium"
            }
        )

        relevance_check_dict = json.loads(response.output_text)
        if(len(relevance_check_dict["relevant"]) == 0):
            return "There is no relevant information available for the given question."
        relevant_docs = relevance_check_dict["relevant"]
        return relevant_docs    
    except Exception as e:
        return "There was an error with the Open AI API. Please try again."

