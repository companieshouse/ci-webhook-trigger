source_directory := source

.PHONY: all
all: dist

.PHONY: clean
clean:
	rm *.zip
	rm -rf $(source_directory)/dist

.PHONY: test
test: test-unit

.PHONY: test-unit
test-unit:
	$(error Not yet implemented!)

.PHONY: package
package:
ifndef function_name
	$(error No function_name given. Aborting)
endif
ifndef version
	$(error No version given. Aborting)
endif
	$(info Packaging version: $(version))
	cd $(source_directory) && lambda build
	mv $(source_directory)/dist/*$(function_name).zip ./$(function_name)-$(version).zip

.PHONY: dist
dist: clean package
