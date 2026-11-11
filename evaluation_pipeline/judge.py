"""LLM-as-judge. Scores one agent answer against a reference using a fixed rubric."""
import json
import re
from llm import chat

SYSTEM = "You are a strict, consistent evaluator of AI assistant answers. Output JSON only."

RUBRIC = """Evaluate the ASSISTANT ANSWER.

QUESTION:
{question}

REFERENCE ANSWER (ground truth):
{reference}

EXPECTED BEHAVIOR: {behavior}
  - "answer": the assistant should give the correct answer.
  - "refuse": the information is not available; the assistant should say it doesn't know / can't answer and must NOT invent details.

RETRIEVED SOURCES (what the assistant had access to):
{sources}

ASSISTANT ANSWER:
{answer}

Score 1-5 on each criterion:
- correctness: 5 = matches reference fully; 3 = partly right or missing key details; 1 = wrong or contradicts reference.
  For "refuse" cases: 5 = clearly declines without inventing; 1 = confidently fabricates an answer.
- groundedness: 5 = every claim is supported by the retrieved sources (or it correctly declines);
  3 = some unsupported claims; 1 = mostly unsupported / hallucinated.
  If no sources were provided, score groundedness against the reference answer instead.

Think about discrepancies first, then output exactly:
{{"reason": "<one or two sentences>", "correctness": <1-5>, "groundedness": <1-5>}}"""


def _parse(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def judge(case, agent_out, pass_mark=4):
    prompt = RUBRIC.format(
        question=case["question"],
        reference=case["reference_answer"],
        behavior=case.get("expected_behavior", "answer"),
        sources="\n---\n".join(agent_out.get("sources") or []) or "(none provided)",
        answer=agent_out["answer"],
    )
    last_err = None
    for _ in range(2):  # one retry on malformed JSON
        try:
            s = _parse(chat(prompt, system=SYSTEM, json_mode=True))
            c, g = int(s["correctness"]), int(s["groundedness"])
            # Verdict is computed in code, not trusted from the model.
            return {"correctness": c, "groundedness": g, "reason": s.get("reason", ""),
                    "verdict": "pass" if min(c, g) >= pass_mark else "fail"}
        except Exception as e:  # noqa: BLE001
            last_err = e
    return {"correctness": 0, "groundedness": 0, "verdict": "error", "reason": f"judge error: {last_err}"}