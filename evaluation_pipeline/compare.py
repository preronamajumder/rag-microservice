"""Regression gate. Compares the latest results/run_*.json to baseline.json.

  python compare.py --floor 0.8 --max-drop 0.05          # gate used in CI
  python compare.py --update-baseline                    # accept current run as the new baseline

Exit 1 if:  pass rate < --floor   OR   pass rate fell more than --max-drop vs baseline
            OR (optional) more than --max-case-regressions cases flipped pass -> fail.
Why both an absolute floor and a relative drop: the floor stops slow decay, the drop catches a
sudden regression even when you are still above the floor.
"""
import argparse
import json
import os
import sys
from pathlib import Path


def latest_run():
    runs = sorted(Path("results").glob("run_*.json"))
    if not runs:
        sys.exit("No results found. Run run_eval.py first.")
    return json.loads(runs[-1].read_text())


def slim(run):
    return {"pass_rate": run["pass_rate"],
            "cases": {r["id"]: {"verdict": r["verdict"], "category": r["category"]} for r in run["rows"]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", type=float, default=0.8)
    ap.add_argument("--max-drop", type=float, default=0.05)
    ap.add_argument("--max-case-regressions", type=int, default=-1, help="-1 = report only")
    ap.add_argument("--baseline", default="baseline.json")
    ap.add_argument("--update-baseline", action="store_true")
    a = ap.parse_args()

    cur = slim(latest_run())
    if a.update_baseline:
        Path(a.baseline).write_text(json.dumps(cur, indent=2))
        print(f"Baseline updated: pass rate {cur['pass_rate']:.0%} over {len(cur['cases'])} cases")
        return

    lines, failures = [], []
    lines.append(f"## LLM eval result\n\nPass rate: **{cur['pass_rate']:.0%}** (floor {a.floor:.0%})")
    if cur["pass_rate"] < a.floor:
        failures.append(f"pass rate {cur['pass_rate']:.0%} is below floor {a.floor:.0%}")

    bp = Path(a.baseline)
    if bp.exists():
        base = json.loads(bp.read_text())
        drop = base["pass_rate"] - cur["pass_rate"]
        lines.append(f"Baseline: {base['pass_rate']:.0%}  |  change: {-drop:+.0%} (max allowed drop {a.max_drop:.0%})")
        if drop > a.max_drop:
            failures.append(f"pass rate dropped {drop:.0%} vs baseline (max {a.max_drop:.0%})")
        regressed = [i for i, c in cur["cases"].items()
                     if base["cases"].get(i, {}).get("verdict") == "pass" and c["verdict"] != "pass"]
        fixed = [i for i, c in cur["cases"].items()
                 if base["cases"].get(i, {}).get("verdict") != "pass" and c["verdict"] == "pass" and i in base["cases"]]
        new = [i for i in cur["cases"] if i not in base["cases"]]
        if regressed:
            lines.append("\n**Regressed (pass -> fail):** " + ", ".join(regressed))
        if fixed:
            lines.append("**Fixed (fail -> pass):** " + ", ".join(fixed))
        if new:
            lines.append("**New cases (no baseline yet):** " + ", ".join(new))
        if 0 <= a.max_case_regressions < len(regressed):
            failures.append(f"{len(regressed)} cases regressed (max {a.max_case_regressions})")
    else:
        lines.append("_No baseline.json yet - only the floor is enforced. Run with --update-baseline to create one._")

    lines.append("\n**" + ("FAILED: " + "; ".join(failures) if failures else "PASSED") + "**")
    report = "\n".join(lines)
    print(report)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).open("a").write(report + "\n")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()