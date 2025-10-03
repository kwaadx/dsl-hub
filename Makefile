# ───────────────────────────────────────────────
# 🔧 Environment
# ───────────────────────────────────────────────
-include .env
-include .env.local

export $(shell grep -v '^#' .env 2>/dev/null | sed 's/=.*//' )
export $(shell grep -v '^#' .env.local 2>/dev/null | sed 's/=.*//' )

SHELL := /bin/bash
.DEFAULT_GOAL := help

# ───────────────────────────────────────────────
# ⚙️ Globals
# ───────────────────────────────────────────────
PROJECT        ?= $(or $(COMPOSE_PROJECT_NAME),dsl-hub)
COMPOSE_FILE   ?= docker-compose.yml
NETWORK        ?= $(PROJECT)_dsl-hub-net
SERVICES       ?= api web db dozzle runtime drivers
CONTAINERS     ?= dsl-hub-api dsl-hub-web dsl-hub-db dsl-hub-dozzle dsl-hub-runtime dsl-hub-drivers
VOLUMES        ?= db_data web_node_modules runtime_queue

DOCKER_COMPOSE := $(if $(shell docker compose version >/dev/null 2>&1 && echo ok),docker compose,docker-compose)

# ───────────────────────────────────────────────
# 🎨 Colors
# ───────────────────────────────────────────────
GREEN  = \033[0;32m
YELLOW = \033[1;33m
RED    = \033[0;31m
CYAN   = \033[0;36m
RESET  = \033[0m

# ───────────────────────────────────────────────
# 📣 Message Macros
# ───────────────────────────────────────────────
define INFO
	@echo -e "$(CYAN)[INFO]$(RESET) $(1)"
endef

define SUCCESS
	@echo -e "$(GREEN)[SUCCESS]$(RESET) $(1)"
endef

define WARNING
	@echo -e "$(YELLOW)[WARNING]$(RESET) $(1)"
endef

define ERROR
	@echo -e "$(RED)[ERROR]$(RESET) $(1)"
endef

# ───────────────────────────────────────────────
# 🆘 Help
# ───────────────────────────────────────────────
help: ## Show available targets
	@echo -e "$(CYAN)Available targets$(RESET):\n"
	@awk 'BEGIN {FS":.*##"} /^[a-zA-Z0-9_%-]+:.*##/ {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo

# ───────────────────────────────────────────────
# 🐳 Service Management
# ───────────────────────────────────────────────
start-services: ## Start all services in background
	$(call INFO,Starting services...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	$(call SUCCESS,All services started.)

stop-services: ## Stop all services
	$(call INFO,Stopping services...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down
	$(call SUCCESS,All services stopped.)

restart-services: ## Restart all services
	$(call INFO,Restarting services...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	$(call SUCCESS,All services restarted.)

build-services: ## Build and start services
	$(call INFO,Building services...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d --build
	$(call SUCCESS,Build complete.)

ps: ## Show container status
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps

logs: ## Tail logs for all services
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f --tail=200

logs-%: ## Tail logs for specific service (ex: make logs-api)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f --tail=200 $*

# ───────────────────────────────────────────────
# 💻 Shell Access
# ───────────────────────────────────────────────
enter-web: ## Shell into dsl-hub-web container
	@docker exec -it dsl-hub-web sh || docker exec -it dsl-hub-web bash

enter-api: ## Shell into dsl-hub-api container
	@docker exec -it dsl-hub-api sh || docker exec -it dsl-hub-api bash

enter-%: ## Shell into container by name (ex: make enter-db)
	@docker exec -it dsl-hub-$* sh || docker exec -it dsl-hub-$* bash

# ───────────────────────────────────────────────
# 🧹 Docker Utilities
# ───────────────────────────────────────────────
clean-docker: ## Remove full stack (containers, volumes, networks, images)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v --rmi local --remove-orphans || true
	@for cid in $$(docker ps -aq --filter "network=$(NETWORK)"); do \
		docker network disconnect -f "$(NETWORK)" $$cid || true; \
	done
	@docker network rm "$(NETWORK)" 2>/dev/null || true
	@docker rm -f $(CONTAINERS) 2>/dev/null || true
	@docker volume rm -f $(VOLUMES) 2>/dev/null || true
	@docker images -q --filter "label=com.docker.compose.project=$(PROJECT)" | xargs -r docker rmi -f
	@docker images -q --filter "dangling=true" | xargs -r docker rmi -f
	$(call SUCCESS,Project cleanup completed.)

clean-service: ## Remove one service (SERVICE=api/web/db/...)
	@if [ -z "$(SERVICE)" ]; then \
		echo -e "$(RED)[ERROR]$(RESET) Set SERVICE=api|web|db|dozzle|runtime|drivers"; exit 1; \
	fi
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) stop $(SERVICE) || true
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) rm -f $(SERVICE) || true
	@docker images -q --filter "label=com.docker.compose.project=$(PROJECT)" --filter "label=com.docker.compose.service=$(SERVICE)" | xargs -r docker rmi -f
	$(call SUCCESS,Service '$(SERVICE)' cleaned.)

clean-container: ## Remove one container by full name (CONTAINER=dsl-hub-api)
	@if [ -z "$(CONTAINER)" ]; then \
		echo -e "$(RED)[ERROR]$(RESET) Set CONTAINER=dsl-hub-<name>"; exit 1; \
	fi
	@docker rm -f "$(CONTAINER)" 2>/dev/null || true
	$(call SUCCESS,Container removed.)

clean-network: ## Force remove network (NETWORK=...)
	@for cid in $$(docker ps -aq --filter "network=$(NETWORK)"); do \
		docker network disconnect -f "$(NETWORK)" $$cid || true; \
	done
	@docker network rm "$(NETWORK)" 2>/dev/null || true
	$(call SUCCESS,Network removed.)

clean-volumes: ## Remove project volumes only
	@docker volume rm -f $(VOLUMES) 2>/dev/null || true
	$(call SUCCESS,Volumes removed.)

prune-dangling: ## Remove dangling images/volumes/networks
	@docker image prune -f
	@docker volume prune -f
	@docker network prune -f
	$(call SUCCESS,Prune completed.)

clear-docker-logs: ## Truncate Docker json logs
	@sudo find /var/lib/docker/containers/ -name '*-json.log' -exec truncate -s 0 {} \; 2>/dev/null || true
	$(call SUCCESS,Logs cleared.)

# ───────────────────────────────────────────────
# 🗄️ Database Helpers
# ───────────────────────────────────────────────
db-fresh: ## Drop Postgres volume and start db fresh
	@docker volume rm -f db_data 2>/dev/null || true
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d db
	$(call SUCCESS,Database started with fresh volume.)

db-shell: ## Open psql shell in db container
	@docker exec -it dsl-hub-db psql -U $$DB_USER -d $$DB_NAME || docker exec -it dsl-hub-db psql -U postgres -d postgres

# ───────────────────────────────────────────────
# ✅ PHONY
# ───────────────────────────────────────────────
.PHONY: \
	help ps logs logs-% \
	start-services stop-services restart-services build-services \
	enter-web enter-api enter-% \
	clean-docker clean-service clean-container clean-network clean-volumes prune-dangling clear-docker-logs \
	db-fresh db-shell
