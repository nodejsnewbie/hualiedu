.PHONY: backend

backend:
	$(MAKE) -C backend

%:
	$(MAKE) -C backend $@
