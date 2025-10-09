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
# ⚙️ Globals (override via env or CLI)
# ───────────────────────────────────────────────
PROJECT        ?= $(or $(COMPOSE_PROJECT_NAME),dsl-hub)
COMPOSE_FILE   ?= docker-compose.yml
NETWORK        ?= $(PROJECT)_dsl-hub-net
SERVICES       ?= api web db dozzle runtime drivers
CONTAINERS     ?= dsl-hub-api dsl-hub-web dsl-hub-db dsl-hub-dozzle dsl-hub-runtime dsl-hub-drivers
VOLUMES        ?= db_data web_node_modules runtime_queue

# Auto-detect Compose v2 vs v1
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
	@awk 'BEGIN {FS":.*##"} /^[a-zA-Z0-9_%-]+:.*##/ {printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo

# ───────────────────────────────────────────────
# 🐳 Service Management
# ───────────────────────────────────────────────

# ---- Tests (Docker) ----
# Run tests inside the api service container so env and deps match
# Usage:
#   make test            # run all tests in /tests
#   make test ARGS='-k sse'  # pass extra pytest args
TEST_ARGS ?=

test: ## Run pytest inside the api container (uses ./tests)
	$(call INFO,Running tests in Docker ...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) run --rm api pytest -q /app/api/src/tests $(TEST_ARGS)
	$(call SUCCESS,Tests finished.)
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

logs-%: ## Tail logs for a specific service (ex: make logs-api)
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
# 🧹 Docker Utilities (project scoped)
# ───────────────────────────────────────────────
clean-docker: ## Remove full stack (containers, volumes, networks, images) for this project
	$(call INFO,Tearing down compose stack ...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v --rmi local --remove-orphans || true

	$(call INFO,Force-disconnecting anything left on network '$(NETWORK)' ...)
	@for cid in $$(docker ps -aq --filter "network=$(NETWORK)"); do \
		docker network disconnect -f "$(NETWORK)" $$cid || true; \
	done

	$(call INFO,Removing network/containers/volumes ...)
	@docker network rm "$(NETWORK)" 2>/dev/null || true
	@docker rm -f $(CONTAINERS) 2>/dev/null || true
	@docker volume rm -f $(VOLUMES) 2>/dev/null || true

	$(call INFO,Removing project images ...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) images -q | xargs -r docker rmi -f
	@docker images -q --filter "label=com.docker.compose.project=$(PROJECT)" | xargs -r docker rmi -f
	@docker images -q --filter "dangling=true" | xargs -r docker rmi -f

	$(call SUCCESS,Project cleanup completed.)

clean-service: ## Remove one service (SERVICE=api/web/db/...) incl. its image
	@if [ -z "$(SERVICE)" ]; then \
		echo -e "$(RED)[ERROR]$(RESET) Set SERVICE=api|web|db|dozzle|runtime|drivers"; exit 1; \
	fi
	$(call INFO,Removing service '$(SERVICE)' ...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) stop $(SERVICE) || true
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) rm -f $(SERVICE) || true
	@docker images -q --filter "label=com.docker.compose.project=$(PROJECT)" --filter "label=com.docker.compose.service=$(SERVICE)" | xargs -r docker rmi -f
	$(call SUCCESS,Service '$(SERVICE)' cleaned.)

clean-container: ## Remove a single container by full name (CONTAINER=dsl-hub-api)
	@if [ -z "$(CONTAINER)" ]; then \
		echo -e "$(RED)[ERROR]$(RESET) Set CONTAINER=dsl-hub-<name>"; exit 1; \
	fi
	$(call INFO,Removing container $(CONTAINER) ...)
	@docker rm -f "$(CONTAINER)" 2>/dev/null || true
	$(call SUCCESS,Container removed (if existed).)

clean-network: ## Force remove the compose network (NETWORK=...)
	$(call INFO,Removing network '$(NETWORK)' ...)
	@for cid in $$(docker ps -aq --filter "network=$(NETWORK)"); do \
		docker network disconnect -f "$(NETWORK)" $$cid || true; \
	done
	@docker network rm "$(NETWORK)" 2>/dev/null || true
	$(call SUCCESS,Network removed.)

clean-volumes: ## Remove project volumes only
	$(call INFO,Removing project volumes ...)
	@docker volume rm -f $(VOLUMES) 2>/dev/null || true
	$(call SUCCESS,Volumes removed.)

prune-dangling: ## Prune dangling images/volumes/networks
	$(call INFO,Pruning dangling resources ...)
	@docker image prune -f
	@docker volume prune -f
	@docker network prune -f
	$(call SUCCESS,Prune completed.)

clear-docker-logs: ## Truncate Docker json logs (may require sudo)
	$(call INFO,Clearing Docker logs ...)
	@sudo find /var/lib/docker/containers/ -name '*-json.log' -exec truncate -s 0 {} \; 2>/dev/null || true
	$(call SUCCESS,Logs cleared.)

# ───────────────────────────────────────────────
# 🧱 Rebuild / Reset helpers
# ───────────────────────────────────────────────
build-no-cache: ## Build all images with --no-cache and --pull, then start
	$(call INFO,Building with --no-cache and pulling latest base images ...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build --no-cache --pull
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	$(call SUCCESS,Fresh build completed.)

# ───────────────────────────────────────────────
# 🧨 Full project-scoped reset (containers + volumes + images + orphans)
# ───────────────────────────────────────────────
reset: ## Variant A: wipe ONLY this project's stack (containers, volumes, images, networks), then rebuild & start
	$(call WARNING,This will WIPE containers/volumes/images for project '$(PROJECT)'!)
	# 1) Down + remove orphans
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down --remove-orphans || true
	# 2) Down with volumes + local images (double-tap to be sure)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v --rmi local --remove-orphans || true

	# 3) Kill any leftover "compose run" orphans like $(PROJECT)-api-run-xxxx
	@docker ps -aq --filter "name=$(PROJECT)-.*-run-" | xargs -r docker rm -f

	# 4) Hard remove project network (if still alive) after disconnecting stragglers
	@for cid in $$(docker ps -aq --filter "network=$(NETWORK)"); do \
		docker network disconnect -f "$(NETWORK)" $$cid || true; \
	done
	@docker network rm "$(NETWORK)" 2>/dev/null || true

	# 5) Remove ALL project-scoped volumes & images by label (safer than hardcoding names)
	@docker volume ls -q --filter "label=com.docker.compose.project=$(PROJECT)" | xargs -r docker volume rm -f
	@docker images -q --filter "label=com.docker.compose.project=$(PROJECT)" | xargs -r docker rmi -f
	# Also remove any dangling stuff left behind
	@docker image prune -f >/dev/null || true

	# 6) (Opt.) Clean build cache so images are truly fresh
	@docker builder prune -af >/dev/null || true

	# 7) Fresh build & up
	$(call INFO,Building images with --no-cache --pull ...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build --no-cache --pull
	$(call INFO,Starting services ...)
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	$(call SUCCESS,Variant A reset done — fresh stack is running.)

# ───────────────────────────────────────────────
# 🗄️ Small fix: DB shell helper (uses DB_NAME)
# ───────────────────────────────────────────────
db-shell: ## Open psql shell in db container
	@docker exec -it dsl-hub-db psql -U $$DB_USER -d $$DB_NAME \
	|| docker exec -it dsl-hub-db psql -U postgres -d postgres

prune-build-cache: ## Remove Docker build cache (buildx)
	$(call INFO,Pruning Docker build cache ...)
	@docker builder prune -af
	$(call SUCCESS,Build cache pruned.)

# ───────────────────────────────────────────────
# 🗄️ Database Helpers
# ───────────────────────────────────────────────
db-fresh: ## Drop Postgres volume and start db fresh
	$(call WARNING,This will DELETE Postgres volume 'db_data'!)
	@docker volume rm -f db_data 2>/dev/null || true
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d db
	$(call SUCCESS,Database started with fresh volume.)
	$(MAKE) guidelines-sync

db-shell: ## Open psql shell in db container
	@docker exec -it dsl-hub-db psql -U $$DB_USER -d $$DB_DB || docker exec -it dsl-hub-db psql -U postgres -d postgres

# ───────────────────────────────────────────────
# 📄 Docs helpers
# ───────────────────────────────────────────────

guidelines-sync: ## Regenerate .junie/guidelines.md from current Alembic migration
	$(call INFO,Updating guidelines from Alembic schema ...)
	@python3 apps/api/alembic/update_guidelines.py || true
	$(call SUCCESS,Guidelines updated.)

# ───────────────────────────────────────────────
# ✅ PHONY
# ───────────────────────────────────────────────
.PHONY: \
	help ps logs logs-% \
	start-services stop-services restart-services build-services \
	enter-web enter-api enter-% \
	clean-docker clean-service clean-container clean-network clean-volumes prune-dangling clear-docker-logs \
	build-no-cache reset prune-build-cache \
	db-fresh db-shell guidelines-sync
