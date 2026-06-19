#### Basic ontology validation pipeline for the forthcoming SOSA-only track

config.ONTOLOGY_FILE      := sosa-mappings-edit.ttl
config.ONTOLOGY_PREFIX    := sosa-next
config.ONTOLOGY_IRI       := https://w3id.org/ssn-sosa-bfo-cco-mapping/sosa-next
config.RELEASE_FILES      := ../../releases/sosa-next/sosa-bfo-directmappings.ttl ../../releases/sosa-next/sosa-cco-directmappings.ttl

config.TEMP_DIR           := build/artifacts
config.REPORTS_DIR        := $(config.TEMP_DIR)
config.QUERIES_DIR        := sparql
config.LIBRARY_DIR        := ../../build/lib

config.FAIL_ON_TEST_FAILURES := false
config.REPORT_FAIL_ON        := none

TODAY     := $(shell date +%Y-%m-%d)
TIMESTAMP := $(shell date +'%Y-%m-%d %H:%M')

config.RELEASE_NAME := $(config.ONTOLOGY_PREFIX) $(TIMESTAMP)

EDITOR_BUILD_FILE  := $(config.ONTOLOGY_FILE)
EDITOR_REPORT_FILE := $(config.REPORTS_DIR)/$(config.ONTOLOGY_PREFIX)-edit-report.tsv
REQUIRED_DIRS      := $(sort $(config.TEMP_DIR) $(config.LIBRARY_DIR) $(config.QUERIES_DIR) $(config.REPORTS_DIR))

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
