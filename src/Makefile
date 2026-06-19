#### Track dispatcher for SSN/SOSA -> BFO/CCO mapping validation

TRACKS := current-ssn-sosa sosa-next

.PHONY: all $(TRACKS) reason-current-ssn-sosa test-current-ssn-sosa hygiene-current-ssn-sosa reason-sosa-next test-sosa-next hygiene-sosa-next clean

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

clean:
	$(MAKE) -C current-ssn-sosa clean
	$(MAKE) -C sosa-next clean
