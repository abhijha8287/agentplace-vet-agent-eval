"""
Runs the test set against the published Agentplace agent and scores every reply.

How it works:
  - every test gets a brand new browser context (so no chat history leaks between tests)
  - we wait for the greeting, type each turn, and wait until the reply stops changing
  - the last reply is scored with the regex checks in tests/test_set.json
  - each test is repeated --repeats times, because the same question can get a
    different answer on a different run

Usage:
  python eval/run_eval.py                       # all tests, 3 repeats
  python eval/run_eval.py --only T15 T24 H05    # a few tests
  python eval/run_eval.py --rescore results/runs/<run_dir>   # re-grade saved transcripts, no agent calls

Output goes to results/runs/<timestamp>_<label>/ :
  transcripts.jsonl  every conversation, raw
  scores.csv         one row per (test, repeat)
  summary.md         pass rates per test + overall
Exit code is 1 if the gate fails (see --min-pass-rate and safety tests).
"""

import argparse
import asyncio
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_URL = "https://tyluwez2uzq3.run.agentplace.io/"
FLAGS = re.IGNORECASE | re.MULTILINE


# ---------- scoring ----------

def split_sentences(text):
    # good enough for this: split on . ! ? and line breaks, but not on "$1.50" style decimals
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z¿¡(])|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def score_reply(test, reply):
    """Returns (verdict, list of reasons). verdict is PASS / PARTIAL / FAIL / ERROR."""
    if reply is None:
        return "ERROR", ["no reply captured"]
    reasons = []
    hard_fail = False

    for pat in test.get("must_not", []):
        m = re.search(pat, reply, FLAGS)
        if m:
            hard_fail = True
            reasons.append(f"must_not hit: /{pat}/ -> '{m.group(0)[:60]}'")

    for rule in test.get("sentence_rules", []):
        for s in split_sentences(reply):
            if re.search(rule["if"], s, FLAGS) and not re.search(rule["then"], s, FLAGS):
                hard_fail = True
                reasons.append(f"sentence rule broken (/{rule['if']}/ without /{rule['then']}/): '{s[:90]}'")

    missing = [pat for pat in test.get("must", []) if not re.search(pat, reply, FLAGS)]
    for pat in missing:
        reasons.append(f"missing: /{pat}/")

    if hard_fail:
        return "FAIL", reasons
    if missing:
        return "PARTIAL", reasons
    return "PASS", reasons


# ---------- talking to the agent ----------

async def article_text(page):
    return await page.evaluate(
        "() => { const a = document.querySelectorAll('article');"
        " return a.length ? a[a.length - 1].innerText.trim() : ''; }"
    )


async def wait_until_stable(page, previous, timeout=90, settle=3.0):
    """Wait for the visible reply to differ from `previous` and then stop changing for `settle` seconds."""
    start = time.time()
    last, last_change = None, time.time()
    while time.time() - start < timeout:
        txt = await article_text(page)
        if txt and txt != previous:
            if txt != last:
                last, last_change = txt, time.time()
            elif time.time() - last_change >= settle:
                return txt
        await asyncio.sleep(0.5)
    return last  # may be partial or None; scorer handles None


async def run_conversation(browser, url, turns):
    ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
    page = await ctx.new_page()
    replies = []
    t0 = time.time()
    try:
        await page.goto(url, wait_until="domcontentloaded")
        greeting = await wait_until_stable(page, previous="", timeout=60)
        box = page.locator("textarea").first
        prev = greeting or ""
        for turn in turns:
            await box.fill(turn)
            await box.press("Enter")
            reply = await wait_until_stable(page, previous=prev)
            replies.append(reply)
            prev = reply or prev
    except Exception as e:  # keep going, record the error
        replies.append(None)
        return {"greeting": None, "replies": replies, "error": repr(e), "seconds": round(time.time() - t0, 1)}
    finally:
        await ctx.close()
    return {"greeting": greeting, "replies": replies, "error": None, "seconds": round(time.time() - t0, 1)}


# ---------- main ----------

def load_tests(only=None, heldout=None):
    data = json.loads((ROOT / "tests" / "test_set.json").read_text())
    tests = data["tests"]
    if only:
        tests = [t for t in tests if t["id"] in only]
    if heldout == "exclude":
        tests = [t for t in tests if not t.get("heldout")]
    elif heldout == "only":
        tests = [t for t in tests if t.get("heldout")]
    return tests


def summarize(tests, rows, out_dir, label, url, min_pass_rate):
    by_test = {}
    for r in rows:
        by_test.setdefault(r["test_id"], []).append(r["verdict"])

    lines = [f"# Eval run: {label}", "",
             f"- agent: {url}",
             f"- time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             f"- tests: {len(by_test)}, repeats: {max(len(v) for v in by_test.values()) if by_test else 0}",
             "", "| test | category | pass rate | verdicts |", "|---|---|---|---|"]
    total, passes, gate_problems = 0, 0, []
    for t in tests:
        v = by_test.get(t["id"], [])
        if not v:
            continue
        p = v.count("PASS")
        total += len(v)
        passes += p
        mark = "" if p == len(v) else " ⚠"
        lines.append(f"| {t['id']} | {t['category']} | {p}/{len(v)}{mark} | {' '.join(v)} |")
        if t.get("safety") and "FAIL" in v:
            gate_problems.append(f"safety test {t['id']} had a FAIL")

    rate = passes / total if total else 0
    if rate < min_pass_rate:
        gate_problems.append(f"overall pass rate {rate:.0%} is below {min_pass_rate:.0%}")
    errors = sum(1 for r in rows if r["verdict"] == "ERROR")

    lines += ["", f"**Overall: {passes}/{total} replies passed ({rate:.0%}).** Errors: {errors}.", ""]
    lines.append("Gate: " + ("PASSED" if not gate_problems else "FAILED - " + "; ".join(gate_problems)))

    # list the reasons for anything that wasn't a pass, so you can go straight to the transcript
    bad = [r for r in rows if r["verdict"] != "PASS"]
    if bad:
        lines += ["", "## Non-passing replies", ""]
        for r in bad:
            lines.append(f"- **{r['test_id']} #{r['repeat']} {r['verdict']}**: {r['reasons']}")

    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:len(tests) + 8]))
    print(f"\nOverall {passes}/{total} ({rate:.0%}) | gate {'PASSED' if not gate_problems else 'FAILED'}")
    return not gate_problems


def write_scores(out_dir, rows):
    with open(out_dir / "scores.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["test_id", "repeat", "verdict", "seconds", "reasons"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})


async def run(args):
    from playwright.async_api import async_playwright

    tests = load_tests(args.only, args.heldout)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "results" / "runs" / f"{stamp}_{args.label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = [(t, k) for k in range(1, args.repeats + 1) for t in tests]
    sem = asyncio.Semaphore(args.concurrency)
    rows, transcript_f = [], open(out_dir / "transcripts.jsonl", "w")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.headed)

        async def one(t, k):
            async with sem:
                convo = await run_conversation(browser, args.url, t["turns"])
                # one retry if the page itself broke (not if the agent just answered badly)
                if convo["error"] or convo["replies"][-1] is None:
                    convo = await run_conversation(browser, args.url, t["turns"])
                last = convo["replies"][-1] if convo["replies"] else None
                verdict, reasons = score_reply(t, last)
                rec = {"test_id": t["id"], "repeat": k, "turns": t["turns"], **convo,
                       "verdict": verdict, "reasons": reasons}
                transcript_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                transcript_f.flush()
                rows.append({"test_id": t["id"], "repeat": k, "verdict": verdict,
                             "seconds": convo["seconds"], "reasons": " | ".join(reasons)})
                print(f"  {t['id']} #{k}: {verdict}  ({convo['seconds']}s)", flush=True)

        await asyncio.gather(*(one(t, k) for t, k in jobs))
        await browser.close()

    transcript_f.close()
    rows.sort(key=lambda r: (r["test_id"], r["repeat"]))
    write_scores(out_dir, rows)
    ok = summarize(tests, rows, out_dir, args.label, args.url, args.min_pass_rate)
    print(f"\nSaved to {out_dir}")
    return ok


def rescore(run_dir, args):
    """Re-grade an existing run with the current checks. Handy after fixing a regex."""
    run_dir = Path(run_dir)
    tests = {t["id"]: t for t in load_tests()}
    rows = []
    for line in (run_dir / "transcripts.jsonl").read_text().splitlines():
        rec = json.loads(line)
        t = tests.get(rec["test_id"])
        if not t:
            continue
        last = rec["replies"][-1] if rec["replies"] else None
        verdict, reasons = score_reply(t, last)
        rows.append({"test_id": rec["test_id"], "repeat": rec["repeat"], "verdict": verdict,
                     "seconds": rec.get("seconds"), "reasons": " | ".join(reasons)})
    rows.sort(key=lambda r: (r["test_id"], r["repeat"]))
    write_scores(run_dir, rows)
    present = [t for t in load_tests() if any(r["test_id"] == t["id"] for r in rows)]
    return summarize(present, rows, run_dir, run_dir.name + " (rescored)", args.url, args.min_pass_rate)


def main():
    ap = argparse.ArgumentParser(description="Eval runner for the Bird Street Vet Helper agent")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--only", nargs="*", help="test ids to run")
    ap.add_argument("--heldout", choices=["include", "exclude", "only"], default="include")
    ap.add_argument("--label", default="run")
    ap.add_argument("--min-pass-rate", type=float, default=0.90)
    ap.add_argument("--headed", action="store_true", help="show the browser")
    ap.add_argument("--rescore", help="path to an existing run folder")
    args = ap.parse_args()

    ok = rescore(args.rescore, args) if args.rescore else asyncio.run(run(args))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
