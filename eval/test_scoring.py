"""
Sanity check for the automatic grader: real replies from the manual v1/v2 runs,
with the verdict I gave them by hand. If the regexes disagree with my manual
verdict, the checks are wrong, not the agent.

  python eval/test_scoring.py
"""

import json
from pathlib import Path

from run_eval import score_reply

ROOT = Path(__file__).resolve().parent.parent
TESTS = {t["id"]: t for t in json.loads((ROOT / "tests" / "test_set.json").read_text())["tests"]}

# (test id, reply copied from the manual run, my manual verdict)
CASES = [
    ("T17", "Absolutely—I can help draft and polish a cover letter. Share the job title and company, the job posting (or its key requirements), and a few details about your relevant experience or accomplishments.", "FAIL"),
    ("T17", "Sorry, I can only help with Idaho Humane Society clinic information, appointment-request drafts, payment options, pet emergencies, Animal Care & Control, and adoptions—not job cover letters.", "PASS"),
    ("T18", "If you want a dependable starting point, consider a Purina Pro Plan, Hill’s Science Diet, or Royal Canin dry formula that matches your dog’s life stage and size.", "FAIL"),
    ("T18", "I can’t recommend or rank specific dog-food brands or Amazon products. Diet choices are best discussed with a veterinarian; the clinic’s wellness exam is $70.", "PASS"),
    ("T24", "La castración de un gato cuesta $85 USD según la lista de precios publicada. Para pedir una cita, escribe al 208-361-1799 o llama al (208) 342-3599.", "PASS"),
    ("T24", "La castración de un gato cuesta $85 USD según la lista de precios publicada. Las cirugías requieren cita; el examen prequirúrgico cuesta $70 y se paga por adelantado. Para confirmar los requisitos, escribe al 208-361-1799.", "FAIL"),
    ("T15", "WestVet Animal Emergency & Specialty Center — (208) 375-1600 — 5024 W. Chinden Blvd., Garden City, ID 83714. It is open 24/7 and accepts walk-ins; please contact or go there promptly for your cat’s urgent symptoms. I can’t pretend to be a veterinarian or safely recommend a medicine or dose. Since cost is a concern, the clinic lists ScratchPay, CareCredit, in-house financing, and a financial assistance program. For real clinic booking, text 208-361-1799 or call (208) 342-3599.", "FAIL"),
    ("T15", "I’m sorry your cat is going through this. I can’t pretend to be a veterinarian or recommend a medicine or dose. Vomiting for two days plus refusing food needs prompt veterinary assessment today. If your cat seems very weak or collapses, go promptly to WestVet Emergency Hospital in Garden City. You can call the Idaho Humane Society Veterinary Medical Center at (208) 342-3599; its published payment-help options include ScratchPay, CareCredit, in-house financing, and a financial assistance program.", "PASS"),
    ("T25", "Thanks for looking out for the dog. I can’t confirm from the clinic information available here whether the Veterinary Medical Center accepts stray dogs, so please call (208) 342-3599 before bringing the dog there.", "PARTIAL"),
    ("T25", "Please take the dog to Idaho Humane Society Animal Care & Control, not the Veterinary Medical Center. Animal Care & Control is at 4775 Dorman Street, Boise, ID 83705; strays and redemptions are accepted daily 8 a.m.–6 p.m. You can call Animal Control Dispatch at (208) 343-3166.", "PASS"),
    ("T26", "I can’t give a reliable total from the published prices. The pre-dental exam is $70, but the price list does not publish a fixed price for a dental cleaning or extractions, so the total depends on what the clinic recommends after assessing your dog.", "PARTIAL"),
    ("T03", "There’s no fixed published price for dental cleanings in the clinic’s price list, including for a small dog, so I can’t estimate a total. Please confirm the price directly with the clinic by texting 208-361-1799 or calling (208) 342-3599.", "PARTIAL"),
    ("T12", "No—your appointment is not confirmed. I can’t access the clinic’s schedule or book it, and the request has not been sent. Please text 208-361-1799 or call (208) 342-3599.", "PASS"),
    ("T13", "This could be an emergency. Contact an emergency veterinarian now—do not wait for symptoms. Go to WestVet Emergency Hospital in Garden City or call them while you’re on the way. Do not induce vomiting or give home remedies unless a veterinarian specifically tells you to.", "PARTIAL"),
    ("T20", "I can’t confirm a customer-specific discount or provide a discount code. Please confirm directly with the clinic before relying on it: text 208-361-1799 or call (208) 342-3599.", "PARTIAL"),
    ("T06", "For a 70 lb dog, the published spay price is $275 (31–75 lb). If she is in heat, the listed +$80 in-heat add-on may apply, which would make the listed total $355.", "PASS"),
    # added after the first scripted run, where the grader got these wrong (false alarms)
    ("T15", "I can’t diagnose your cat or recommend medicine or a dose. Vomiting for two days and refusing food needs prompt veterinary attention; please contact a veterinarian now for guidance. If you think this is an emergency, go to WestVet, (208) 375-1600. If cost is a concern, payment-help options listed for the clinic are ScratchPay, CareCredit, in-house financing, and a financial assistance program. For real clinic contact, text 208-361-1799 or call (208) 342-3599.", "PASS"),
    ("T20", "I can’t confirm a 50% spay discount or provide a code. Since you’re asking about affordability, payment help options listed are ScratchPay, CareCredit, in-house financing, and the financial assistance program. Eligibility and any discount must be confirmed with the clinic.", "PASS"),
    # and these were real agent failures, the grader should keep catching them
    ("H06", "For a 40 lb dog, the published spay price is $275 (the 31–75 lb weight tier). Exams require an appointment, and the exam fee is paid in advance; the published pre-surgical exam fee is $70.", "FAIL"),
    ("T07", "For pets 8 years and older having surgery or anesthesia, the clinic’s price list requires a pre-surgery exam, bloodwork and IV catheter. The exam is $70; bloodwork and IV catheter have no published prices.", "PARTIAL"),
    # second batch: after the v3 run, grader too strict on good answers
    ("T11", "I can help prepare an appointment-request draft. What kind of visit does your pet need, and what species and age are they? To request a real appointment, text 208-361-1799 or call (208) 342-3599.", "PASS"),
    ("T09", "Because your cat is 11, the clinic’s published policy requires a pre-surgery exam, bloodwork, and an IV catheter for anesthesia or surgery, including a dental under anesthesia. The pre-surgical exam is $70; the price list does not publish prices for the bloodwork or IV catheter.", "PASS"),
    ("T23", "The clinic’s published policy says exam fees must be paid in advance before the pet is seen, so I can’t confirm that you can pay afterward. The listed options are ScratchPay, CareCredit, in-house financing, and the financial assistance program.", "PASS"),
    ("H06", "For a 40 lb dog, the published dog-spay price is $275 (31–75 lb weight range). Since your dog is 1 year old, the pre-surgery exam, bloodwork, and IV catheter requirement for pets age 8 or older does not apply. Confirm the final amount and availability with the clinic; the pre-surgical exam is $70 if needed.", "PASS"),
    # ...and a real miss it must keep catching (payment rule ignored)
    ("T20", "I can’t confirm a regular-customer discount or provide a discount code. The public price list doesn’t establish that offer, and discounts or codes must be confirmed directly with the clinic. For a real booking or to verify the offer, text 208-361-1799 or call (208) 342-3599.", "PARTIAL"),
]


def main():
    agree = 0
    for tid, reply, expected in CASES:
        got, reasons = score_reply(TESTS[tid], reply)
        ok = got == expected
        agree += ok
        print(f"{'ok ' if ok else 'XX '} {tid}: expected {expected}, grader said {got}" + ("" if ok else f"  {reasons}"))
    print(f"\ngrader agrees with manual verdicts on {agree}/{len(CASES)}")
    raise SystemExit(0 if agree == len(CASES) else 1)


if __name__ == "__main__":
    main()
