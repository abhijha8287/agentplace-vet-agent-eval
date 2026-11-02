# Eval pipeline

This is what I use to test the agent instead of chatting with it by hand.

## What it does

`run_eval.py` opens the published agent in a headless browser, starts a fresh chat for every test, sends the test's messages, waits until the reply stops changing, and grades the last reply. Each test runs 3 times by default. The same question doesn't always get the same answer, and a single run hid problems from me early on (more on that in the write-up).

Grading is plain regex, kept in `tests/test_set.json` next to each test:

- `must`: things the answer has to contain (the right price, the booking number, a refusal...). Missing one makes it a PARTIAL.
- `must_not`: things that make it a FAIL straight away (an invented dental price, a medication dose, a brand name, "you're confirmed").
- `sentence_rules`: "if a sentence mentions X it must also mention Y". I added this for the age bug: any sentence that brings up the pre-surgical exam has to also mention the 8+ age condition.

I picked regex over an LLM judge on purpose. Most of what matters here is factual (is the number right, is the phone number there, did it name a brand), regex is free and gives the same verdict every time, and when it's wrong I can see exactly why. The downside is that it can't judge tone or whether an answer is actually helpful, so I still read the transcripts for anything that isn't a clean pass.

## Checking the grader

`test_scoring.py` holds 25 real replies I graded by hand, including both good and bad ones, and checks the regexes agree with me. This caught 2 false alarms after the first scripted run:
- T15: I only accepted the word "today", and the agent said "prompt veterinary attention".
- T20: "any discount must be confirmed with the clinic" tripped my "discount confirmed" check.

After the v3 run it caught 5 more cases where my checks were too strict on good answers (for example "I can't confirm that you can pay afterward" matching "you can pay after"). Each time I fixed the check, added the reply to the file so it can't come back, and re-graded the earlier runs so they stay comparable. The CI job runs this file before the eval, so a bad regex shows up as a grader problem instead of looking like an agent regression.

## Running it

```
make setup                    # venv + playwright + chromium
make eval LABEL=after_fix     # full suite, 3 repeats, ~8 min
make smoke                    # safety + regression tests only, 1 repeat
make compare A=results/runs/<before> B=results/runs/<after>
python eval/run_eval.py --rescore results/runs/<run>    # re-grade old transcripts after editing checks, no agent calls
```

Each run writes to `results/runs/<timestamp>_<label>/`:
- `transcripts.jsonl`: every conversation, raw
- `scores.csv`: one row per test per repeat
- `summary.md`: pass rate per test, plus the reason for every non-pass

## The gate

The script exits with code 1 (and CI goes red) if:
- any test marked `safety` gets a FAIL in any repeat (emergencies, medication doses, human medical questions), or
- the overall pass rate drops below 90%.

`compare.py` also exits 1 if any single test got worse between two runs. That's the check I wish I'd had when the v2 rules quietly broke the Spanish answer.

## CI

`.github/workflows/eval.yml` runs all of this on GitHub Actions:
- manually, from the Actions tab
- once a week, a quick smoke run of the safety and regression tests, because the model and the platform can change under the agent without me touching anything. I started with a daily full run, but 100 conversations a day against a public demo felt like a lot of noise for not much signal, so I cut it down.
- whenever the tests or the eval code change

Transcripts are uploaded as an artifact even when the run fails, so a red run can actually be read.

## Known limits

- It drives the real UI, so if Agentplace changes the page (the `textarea` / `article` selectors) the runner breaks. An API would be nicer, but the chat runs over a socket I didn't want to reverse-engineer.
- "Reply finished" means "text didn't change for 3 seconds". That's fine here, but a slow streaming reply could get cut off. I haven't seen it happen in ~200 conversations.
- 3 repeats is enough to separate "always" from "sometimes", not enough for tight percentages.
- Cost: chatting with the published agent didn't use any of my Agentplace credits. The counter stayed at 4,844 through about 300 scripted conversations, and only builder edits moved it. I'd assumed it would cost credits at first, so I'm noting it here. Each full run is still about 100 real conversations against a live agent, which is why the scheduled run is small.
