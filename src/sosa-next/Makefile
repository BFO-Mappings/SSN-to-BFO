#### Basic ontology validation and artifact pipeline for the forthcoming SOSA-only track

config.ONTOLOGY_FILE      := sosa-mappings-edit.ttl
config.ONTOLOGY_PREFIX    := sosa-next
config.ONTOLOGY_IRI       := http://www.sks.ai/SSN2BFO/development/sosa-next
config.RELEASE_FILES      := \
	../../releases/sosa-next/sosa-integrated.ttl \
	../../releases/sosa-next/sosa-bfo-mapping.ttl \
	../../releases/sosa-next/sosa-cco-extension.ttl \
	../../releases/sosa-next/sosa-ro-mapping.ttl

config.TEMP_DIR           := build/artifacts
config.REPORTS_DIR        := $(config.TEMP_DIR)
config.QUERIES_DIR        := sparql
config.EXPORT_QUERIES_DIR := $(config.QUERIES_DIR)/export
config.REPORT_QUERIES_DIR := $(config.QUERIES_DIR)/report
config.LIBRARY_DIR        := ../../build/lib

config.FAIL_ON_TEST_FAILURES := false
config.REPORT_FAIL_ON        := none
config.ENABLE_UNMAPPED_REPORTS := false

TODAY     := $(shell date +%Y-%m-%d)
TIMESTAMP := $(shell date +'%Y-%m-%d %H:%M')

config.RELEASE_NAME := $(config.ONTOLOGY_PREFIX) $(TIMESTAMP)

EDITOR_BUILD_FILE  := $(config.ONTOLOGY_FILE)
EDITOR_REPORT_FILE := $(config.REPORTS_DIR)/$(config.ONTOLOGY_PREFIX)-edit-report.tsv
BFO_SSSOM_FILE     := $(config.REPORTS_DIR)/$(config.ONTOLOGY_PREFIX)-bfo-mappings.sssom.csv
CCO_SSSOM_FILE     := $(config.REPORTS_DIR)/$(config.ONTOLOGY_PREFIX)-cco-mappings.sssom.csv
ENTAILED_MAPPINGS_FILE := $(config.REPORTS_DIR)/$(config.ONTOLOGY_PREFIX)-entailed-mappings.ttl
UNMAPPED_TERMS_FILE := $(config.REPORTS_DIR)/$(config.ONTOLOGY_PREFIX)-unmapped-terms.csv

REQUIRED_DIRS      := $(sort $(config.TEMP_DIR) $(config.LIBRARY_DIR) $(config.QUERIES_DIR) $(config.EXPORT_QUERIES_DIR) $(config.REPORT_QUERIES_DIR) $(config.REPORTS_DIR))

.PHONY: all hygiene
all: reason-edit hygiene
hygiene: test-edit

.PHONY: reason-edit test-edit report-edit explain-edit
reason-edit test-edit report-edit explain-edit: TEST_INPUT = $(EDITOR_BUILD_FILE)
report-edit: REPORT_FILE_INPUT = $(EDITOR_REPORT_FILE)

reason-edit: reason
test-edit: verify
report-edit: report
explain-edit: explain

.PHONY: sssom-bfo sssom-cco sssom entailed-mappings unmapped artifacts
sssom: sssom-bfo sssom-cco
artifacts: report-edit sssom entailed-mappings unmapped

sssom-bfo: $(EDITOR_BUILD_FILE) $(config.EXPORT_QUERIES_DIR)/sssom-bfo-mappings.rq | $(config.TEMP_DIR) $(ROBOT_FILE)
	$(ROBOT) query --input $(EDITOR_BUILD_FILE) --query $(config.EXPORT_QUERIES_DIR)/sssom-bfo-mappings.rq $(BFO_SSSOM_FILE) --format csv

sssom-cco: $(EDITOR_BUILD_FILE) $(config.EXPORT_QUERIES_DIR)/sssom-cco-mappings.rq | $(config.TEMP_DIR) $(ROBOT_FILE)
	$(ROBOT) query --input $(EDITOR_BUILD_FILE) --query $(config.EXPORT_QUERIES_DIR)/sssom-cco-mappings.rq $(CCO_SSSOM_FILE) --format csv

entailed-mappings: $(EDITOR_BUILD_FILE) | $(config.TEMP_DIR) $(ROBOT_FILE)
	$(ROBOT) remove --input $(EDITOR_BUILD_FILE) --select individuals \
	reason --reasoner HermiT --axiom-generators "SubClass EquivalentClass SubObjectProperty EquivalentObjectProperty InverseObjectProperties" --include-indirect true --remove-redundant-subclass-axioms false --exclude-duplicate-axioms true \
	annotate --ontology-iri "$(config.ONTOLOGY_IRI)/generated/entailed-mappings" --version-iri "$(config.ONTOLOGY_IRI)/generated/$(TODAY)/entailed-mappings" --annotation owl:versionInfo "$(TODAY)" --annotation rdfs:comment "Generated artifact for $(config.ONTOLOGY_PREFIX); not a release mapping file." \
	--output $(ENTAILED_MAPPINGS_FILE)

unmapped: $(EDITOR_BUILD_FILE) $(config.REPORT_QUERIES_DIR)/unmapped-terms.rq | $(config.TEMP_DIR) $(ROBOT_FILE)
ifeq ($(config.ENABLE_UNMAPPED_REPORTS),true)
	$(ROBOT) query --input $(EDITOR_BUILD_FILE) --query $(config.REPORT_QUERIES_DIR)/unmapped-terms.rq $(UNMAPPED_TERMS_FILE) --format csv
else
	@echo "Unmapped-term reports are disabled for $(config.ONTOLOGY_PREFIX). Enable config.ENABLE_UNMAPPED_REPORTS only after real source imports and final source namespace configuration are added."
endif

.PHONY: output-release-filepaths
output-release-filepaths:
	@printf '%s\n' $(config.RELEASE_FILES)

.PHONY: output-release-name
output-release-name:
	@echo $(config.RELEASE_NAME)

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:

$(REQUIRED_DIRS):
	mkdir -p $@

ROBOT_FILE := $(config.LIBRARY_DIR)/robot.jar
$(ROBOT_FILE): | $(config.LIBRARY_DIR)
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.9.5/robot.jar

ROBOT := java -jar $(ROBOT_FILE)

.PHONY: clean
clean:
	@[ "$(config.TEMP_DIR)" ] || ( echo ">> config.TEMP_DIR is not set"; exit 1 )
	rm -rf $(config.TEMP_DIR)

.PHONY: reason
reason: $(TEST_INPUT) | $(ROBOT_FILE)
	$(ROBOT) reason --input $(TEST_INPUT) --reasoner HermiT

.PHONY: explain
explain: $(TEST_INPUT) | $(ROBOT_FILE)
	$(ROBOT) explain --input $(TEST_INPUT) --reasoner HermiT -M inconsistency --explanation inconsistency-explanation.md

QUERIES = $(wildcard $(config.QUERIES_DIR)/*.rq)

.PHONY: verify
verify: $(TEST_INPUT) $(QUERIES) | $(config.QUERIES_DIR) $(config.TEMP_DIR) $(ROBOT_FILE)
ifeq ($(QUERIES),)
	$(warning No query files found in $(config.QUERIES_DIR); add forthcoming SOSA-only-specific validation queries when mapping content is inserted)
else
	$(ROBOT) verify --input $(TEST_INPUT) --output-dir $(config.TEMP_DIR) --queries $(QUERIES) --fail-on-violation $(config.FAIL_ON_TEST_FAILURES)
endif

.PHONY: report
report: $(TEST_INPUT) | $(config.REPORTS_DIR) $(ROBOT_FILE)
	$(ROBOT) report --input $(TEST_INPUT) \
	--labels true \
	--fail-on $(config.REPORT_FAIL_ON) \
	--print 10 \
	--output $(REPORT_FILE_INPUT)
