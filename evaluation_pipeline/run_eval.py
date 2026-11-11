"""Run the eval suite. Usage: python run_eval.py [--dataset dataset.jsonl] [--threshold 0.8]
Exits with code 1 if the overall pass rate is below the threshold (so CI can fail the build - Week 2)."""
import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from agent_under_test import answer
from judge import judge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="dataset.jsonl")
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    cases = [json.loads(l) for l in Path(args.dataset).read_text().splitlines() if l.strip()]
    rows = []
    for c in cases:
        t0 = time.time()
        try:
            out = answer(c["question"])
        except Exception as e:  # noqa: BLE001  agent crash is a failure, not a harness crash
            out = {"answer": f"AGENT ERROR: {e}", "sources": []}
        latency = round(time.time() - t0, 2)
        j = judge(c, out)
        rows.append({"id": c["id"], "category": c.get("category", "general"), "question": c["question"],
                     "answer": out["answer"], "latency_s": latency, **j})
        print(f"[{j['verdict'].upper():5}] {c['id']:<12} c={j['correctness']} g={j['groundedness']}  {latency}s")

    by_cat = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r["verdict"] == "pass")
    passed = sum(r["verdict"] == "pass" for r in rows)
    rate = passed / len(rows)

    print("\n=== Summary ===")
    print(f"Overall: {passed}/{len(rows)} = {rate:.0%} (threshold {args.threshold:.0%})")
    for cat, v in sorted(by_cat.items()):
        print(f"  {cat:<16} {sum(v)}/{len(v)}")

    Path(args.out).mkdir(exist_ok=True)
    path = Path(args.out) / f"run_{time.strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps({"pass_rate": rate, "rows": rows}, indent=2))
    print(f"Saved {path}")
    sys.exit(0 if rate >= args.threshold else 1)


if __name__ == "__main__":
    main()