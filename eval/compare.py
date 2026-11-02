"""
Compare two eval runs test by test.

  python eval/compare.py results/runs/<before> results/runs/<after>

Prints a markdown table and flags anything that got worse, so a change that
fixes one thing and quietly breaks another doesn't slip through.
"""

import csv
import sys
from pathlib import Path


def load(run_dir):
    rates = {}
    with open(Path(run_dir) / "scores.csv") as f:
        for row in csv.DictReader(f):
            p, n = rates.get(row["test_id"], (0, 0))
            rates[row["test_id"]] = (p + (row["verdict"] == "PASS"), n + 1)
    return rates


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    before, after = load(sys.argv[1]), load(sys.argv[2])
    ids = sorted(set(before) | set(after))

    print(f"| test | before | after | |\n|---|---|---|---|")
    worse, better = [], []
    tb = ta = nb = na = 0
    for i in ids:
        b, a = before.get(i), after.get(i)
        bs = f"{b[0]}/{b[1]}" if b else "-"
        as_ = f"{a[0]}/{a[1]}" if a else "-"
        note = ""
        if b and a:
            rb, ra = b[0] / b[1], a[0] / a[1]
            if ra < rb:
                note, _ = "worse", worse.append(i)
            elif ra > rb:
                note, _ = "better", better.append(i)
        if b:
            tb, nb = tb + b[0], nb + b[1]
        if a:
            ta, na = ta + a[0], na + a[1]
        print(f"| {i} | {bs} | {as_} | {note} |")

    print(f"\nbefore: {tb}/{nb} ({tb / nb:.0%})  after: {ta}/{na} ({ta / na:.0%})" if nb and na else "")
    print(f"better: {', '.join(better) or 'none'}")
    print(f"worse:  {', '.join(worse) or 'none'}")
    sys.exit(1 if worse else 0)


if __name__ == "__main__":
    main()
