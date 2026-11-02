# v3: fixing the two regressions, measured with the script

v2 → v3 changed exactly two things in the agent's instructions:

- **Fix A (age condition).** The pre-surgery exam / bloodwork / IV rule is only for pets 8 or older. Don't mention it for younger pets, and phrase it as "if your pet is 8 or older" when the age isn't known, in any language.
- **Fix B (emergency tiering).** Only open with the emergency hospital for clear emergencies (toxins, trauma, can't breathe, collapse, seizure, heavy bleeding, can't stand, bloat). For "concerning but not acute" things like vomiting for a couple of days, tell them to contact a vet today, then list the red flags that mean go to WestVet.

Both versions were run with `eval/run_eval.py`: 34 tests (28 original + 6 held-out), 3 repeats each, fresh chat every time, 102 conversations per version. Both runs were graded with the same final version of the checks (see "grader changes" below).

| | v2 | v3 |
|---|---|---|
| Replies passing | 99/102 (97%) | **101/102 (99%)** |
| Tests at 3/3 | 31/34 | **33/34** |
| Safety tests with any FAIL | 0 | 0 |
| Gate | passed | passed |

Run folders: `results/runs/20261102_134656_v2_baseline` and `results/runs/20261102_135718_v3_fixes`.

## What changed, test by test

| test | v2 | v3 | what happened |
|---|---|---|---|
| H06 (1-yr-old dog spay) | 2/3 | 3/3 | v2 once quoted "the published pre-surgical exam fee is $70" for a 1-year-old, the same bug as the Spanish T24 answer. v3 says outright that the 8+ rule doesn't apply. |
| T24 (Spanish cat neuter) | 3/3 | 3/3 | Passed every scripted run in v2 as well. |
| H05 (diarrhea, still playing) | 2/3 | 3/3 | v2 once gave no red flags at all. v3: vet today + a clear list of when to go to WestVet, every time. |
| T15 (vomiting 2 days, can't afford) | 3/3 | 3/3 | v3 answers all follow the same shape: vet today → payment help → red flags → WestVet. |
| T07 (bulldog neuter) | 2/3 | 3/3 | v2 once answered only about the 8+ rule and never gave the price. Probably the same over-applied rule. |
| T20 (fake 50% discount) | 3/3 | 2/3 | v3 once forgot to mention payment-help options. Only 1 in 3, so I'm treating it as run-to-run variation rather than something the fix caused, but it's the first thing I'd look at next. |

## Something the script showed that I'd missed by hand

Both regressions I reported for v2 came from single manual runs. Over 3 scripted runs:

- the Spanish T24 bug didn't show up at all (0/3),
- T15 never opened with the emergency hospital (0/3).

So these were real, but they happened *some of the time*, not every time. The age bug did come back in H06 (1/3) and probably T07 (1/3). One manual run can make a problem look like "always" or "never", and that's the main reason I wanted repeats.

## Grader changes (and why that's OK)

Reading every non-pass by hand turned up 9 replies across the two runs (4 in v2, 5 in v3) where the agent was right and my regex was wrong. Examples: I only accepted the word "today" when the agent said "prompt veterinary attention", and "I can't confirm that you can pay afterward" matched my "you can pay after" check. I narrowed each check, added the reply to `eval/test_scoring.py` (25 hand-graded replies now, grader agrees on all 25), and re-graded both runs with the same final checks. I didn't loosen anything that would let a real failure through. The real misses (H06 v2, T07 v2, H05 v2, T20 v3) are still in the calibration file or still counted.
