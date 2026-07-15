.PHONY: validate validate-write audit-write legacy-audit-write compile check check-coms check-publication-metadata watch-coms coms-status post-merge-check status diffstat

validate:
	python tools/run_validation_suite.py

validate-write:
	python tools/run_validation_suite.py --write-reports

audit-write: legacy-audit-write

legacy-audit-write:
	@echo "Running informational pre-COMS legacy ontology/spreadsheet audit (not a release gate)."
	python tools/compare_mappings.py \
		--ttl legacy/SSN2BFO-pre-COMS.ttl \
		--spreadsheet "Current_SOSA-SSN to BFO-CCO.xlsx" \
		--output-md reports/mapping-consistency-audit.md \
		--output-csv reports/mapping-consistency-audit.csv

compile:
	python -m py_compile \
		tools/run_validation_suite.py \
		tools/test_elk_instance_mapping_entailments.py \
		tools/test_instance_data.py \
		tools/compare_mappings.py \
		tools/generate_mapping_from_coms.py \
		tools/check_coms_mapping.py \
		tools/watch_coms_mapping.py \
		tools/publication_metadata.py \
		tools/check_publication_metadata.py \
		tests/test_generate_mapping_from_coms.py \
		tests/test_publication_metadata.py \
		tools/workflow_check.py

check-publication-metadata:
	python -m unittest discover -s tests -p 'test_publication_metadata.py'
	python tools/check_publication_metadata.py

check-coms:
	python tools/check_coms_mapping.py

watch-coms:
	@echo "Watching mappings/SSN2BFO-COMS.xlsx. Press Ctrl+C to stop."
	python tools/watch_coms_mapping.py

coms-status:
	python tools/check_coms_mapping.py --status

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
