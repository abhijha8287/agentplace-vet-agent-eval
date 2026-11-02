# Vet clinic agent on Agentplace

[![agent-eval](https://github.com/abhijha8287/agentplace-vet-agent-eval/actions/workflows/eval.yml/badge.svg)](https://github.com/abhijha8287/agentplace-vet-agent-eval/actions/workflows/eval.yml)

This is my test task for the AI Agent Builder role at Agentplace. I built a customer-facing agent for a real business on the free Luna model, tested it with a set of tricky conversations, fixed the things that broke, and measured it again.

**Try the agent:** https://tyluwez2uzq3.run.agentplace.io/

It's a front desk for the Idaho Humane Society's Veterinary Medical Center in Boise. Everything it knows comes from the clinic's public website and price list. It's an unofficial demo, not affiliated with the clinic, and it says so in its first message. It can't book anything; for real appointments it points people to the clinic's actual text and phone numbers.

## Where to start

If you only read one thing, read [WRITEUP.md](WRITEUP.md). It covers why I picked this business, what failed, what I changed, and which change fixed what.

After that:
- [tests/test_set.json](tests/test_set.json): the 34 test conversations, each with its pass/fail criteria
- [results/](results/): each round of testing, from the first manual pass to the scripted v2 vs v3 comparison
- [eval/README.md](eval/README.md): how the test runner and grading work, and their limits

## Results in short

| version | how it was tested | result |
|---|---|---|
| v1 (first build) | by hand, 28 tests, once each | 18/28 passing |
| v3 (current) | script, 34 tests, 3 times each | 101/102 replies passing |
| v3 on GitHub Actions | same, first CI run | 100/102, gate passed |

The biggest finding was that most of the failures were missing facts, not bad behaviour. Adding a handful of facts fixed 7 of the 10 problems. Rules were only needed for staying on topic, not recommending brands, and mentioning payment help. The first versions of those rules were too broad and broke two other answers, so v3 narrows them down.

## Running the tests yourself

You need Python 3.12+.

```
make setup                  # virtualenv, Playwright and Chromium
make eval LABEL=mine        # all 34 tests x 3, about 8 minutes
make smoke                  # just the safety and regression tests, once each
make compare A=results/runs/<old> B=results/runs/<new>
```

It talks to the published agent through a headless browser, the same way a visitor would. Results end up in `results/runs/<time>_<label>/`, with every transcript saved.

GitHub Actions runs the same thing when the tests or eval code change, once a week as a quick smoke check, or manually from the Actions tab. The run fails if any safety test fails or the pass rate drops below 90%.

## Layout

```
WRITEUP.md                   the report
knowledge/                   clinic facts I graded the agent against
tests/test_set.json          the test conversations and their checks
eval/run_eval.py             runs the tests and grades the replies
eval/compare.py              compares two runs, flags anything that got worse
eval/test_scoring.py         makes sure the grader agrees with my hand grading
results/                     write-ups for each round + raw runs
.github/workflows/eval.yml   CI
```

## A couple of honest notes

- The grading is regex-based. It's good at facts (right price, right phone number, no brand names) and can't judge tone, so I read the transcripts for anything that didn't pass cleanly. Most non-passes so far turned out to be my checks being too strict, not the agent being wrong. That's written up in the results.
- 3 runs per test tells you whether something happens always or only sometimes. It isn't enough for precise percentages.
- The clinic info was collected on 2 Nov 2026. If their prices change, the agent and the test answers will be out of date.
