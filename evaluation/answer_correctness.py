"""
The module comprises of the answer correctness evaluation function
"""

import os
import csv
import langchain
from dotenv import load_dotenv, find_dotenv
from deepeval import evaluate
from deepeval.models import GPTModel
from deepeval.test_case import LLMTestCase, SingleTurnParams, LLMTestCaseParams
from deepeval.metrics import GEval

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
gpt_model = GPTModel(model="gpt-5", temperature=0)


def answer_correctness_eval()-> float:
    """
    Evaluates the generated answers using DeepEval's Custom GEval

    Returns
    -------
    str
        The answer correctness aggregated score
        
    """


    correctness_metric = GEval(
    name="Correctness",
    evaluation_steps=[
        "The 'actual output' must be in the same professional language and tone as the 'expected output'.",
        "The factual information in the 'actual output' must not contradict any factual information in the 'expected output'.",
        "None of the factual information from the 'expected output' must be omitted in the 'actual output'.",
        "The order in which the information exists in paragraphs in the 'actual output' must be identical in the 'expected output'.",
        "The structure of lists in the 'actual output' must be the same in the 'expected output'.",
        "The mathematical equations in the 'actual output' must be the same as in the 'expected output'.",
        "The in-text citations in the 'actual output' must be identical to the in-text citations in the 'expected output'."
        "It is acceptable for the phrasing of the sentences to not be identical but the factual information, terms, terminologies, headings, and names are required to be identical."   
    ],
    evaluation_params=[
        SingleTurnParams.ACTUAL_OUTPUT, 
        SingleTurnParams.EXPECTED_OUTPUT
    ],
    model=gpt_model,
    threshold=0.9,
    strict_mode=False,
    verbose_mode=True
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
            test_case = LLMTestCase(
                input=question,
                actual_output=final_answer,
                expected_output=ground_truth
            )
            test_cases.append(test_case)
    
    try:
        evaluation = evaluate(test_cases=test_cases, metrics=[correctness_metric])
        results = evaluation.test_results
    except:
        return "There was an error in DeepEval. Please check your model API key."
    scores = []
    for res in results:
        for metric_data in res.metrics_data:
            if metric_data.name == correctness_metric.__name__:
                scores.append(metric_data.score)
    if scores:
        aggregate_score = sum(scores) / len(scores)
        return aggregate_score
    else:
        return "No scores found"


if __name__ == "__main__":
    score = answer_correctness_eval()
    print("Score: ", score)
