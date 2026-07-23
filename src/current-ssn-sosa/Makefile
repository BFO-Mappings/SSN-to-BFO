#### Parse validation for retained current SSN/SOSA examples

config.TEMP_DIR      := build/artifacts
config.EXAMPLES_DIR  := examples

REPOSITORY_ROOT := $(abspath ../..)
ROBOT_INSTALLER := $(REPOSITORY_ROOT)/tools/install_validation_robot.sh
EXAMPLE_VALIDATION_DIR := $(config.TEMP_DIR)/example-validation

.PHONY: all validate-examples clean
all: validate-examples

validate-examples: | $(EXAMPLE_VALIDATION_DIR)
	@robot_bin="$$( "$(ROBOT_INSTALLER)" )"; \
	robot="$$robot_bin/robot"; \
	files="$$(find $(config.EXAMPLES_DIR) -type f -name '*.ttl' | sort)"; \
	if [ -z "$$files" ]; then \
		echo "No Turtle example files found under $(config.EXAMPLES_DIR)."; \
	else \
		for file in $$files; do \
			out="$(EXAMPLE_VALIDATION_DIR)/$$(printf '%s' "$$file" | sed 's#[/.]#_#g').ttl"; \
			echo "Parse-checking $$file"; \
			"$$robot" convert --input "$$file" --format ttl --output "$$out"; \
		done; \
	fi

$(EXAMPLE_VALIDATION_DIR):
	mkdir -p $@

clean:
	@[ "$(config.TEMP_DIR)" ] || ( echo ">> config.TEMP_DIR is not set"; exit 1 )
	rm -rf $(config.TEMP_DIR)
	mkdir -p $(config.TEMP_DIR)
	touch $(config.TEMP_DIR)/.gitkeep

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:
