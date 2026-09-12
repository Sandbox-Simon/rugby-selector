.DEFAULT_GOAL := help

.PHONY: help install run test check

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "%-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install project dependencies
	poetry install

run: ## Start the Streamlit app
	poetry run streamlit run src/rugby_selector/app.py

test: ## Run the test suite
	poetry run pytest -q

check: ## Validate Poetry configuration and run tests
	poetry check
	poetry run pytest -q
