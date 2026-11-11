"""Check how well the judge agrees with YOU.
1. Run run_eval.py. 2. Label 10-15 cases yourself in human_labels.jsonl:
   {"id": "case-001", "human_verdict": "pass"}   (pass | fail)
3. python calibrate.py   -> agreement %, Cohen's kappa, and every disagreement to review."""
import json
from pathlib import Path


def main():
    runs = sorted(Path("results").glob("run_*.json"))
    if not runs:
        raise SystemExit("No results found. Run run_eval.py first.")
    judged = {r["id"]: r for r in json.loads(runs[-1].read_text())["rows"]}
    human = {}
    for l in Path("human_labels.jsonl").read_text().splitlines():
        if l.strip():
            d = json.loads(l)
            human[d["id"]] = d["human_verdict"]

    ids = [i for i in human if i in judged]
    if not ids:
        raise SystemExit("No overlapping ids between human_labels.jsonl and the latest run.")
    h = [human[i] == "pass" for i in ids]
    j = [judged[i]["verdict"] == "pass" for i in ids]
    n = len(ids)
    agree = sum(a == b for a, b in zip(h, j)) / n
    # Cohen's kappa (binary)
    ph, pj = sum(h) / n, sum(j) / n
    pe = ph * pj + (1 - ph) * (1 - pj)
    kappa = (agree - pe) / (1 - pe) if pe < 1 else 1.0

    print(f"Compared {n} cases | agreement {agree:.0%} | kappa {kappa:.2f}  (>0.6 decent, >0.8 strong)")
    print("\nDisagreements (read these - they tell you how to fix the rubric):")
    for i in ids:
        if (human[i] == "pass") != (judged[i]["verdict"] == "pass"):
            r = judged[i]
            print(f"- {i}: human={human[i]} judge={r['verdict']} (c={r['correctness']}, g={r['groundedness']})")
            print(f"    Q: {r['question']}\n    A: {r['answer'][:200]}\n    judge said: {r['reason']}")


if __name__ == "__main__":
    main()