#### Track dispatcher for SSN/SOSA -> BFO/CCO mapping validation and artifacts

TRACKS := current-ssn-sosa sosa-next

.PHONY: all $(TRACKS) reason-current-ssn-sosa test-current-ssn-sosa hygiene-current-ssn-sosa reason-sosa-next test-sosa-next hygiene-sosa-next clean
.PHONY: reports reports-current-ssn-sosa reports-sosa-next sssom sssom-current-ssn-sosa sssom-sosa-next
.PHONY: entailed-mappings entailed-current-ssn-sosa entailed-sosa-next unmapped unmapped-current-ssn-sosa unmapped-sosa-next
.PHONY: artifacts artifacts-current-ssn-sosa artifacts-sosa-next derive-bfo-from-cco derive-bfo-from-cco-current-ssn-sosa

all: $(TRACKS)

current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa all

sosa-next:
	$(MAKE) -C sosa-next all

reason-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa reason-edit

test-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa test-edit

hygiene-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa hygiene

reason-sosa-next:
	$(MAKE) -C sosa-next reason-edit

test-sosa-next:
	$(MAKE) -C sosa-next test-edit

hygiene-sosa-next:
	$(MAKE) -C sosa-next hygiene

reports: reports-current-ssn-sosa reports-sosa-next

reports-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa report-edit

reports-sosa-next:
	$(MAKE) -C sosa-next report-edit

sssom: sssom-current-ssn-sosa sssom-sosa-next

sssom-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa sssom

sssom-sosa-next:
	$(MAKE) -C sosa-next sssom

entailed-mappings: entailed-current-ssn-sosa entailed-sosa-next

entailed-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa entailed-mappings

entailed-sosa-next:
	$(MAKE) -C sosa-next entailed-mappings

unmapped: unmapped-current-ssn-sosa unmapped-sosa-next

unmapped-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa unmapped

unmapped-sosa-next:
	$(MAKE) -C sosa-next unmapped

artifacts: artifacts-current-ssn-sosa artifacts-sosa-next

artifacts-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa artifacts

artifacts-sosa-next:
	$(MAKE) -C sosa-next artifacts

derive-bfo-from-cco: derive-bfo-from-cco-current-ssn-sosa

derive-bfo-from-cco-current-ssn-sosa:
	$(MAKE) -C current-ssn-sosa derive-bfo-from-cco

clean:
	$(MAKE) -C current-ssn-sosa clean
	$(MAKE) -C sosa-next clean
