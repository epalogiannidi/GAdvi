## MAKEFILE

.DEFAULT: help


## HELP

.PHONY: help
help:
	@echo "    black"
	@echo "        Format code using black, the Python code formatter"
	@echo "    black-check"
	@echo "        Check if source code complies with black"
	@echo "    lint"
	@echo "        Check source code with flake8"
	@echo "    mypy"
	@echo "        Check static typing with mypy"
	@echo "    check-codestyle"
	@echo "        Perform a complete codestyle checking"

## CODE STYLE RELATED

.PHONY: black
black:
	# run black code formatter
	black gadvi/ scripts/

.PHONY: black-check
black-check:
	# dry run black code formatter
	black --check gadvi/ scripts/

.PHONY: lint
lint:
	# run flake linter
	flake8 --max-line-length 120 --ignore E203,E402,W503 gadvi/ scripts/

.PHONY: mypy
mypy:
	# run the mypy static typing checker
	mypy --config-file ./mypi.ini gadvi/ scripts/
	rm -rf ./mypy_cache

.PHONY: check-codestyle
check-codestyle: black-check lint mypy