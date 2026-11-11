# What metrics does Ragas offer?

Here is the current list from the docs. The RAG metrics are Context Precision, Context Recall, Context Entities Recall, Noise Sensitivity, Response Relevancy, Faithfulness, and Multimodal Faithfulness. There are also three NVIDIA-style metrics: Answer Accuracy, Context Relevance, and Response Groundedness. For agents and tool use, it has Topic Adherence, Tool Call Accuracy, Tool Call F1, and Agent Goal Accuracy. Natural-language comparison metrics include Factual Correctness, Semantic Similarity, BLEU, CHRF, ROUGE, String Presence, and Exact Match. You can also write your own metrics, such as the AspectCritic and DiscreteMetric examples I showed. 
# List of available metrics
 +2

Here is what the main ones check, and which of your behaviours each maps to:

Metric	| What it checks	| Needs	| Your behaviour
Faithfulness	| Are the response’s claims supported by the retrieved contexts?	| response, contexts	| Groundedness, hallucination
Response Relevancy	| Does the response address the question?	| question, response, contexts (+ embeddings)	| Off-topic answers
Context Precision	| Are the relevant chunks ranked near the top?	| contexts, reference	| Retrieval quality
Context Recall	| Is everything in the reference answer found in the retrieved contexts?	| contexts, reference	| Missing retrieval
Context Entities Recall	| Are the key names, dates, and numbers from the reference in the contexts?	| contexts, reference	| Fact-heavy docs like budgets and dates
Noise Sensitivity	| Does irrelevant retrieved text lead to wrong answers? |	all four	| Near-duplicate or stale files
Factual Correctness / Answer Accuracy	| Does the response match the reference?	| response, reference	| Correctness
Tool Call Accuracy / F1	| Did the agent call the expected tools with the expected arguments?	| message trace, reference tool calls	| Tool selection
Agent Goal Accuracy	| Did the agent achieve what the user wanted?	| message trace, reference	| Multi-step tasks
Topic Adherence	| Does the agent stay on topic?	| message trace	| Out-of-scope requests
AspectCritic / DiscreteMetric	| Anything you define in a sentence or two	| depends on your definition	| Abstention, refusal, permissions, injection

Some behaviours have no ready-made metric. Abstention (“says it doesn’t know”), permission refusals, and prompt-injection resistance all need a custom AspectCritic, a deterministic code check, or both. For injection and leak cases, prefer the code check, as with the forbidden share_item call.