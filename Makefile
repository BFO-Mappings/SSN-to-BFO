.PHONY: validate validate-write audit-write compile check post-merge-check status diffstat

validate:
	python tools/run_validation_suite.py

validate-write:
	python tools/run_validation_suite.py --write-reports

audit-write:
	python tools/compare_mappings.py \
		--ttl SSN2BFO.ttl \
		--spreadsheet "Current_SOSA-SSN to BFO-CCO.xlsx" \
		--output-md reports/mapping-consistency-audit.md \
		--output-csv reports/mapping-consistency-audit.csv

compile:
	python -m py_compile \
		tools/run_validation_suite.py \
		tools/test_elk_instance_mapping_entailments.py \
		tools/test_instance_data.py \
		tools/compare_mappings.py \
		tools/workflow_check.py

check: validate compile
	git diff --check
	git status --short

post-merge-check:
	git status --short
	python tools/run_validation_suite.py
	git status --short

status:
	git branch --show-current
	git status --short

diffstat:
	git diff --stat
	git diff --cached --stat
