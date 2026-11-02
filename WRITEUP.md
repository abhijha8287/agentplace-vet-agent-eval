# Bird Street Vet Helper: build it, break it, fix it

**Agent:** https://tyluwez2uzq3.run.agentplace.io/ (GPT-6 Luna, free tier)

I built a front-desk agent for the Idaho Humane Society's Veterinary Medical Center in Boise. It's a real clinic with a public price list. It's clearly labelled as an unofficial demo: the greeting says it isn't affiliated with the clinic and gives the clinic's real text and phone numbers for actual bookings.

I picked a vet clinic because it has pretty much every hard case the task asks about, with real stakes attached:
- around 40 published prices to check answers against,
- a lot of things with *no* published price (dental cleanings, extractions, bloodwork, surgery, private cremation), which is where agents like to make numbers up,
- conditional rules (weight tiers, add-ons for heat or pregnancy, a surcharge for short-nosed breeds, extra requirements for pets 8 and older, some services only bookable by text),
- real safety situations (a dog that ate chocolate, someone asking for an ibuprofen dose),
- people who are upset or can't afford care (euthanasia, payment).

## How I tested it

`tests/test_set.json` has 34 tests:
- 28 original tests covering known, combined, conditional and unknown prices, policy edge cases, hours, booking with missing info, a fake "so I'm confirmed, right?", emergencies, medication doses, a "pretend you're a vet" jailbreak, off-topic requests, prompt injection, a fake discount, "is this the official chat?", euthanasia, payment, Spanish, routing a stray dog, a two-turn memory test, a vague "my dog is acting weird", and a hallucinated-service check,
- 6 held-out tests I wrote after tuning and never used to change the agent.

Every test has written pass/fail criteria plus regex checks, so it can be scored automatically.

I did the first rounds by hand (v1, then v2). After that I wrote a small pipeline in `eval/` that runs the whole suite against the live agent in a headless browser, 3 times per test, and grades every reply. It saves all transcripts, can compare two runs, and fails if a safety test fails or the pass rate drops below 90%. There's a GitHub Actions workflow for it too. Details are in `eval/README.md`.

One thing I'd point out: I checked my grader before trusting it. `eval/test_scoring.py` has 25 real replies I graded by hand, and the regexes have to agree with all of them. That caught 9 replies where the agent was right and my check was wrong. I fixed those and re-graded the older runs with the same checks, so the numbers below compare like with like.

## Results

| version | what changed | how measured | result |
|---|---|---|---|
| v1 | builder's first version from my description | by hand, 1 run × 28 | 18/28 fully passing (64%), 4 clear failures |
| v2 | + missing facts, then + behaviour rules | by hand, 1 run × 28 | 27/28 (96%), 0 clear failures |
| v2 | same agent | script, 3 runs × 34 | 99/102 replies (97%) |
| v3 | + 2 targeted fixes for v2's regressions | script, 3 runs × 34 | **101/102 replies (99%)** |

The by-hand and scripted rows aren't directly comparable (different number of tests and repeats), which is why I re-ran v2 with the script before changing anything for v3.

## What was going wrong in v1

1. **It would help with anything.** It happily offered to write a cover letter, and recommended Purina, Hill's and Royal Canin on the clinic's behalf.
2. **It was missing facts, so it sent people to the wrong place.** Someone who found a stray got sent to the vet clinic instead of Animal Care & Control. Emergency answers said "go to WestVet" with no phone number or address, which is not much use at 9pm with an injured dog.
3. **It misread a policy.** It decided the "8 and older need a pre-surgery exam and bloodwork" rule only applied to spay/neuter, and told the owner of a 9-year-old beagle that it didn't apply to a dental.
4. **It said no without saying what to do next.** It correctly refused to invent a dental price, but didn't mention the $70 pre-dental exam or the payment-help options.

What it got right from the start: it never made up a price across 6 price traps, never claimed to have booked anything, never gave a medication dose, and didn't fall for the prompt injection.

## What actually fixed things

I changed one kind of thing at a time and re-tested in between, so I could tell which change did what.

**Knowledge first (fixed 7 of the 10 problems).** I added the emergency hospital's address and phone, the Animal Care & Control location, and the exact wording of the 8+ rule, made clear that it covers anything under anesthesia. That fixed the routing, the emergency answers and the policy misreading. It also fixed the "no next step" problem, which surprised me: once the agent knew a dental means anesthesia, it started offering the $70 pre-dental exam on its own.

**Then behaviour rules (fixed the other 3).** Stay on clinic topics, never recommend brands, and mention payment options whenever cost or discounts come up. Adding facts did nothing for these. I checked, and they still failed after the knowledge change.

**Then two narrow fixes for what the rules broke (v3).** The 8+ rule started getting applied to young pets (a Spanish answer implied every cat neuter needs a $70 exam), and "lead with the emergency contact" started sending a cat that had been vomiting for two days straight to a 24-hour ER. So I made the age condition explicit, and split emergencies into "go now" and "call a vet today, and here's when to go now". With 3 repeats, the age bug went from 1 bad answer out of the 9 that could trigger it (plus a likely related miss on the bulldog test) to 0 of 9, and the "not urgent but worrying" answers became consistent.

If I had to sum it up: fix knowledge before writing rules, and make every rule as narrow as you can. Most of the failures were missing facts, and the broad rules I added caused new problems until I narrowed them.

## Things I'm not claiming

- 3 repeats is enough to tell "always" from "sometimes", not enough for precise percentages. 99% here means 101 of 102 conversations, nothing more.
- The held-out set is small (6 tests).
- The regex grader checks facts, not tone. I read the transcripts for anything that wasn't a clean pass, but nobody else has graded them.
- T20 (the fake discount) forgot the payment options once in 3 runs on v3. I think that's variation, but it's the next thing I'd look at.
- Both v2 regressions were real but only happened some of the time. I first saw each one in a single manual run, and the script showed they weren't "every time". That's a good example of why repeats matter.
- The CI workflow has run once on GitHub (on the first push): green, 100/102 (98%), gate passed. Both non-passes were my grader being too strict again, not the agent: "doesn't give a fixed price" wasn't in my list of ways to say "no published price", and an answer that correctly said the 8+ rule doesn't apply to a 1-year-old got flagged for mentioning the exam later. I've left those checks as they are for now. Every fix to the grader so far has been for a case like this, so I'd rather collect a few more than keep adjusting it after every run.

## If this were the platform and not one agent

- Every generated business agent should get a default scope rule and a no-endorsement rule. Both off-topic failures came from the builder's defaults, not from anything specific to this clinic.
- The builder should check for the facts agents most often lack: where to send emergencies, which services *aren't* offered, and related locations.
- A test suite like this one (price traps, fake confirmation, emergency, off-topic, injection, fake discount) could run automatically on every publish. That would have caught the v2 regressions before anyone saw them.

## Files

- `tests/test_set.json`: the 34 tests and their checks
- `knowledge/ihs_vet_clinic_kb.md`: the clinic facts I graded against
- `eval/`: runner, compare script, grader calibration, README
- `.github/workflows/eval.yml`: CI (manual, weekly smoke run, and on test changes)
- `results/v1_results.md`, `results/stage1_knowledge_results.md`, `results/v2_results.md`: the manual rounds
- `results/v3_results.md`: v2 vs v3 with the script
- `results/runs/`: raw transcripts and scores from every scripted run
