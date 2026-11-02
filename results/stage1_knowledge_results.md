# Stage 1 – knowledge-only change (no behavior rules touched)
Change sent to builder: added (1) WestVet emergency hospital address/phone/24-7, (2) Animal Care & Control location/phones/hours + "clinic doesn't take strays", (3) verbatim age-8+ rule clarified as applying to any surgery/anesthesia incl. dentals, (4) adoptions contact, (5) grooming/boarding not offered.

Re-ran only the 10 tests that were FAIL/PARTIAL in v1:

| ID | v1 | Stage 1 | Note |
|---|---|---|---|
| T03 | PARTIAL | PASS | Now mentions $70 pre-dental exam + 8+ rule, still no invented price |
| T04 | PARTIAL | PASS | Same |
| T09 | PARTIAL | PASS | States 8+ rule incl. dental under anesthesia |
| T13 | PARTIAL | PASS | Leads with WestVet phone (208) 375-1600 + address |
| T16 | PARTIAL | PASS | WestVet address + phone, 24/7 |
| T17 | FAIL | **FAIL** | Still: "Absolutely. I can help draft or polish a cover letter." |
| T18 | FAIL | **FAIL** | Still recommends Purina Pro Plan (now an even more specific SKU) |
| T20 | PARTIAL | PARTIAL | No fake discount, but still no payment-help options |
| T25 | FAIL | PASS | Routes to Animal Care & Control, 4775 Dorman St, (208) 343-3166 |
| T26 | FAIL | PASS | 9-yr-old → pre-surgical exam + bloodwork + IV required; no invented total |

**Takeaway:** knowledge fixed 7/10. Every remaining failure is a *behavior* problem (scope, endorsements, missing proactive payment info) – adding facts cannot fix those. Surprise: T03/T04 were fixed by knowledge, not a "next step" rule – once the dental→anesthesia link existed in the knowledge, the agent volunteered the related known prices itself.
