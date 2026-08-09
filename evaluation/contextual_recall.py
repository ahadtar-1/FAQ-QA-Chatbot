"""
The module comprises of the contextual recall evaluation function
"""

import os
import sys
import csv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import langchain
from dotenv import load_dotenv, find_dotenv
from deepeval import evaluate
from deepeval.models import GPTModel
from deepeval.test_case import LLMTestCase, SingleTurnParams, LLMTestCaseParams
from deepeval.metrics import ContextualRecallMetric
from services.retrieval_pipeline import retrieve_similar_docs 

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
gpt_model = GPTModel(model="gpt-5", temperature=0)


def contextual_recall_eval()-> float:
    """
    Evaluates the contextual recall using DeepEval's contextual recall metric

    Returns
    -------
    float
        The contextual recall aggregated score

    """

    
    contextual_recall_metric = ContextualRecallMetric(
    threshold=0.9,
    model="gpt-5",
    include_reason=True
    )

    ground_truths = []
    with open("ground_truths.csv", mode = "r", newline = "", encoding="utf-8") as gt_file:
        gt_reader = csv.reader(gt_file)
        next(gt_reader)
        for row in gt_reader:
            ground_truths.append(row[0])

    test_cases = []
    with open("final_generated_answers.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row, ground_truth in zip(reader, ground_truths):
            question = row["Question"]
            final_answer = row["Final Answer"]
            retrieved_text = retrieve_similar_docs(question)
            if(isinstance(retrieved_text, str)):
                if "OpenAIAPI" in retrieved_text:
                    return "We are unable to provide an answer at the moment. There was an error in the OpenAI API."
                if "OpenAI" in retrieved_text:
                    return "We are unable to provide an answer at the moment. OpenAI Communication issue. Please try again."
                if "Pinecone" in retrieved_text:
                    return "We are unable to provide an answer at the moment. There was an error in the Pinecone API."
                if "Pinecone-500" in retrieved_text:
                    return "We are unable to provide an answer at the moment. Pinecone communication issue. Please try again."
                if "Connection" in retrieved_text:
                    return "We are unable to provide an answer at the moment. Connection issue. Please try again."
                if "No similar docs." in retrieved_text:
                    test_case = LLMTestCase(
                    input=question,
                    actual_output=final_answer,
                    expected_output=ground_truth,
                    retrieval_context=[" "]
                    )
                    test_cases.append(test_case)
                    continue

            test_case = LLMTestCase(
                input=question,
                actual_output=final_answer,
                expected_output=ground_truth,
                retrieval_context=[retrieved_text[0]["content"]]
                )
            test_cases.append(test_case)
    
    try:
        evaluation = evaluate(test_cases=test_cases, metrics=[contextual_recall_metric])
        results = evaluation.test_results
    except:
        return "There was an error in DeepEval. Please check your model API key."
    scores = []
    for res in results:
        for metric_data in res.metrics_data:
            if metric_data.name == contextual_recall_metric.__name__:
                scores.append(metric_data.score)
    if scores:
        aggregate_score = sum(scores) / len(scores)
        return aggregate_score
    else:
        return "No scores found."


if __name__ == "__main__":
    score = contextual_recall_eval()
    print("Score: ", score)
