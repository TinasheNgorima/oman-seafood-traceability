PY ?= python
.PHONY: env all fetch test clean
env:            ## create a Python 3.11 environment (requires uv)
	uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt
all:            ## reproduce everything offline (about 3 minutes)
	$(PY) scripts/run_all.py
fetch:          ## also re-download Eurostat/ECB (results may change; see README)
	$(PY) scripts/run_all.py --fetch
test: all
	$(PY) -m pytest -q
clean:
	rm -f outputs/*.csv outputs/*.xlsx outputs/*.gexf outputs/*.json outputs/*.txt outputs/figures/*
