#### Parse validation for retained current SSN/SOSA examples

config.TEMP_DIR      := build/artifacts
config.LIBRARY_DIR   := ../../build/lib
config.EXAMPLES_DIR  := examples

EXAMPLE_VALIDATION_DIR := $(config.TEMP_DIR)/example-validation
ROBOT_FILE := $(config.LIBRARY_DIR)/robot.jar
ROBOT := java -jar $(ROBOT_FILE)

.PHONY: all validate-examples clean
all: validate-examples

validate-examples: | $(EXAMPLE_VALIDATION_DIR) $(ROBOT_FILE)
	@files="$$(find $(config.EXAMPLES_DIR) -type f -name '*.ttl' | sort)"; \
	if [ -z "$$files" ]; then \
		echo "No Turtle example files found under $(config.EXAMPLES_DIR)."; \
	else \
		for file in $$files; do \
			out="$(EXAMPLE_VALIDATION_DIR)/$$(printf '%s' "$$file" | sed 's#[/.]#_#g').ttl"; \
			echo "Parse-checking $$file"; \
			$(ROBOT) convert --input "$$file" --format ttl --output "$$out"; \
		done; \
	fi

$(EXAMPLE_VALIDATION_DIR) $(config.LIBRARY_DIR):
	mkdir -p $@

$(ROBOT_FILE): | $(config.LIBRARY_DIR)
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.9.5/robot.jar

clean:
	@[ "$(config.TEMP_DIR)" ] || ( echo ">> config.TEMP_DIR is not set"; exit 1 )
	rm -rf $(config.TEMP_DIR)

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:
