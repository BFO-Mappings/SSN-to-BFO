.PHONY: validate validate-write audit-write legacy-audit-write compile check check-coms check-coms-row-identities check-coms-product-dispositions check-alignment-core check-strict-bfo-mapping check-cco-extension check-bfo-projection check-publication-metadata check-release-rendering check-release-package check-release-archive check-release-rehearsal check-placeholder-catalog-migration watch-coms coms-status post-merge-check status diffstat

validate:
	PYTHONDONTWRITEBYTECODE=1 python tools/run_validation_suite.py

validate-write:
	PYTHONDONTWRITEBYTECODE=1 python tools/run_validation_suite.py --write-reports

audit-write: legacy-audit-write

legacy-audit-write:
	@echo "Running informational pre-COMS legacy ontology/spreadsheet audit (not a release gate)."
	python tools/compare_mappings.py \
		--ttl legacy/SSN2BFO-pre-COMS.ttl \
		--spreadsheet "Current_SOSA-SSN to BFO-CCO.xlsx" \
		--output-md reports/mapping-consistency-audit.md \
		--output-csv reports/mapping-consistency-audit.csv

compile:
	@cache_dir=$$(mktemp -d /tmp/ssn-to-bfo-pycache.XXXXXX); \
	trap 'rm -rf "$$cache_dir"' EXIT HUP INT TERM; \
	PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$$cache_dir" python -m py_compile \
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
		tools/release_context.py \
		tools/release_manifest.py \
		tools/build_release.py \
		tools/check_release.py \
		tools/release_archive.py \
		tools/rehearse_release.py \
		tests/test_generate_mapping_from_coms.py \
		tests/test_coms_row_identity.py \
		tests/test_product_dispositions.py \
		tests/test_modular_products.py \
		tests/test_strict_bfo_mapping.py \
		tests/test_cco_extension.py \
		tests/test_bfo_projection.py \
		tests/test_publication_metadata.py \
		tests/test_release_context.py \
		tests/test_release_rendering.py \
		tests/test_release_manifest.py \
		tests/test_build_release.py \
		tests/test_release_archive.py \
		tests/test_release_rehearsal.py \
		tests/test_placeholder_catalog_migration.py \
		tools/workflow_check.py

check-publication-metadata:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_publication_metadata.py'
	PYTHONDONTWRITEBYTECODE=1 python tools/check_publication_metadata.py

check-release-rendering:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_release_context.py'
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_release_rendering.py'
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_publication_metadata.py'
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_generate_mapping_from_coms.py'
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_modular_products.py'

check-release-package:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_release_manifest.py'
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_build_release.py'
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_release_context.py'
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_release_rendering.py'

check-release-archive:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_release_archive.py'

check-release-rehearsal:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_release_rehearsal.py'

check-placeholder-catalog-migration:
	PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -p 'test_placeholder_catalog_migration.py'

check-coms:
	PYTHONDONTWRITEBYTECODE=1 python tools/check_coms_mapping.py

check-coms-row-identities:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_coms_row_identity.py'
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_generate_mapping_from_coms.py'
	PYTHONDONTWRITEBYTECODE=1 python tools/check_coms_mapping.py --check-only

check-coms-product-dispositions:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_product_dispositions.py'
	PYTHONDONTWRITEBYTECODE=1 python tools/check_coms_mapping.py --check-only

check-alignment-core:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_modular_products.py'
	PYTHONDONTWRITEBYTECODE=1 python tools/check_coms_mapping.py --check-only

check-strict-bfo-mapping:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_strict_bfo_mapping.py'
	PYTHONDONTWRITEBYTECODE=1 python tools/check_coms_mapping.py --check-only

check-cco-extension:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_cco_extension.py'
	PYTHONDONTWRITEBYTECODE=1 python tools/check_coms_mapping.py --check-only

check-bfo-projection:
	PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_bfo_projection.py'
	PYTHONDONTWRITEBYTECODE=1 python tools/check_coms_mapping.py --check-only

watch-coms:
	@echo "Watching mappings/SSN2BFO-COMS.xlsx. Press Ctrl+C to stop."
	PYTHONDONTWRITEBYTECODE=1 python tools/watch_coms_mapping.py

coms-status:
	PYTHONDONTWRITEBYTECODE=1 python tools/check_coms_mapping.py --status

check: validate compile
	git diff --check
	git status --short

post-merge-check:
	git status --short
	PYTHONDONTWRITEBYTECODE=1 python tools/run_validation_suite.py
	git status --short

status:
	git branch --show-current
	git status --short

diffstat:
	git diff --stat
	git diff --cached --stat
