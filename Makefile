FUNCTION_NAME = webhook-trigger

source_directory := source
templates_directory := templates

.PHONY: all
all: dist

.PHONY: clean
clean:
	rm -f *.zip
	rm -rf $(source_directory)/dist

.PHONY: test
test: test-unit

.PHONY: test-unit
test-unit:
	$(error Not yet implemented!)

.PHONY: package
package:
ifndef version
	$(error No version given. Aborting)
endif
	$(info Packaging version: $(version))
	cd $(source_directory) && lambda build
	mv $(source_directory)/dist/*$(FUNCTION_NAME).zip ./$(FUNCTION_NAME)-$(version).zip
	# Add templates to zipped artifact
	zip -ur $(FUNCTION_NAME)-$(version).zip $(templates_directory)

.PHONY: dist
dist: clean package
