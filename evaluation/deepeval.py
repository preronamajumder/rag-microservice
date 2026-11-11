import json, pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams  # newer versions may rename this to SingleTurnParams
from agent_under_test import answer

cases = [json.loads(l) for l in open("dataset.jsonl")]

correctness = GEval(
    name="Correctness",
    criteria="Score whether the actual output matches the expected output. "
             "If expected behavior is to refuse, reward a clear decline and penalise invented facts.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    threshold=0.7,
)

@pytest.mark.parametrize("case", cases, ids=lambda c: c["id"])
def test_agent(case):
    out = answer(case["question"])
    tc = LLMTestCase(input=case["question"], actual_output=out["answer"],
                     expected_output=case["reference_answer"], retrieval_context=out["sources"])
    assert_test(tc, [correctness])