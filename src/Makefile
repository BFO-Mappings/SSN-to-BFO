#### Dispatcher for retained source-track validation and examples

TRACKS := sosa-next

.PHONY: all $(TRACKS) reason-sosa-next test-sosa-next hygiene-sosa-next clean
.PHONY: reports reports-sosa-next sssom sssom-sosa-next
.PHONY: entailed-mappings entailed-sosa-next unmapped unmapped-sosa-next
.PHONY: artifacts artifacts-sosa-next validate-examples validate-examples-current-ssn-sosa

all: $(TRACKS)

sosa-next:
	$(MAKE) -C sosa-next all

reason-sosa-next:
	$(MAKE) -C sosa-next reason-edit

test-sosa-next:
	$(MAKE) -C sosa-next test-edit

hygiene-sosa-next:
	$(MAKE) -C sosa-next hygiene

reports: reports-sosa-next

reports-sosa-next:
	$(MAKE) -C sosa-next report-edit

sssom: sssom-sosa-next

sssom-sosa-next:
	$(MAKE) -C sosa-next sssom

entailed-mappings: entailed-sosa-next

entailed-sosa-next:
	$(MAKE) -C sosa-next entailed-mappings

unmapped: unmapped-sosa-next

unmapped-sosa-next:
	$(MAKE) -C sosa-next unmapped

artifacts: artifacts-sosa-next

artifacts-sosa-next:
	$(MAKE) -C sosa-next artifacts

validate-examples: validate-examples-current-ssn-sosa

validate-examples-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa validate-examples

clean:
	$(MAKE) -C current-ssn-sosa clean
	$(MAKE) -C sosa-next clean
