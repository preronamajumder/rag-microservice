import json
from ragas import SingleTurnSample, EvaluationDataset, evaluate
from ragas.metrics import Faithfulness, AspectCritic
from ragas.llms import LangchainLLMWrapper
from langchain_ollama import ChatOllama
from agent_under_test import answer

judge = LangchainLLMWrapper(ChatOllama(model="llama3.1:8b", temperature=0))

samples = []
for line in open("dataset.jsonl"):
    c = json.loads(line)
    out = answer(c["question"])
    samples.append(SingleTurnSample(
        user_input=c["question"], response=out["answer"],
        retrieved_contexts=out["sources"], reference=c["reference_answer"]))

metrics = [
    Faithfulness(llm=judge),   # groundedness: claims supported by sources?
    AspectCritic(name="abstains_when_unknown", llm=judge,
                 definition="Return true if the response admits it lacks the information instead of inventing an answer."),
]
result = evaluate(EvaluationDataset(samples=samples), metrics=metrics)
print(result.to_pandas())