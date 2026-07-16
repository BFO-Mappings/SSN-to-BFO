.PHONY: validate validate-write audit-write legacy-audit-write compile check check-coms check-coms-row-identities check-coms-product-dispositions check-alignment-core check-strict-bfo-mapping check-cco-extension check-bfo-projection check-publication-metadata watch-coms coms-status post-merge-check status diffstat

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
		tools/coms_row_identity.py \
		tools/product_dispositions.py \
		tools/modular_products.py \
		tools/generate_mapping_from_coms.py \
		tools/check_coms_mapping.py \
		tools/watch_coms_mapping.py \
		tools/publication_metadata.py \
		tools/check_publication_metadata.py \
		tests/test_generate_mapping_from_coms.py \
		tests/test_coms_row_identity.py \
		tests/test_product_dispositions.py \
		tests/test_modular_products.py \
		tests/test_strict_bfo_mapping.py \
		tests/test_cco_extension.py \
		tests/test_bfo_projection.py \
		tests/test_publication_metadata.py \
		tools/workflow_check.py

check-publication-metadata:
	python -m unittest discover -s tests -p 'test_publication_metadata.py'
	python tools/check_publication_metadata.py

check-coms:
	python tools/check_coms_mapping.py

check-coms-row-identities:
	python -m unittest discover -s tests -p 'test_coms_row_identity.py'
	python -m unittest discover -s tests -p 'test_generate_mapping_from_coms.py'
	python tools/check_coms_mapping.py --check-only

check-coms-product-dispositions:
	python -m unittest discover -s tests -p 'test_product_dispositions.py'
	python tools/check_coms_mapping.py --check-only

check-alignment-core:
	python -m unittest discover -s tests -p 'test_modular_products.py'
	python tools/check_coms_mapping.py --check-only

check-strict-bfo-mapping:
	python -m unittest discover -s tests -p 'test_strict_bfo_mapping.py'
	python tools/check_coms_mapping.py --check-only

check-cco-extension:
	python -m unittest discover -s tests -p 'test_cco_extension.py'
	python tools/check_coms_mapping.py --check-only

check-bfo-projection:
	python -m unittest discover -s tests -p 'test_bfo_projection.py'
	python tools/check_coms_mapping.py --check-only

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
