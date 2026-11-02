PY = .venv/bin/python

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	$(PY) -m playwright install chromium

check-grader:
	cd eval && ../$(PY) test_scoring.py

# full run, 3 repeats
eval: check-grader
	$(PY) eval/run_eval.py --repeats 3 --label $(or $(LABEL),local)

# quick smoke test, 1 repeat of the safety + regression tests
smoke:
	$(PY) eval/run_eval.py --repeats 1 --only T13 T14 T15 T16 T24 H01 H05 H06 --label smoke

# make compare A=results/runs/<before> B=results/runs/<after>
compare:
	$(PY) eval/compare.py $(A) $(B)
