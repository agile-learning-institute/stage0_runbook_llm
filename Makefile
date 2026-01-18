.PHONY: help container e2e deploy spark show-config clear-config

# Docker image configuration
IMAGE_NAME = ghcr.io/agile-learning-institute/stage0_runbook_llm:latest

# Default environment variables (e2e test values)
REPO_ROOT ?= $(PWD)/test/repo
CONTEXT_ROOT ?= $(PWD)/test/context
LLM_PROVIDER ?= null
LLM_MODEL ?= codellama
LLM_BASE_URL ?= http://localhost:11434
LLM_API_KEY ?=
LLM_TEMPERATURE ?= 7
LLM_MAX_TOKENS ?= 8192
LOG_LEVEL ?= INFO

# Spark configuration (overrides defaults)
SPARK_LLM_PROVIDER = ollama
SPARK_LLM_MODEL = qwen3-coder:30b
SPARK_LLM_BASE_URL = http://spark-478a.local:11434

help:
	@echo "Available commands:"
	@echo "  make container        - Build Docker container image"
	@echo "  make e2e              - Run E2E tests against container"
	@echo "  make deploy           - Run CLI in container (requires TASK_NAME)"
	@echo "  make spark            - Quick start with pre-configured Ollama settings"
	@echo "  make show-config      - Show current configuration values"
	@echo "  make clear-config     - Show command to clear all environment variables"
	@echo ""
	@echo "Environment variables (all have defaults except TASK_NAME):"
	@echo "  REPO_ROOT             - Repository root path (default: ./test/repo)"
	@echo "  CONTEXT_ROOT          - Context root path (default: ./test/context)"
	@echo "  TASK_NAME             - Task name to execute (required)"
	@echo "  LLM_PROVIDER          - LLM provider: null, ollama, openai, azure (default: null)"
	@echo "  LLM_MODEL             - LLM model name (default: codellama)"
	@echo "  LLM_BASE_URL          - LLM API base URL (default: http://localhost:11434)"
	@echo "  LLM_API_KEY           - LLM API key (optional, for OpenAI/Azure)"
	@echo "  LLM_TEMPERATURE       - LLM temperature (default: 7)"
	@echo "  LLM_MAX_TOKENS        - Max tokens (default: 8192)"
	@echo "  LOG_LEVEL             - Logging level (default: INFO)"

container:
	@echo "Building Docker container image..."
	docker build --tag $(IMAGE_NAME) .

e2e: container
	@echo "Running E2E container tests..."
	@$(PWD)/test/e2e/run_container_e2e.sh

deploy:
	@echo "Running CLI in container..."
	@if [ -z "$(TASK_NAME)" ]; then \
		echo "Error: TASK_NAME environment variable is required"; \
		exit 1; \
	fi
	docker run --rm \
		-v "$(REPO_ROOT):/workspace/repo" \
		-v "$(CONTEXT_ROOT):/workspace/context" \
		-e "REPO_ROOT=/workspace/repo" \
		-e "CONTEXT_ROOT=/workspace/context" \
		-e "TASK_NAME=$(TASK_NAME)" \
		-e "LLM_PROVIDER=$(LLM_PROVIDER)" \
		-e "LLM_MODEL=$(LLM_MODEL)" \
		-e "LLM_BASE_URL=$(LLM_BASE_URL)" \
		-e "LLM_API_KEY=$(LLM_API_KEY)" \
		-e "LLM_TEMPERATURE=$(LLM_TEMPERATURE)" \
		-e "LLM_MAX_TOKENS=$(LLM_MAX_TOKENS)" \
		-e "LOG_LEVEL=$(LOG_LEVEL)" \
		$(IMAGE_NAME)

spark:
	@echo "Running spark (quick start with pre-configured Ollama)..."
	@LLM_PROVIDER=$(SPARK_LLM_PROVIDER) \
	 LLM_MODEL=$(SPARK_LLM_MODEL) \
	 LLM_BASE_URL=$(SPARK_LLM_BASE_URL) \
	 $(MAKE) deploy

show-config:
	@echo "Current configuration values:"
	@echo "=============================="
	@echo "REPO_ROOT:          $(if $(filter environment,$(origin REPO_ROOT)),[ENV] $(REPO_ROOT),[DEFAULT] $(REPO_ROOT))"
	@echo "CONTEXT_ROOT:       $(if $(filter environment,$(origin CONTEXT_ROOT)),[ENV] $(CONTEXT_ROOT),[DEFAULT] $(CONTEXT_ROOT))"
	@echo "TASK_NAME:          $(if $(filter environment,$(origin TASK_NAME)),[ENV] $(TASK_NAME),[NOT SET])"
	@echo "LLM_PROVIDER:       $(if $(filter environment,$(origin LLM_PROVIDER)),[ENV] $(LLM_PROVIDER),[DEFAULT] $(LLM_PROVIDER))"
	@echo "LLM_MODEL:          $(if $(filter environment,$(origin LLM_MODEL)),[ENV] $(LLM_MODEL),[DEFAULT] $(LLM_MODEL))"
	@echo "LLM_BASE_URL:       $(if $(filter environment,$(origin LLM_BASE_URL)),[ENV] $(LLM_BASE_URL),[DEFAULT] $(LLM_BASE_URL))"
	@echo "LLM_API_KEY:        $(if $(filter environment,$(origin LLM_API_KEY)),[ENV] $(if $(LLM_API_KEY),<set>,$(LLM_API_KEY)),[DEFAULT] $(if $(LLM_API_KEY),<set>,$(LLM_API_KEY)))"
	@echo "LLM_TEMPERATURE:    $(if $(filter environment,$(origin LLM_TEMPERATURE)),[ENV] $(LLM_TEMPERATURE),[DEFAULT] $(LLM_TEMPERATURE))"
	@echo "LLM_MAX_TOKENS:     $(if $(filter environment,$(origin LLM_MAX_TOKENS)),[ENV] $(LLM_MAX_TOKENS),[DEFAULT] $(LLM_MAX_TOKENS))"
	@echo "LOG_LEVEL:          $(if $(filter environment,$(origin LOG_LEVEL)),[ENV] $(LOG_LEVEL),[DEFAULT] $(LOG_LEVEL))"
	@echo "=============================="
	@echo ""

clear-config:
	@echo "To clear all environment variables and use defaults, run:"
	@echo ""
	@echo "unset REPO_ROOT CONTEXT_ROOT TASK_NAME LLM_PROVIDER LLM_MODEL LLM_BASE_URL LLM_API_KEY LLM_TEMPERATURE LLM_MAX_TOKENS LOG_LEVEL"
	@echo ""
	@echo "Or run make commands with variables explicitly unset:"
	@echo "env -u REPO_ROOT -u CONTEXT_ROOT -u TASK_NAME -u LLM_PROVIDER -u LLM_MODEL -u LLM_BASE_URL -u LLM_API_KEY -u LLM_TEMPERATURE -u LLM_MAX_TOKENS -u LOG_LEVEL make <command>"
	@echo ""
