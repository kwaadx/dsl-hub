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
# 🐳 Service Management
# ───────────────────────────────────────────────
restart-services:
	$(call INFO,Restarting services...)
	@docker compose down
	@docker compose up -d

start-services:
	$(call INFO,Starting services...)
	@docker compose up -d

stop-services:
	$(call INFO,Stopping services...)
	@docker compose down

build-services:
	$(call INFO,Building services...)
	@docker compose up -d --build

# ───────────────────────────────────────────────
# 💻 Shell Access
# ───────────────────────────────────────────────
enter-web:
	$(call INFO,Entering dsl-hub-web container...)
	@docker exec -it dsl-hub-web sh

# ───────────────────────────────────────────────
# 🧱 Web
# ───────────────────────────────────────────────
build-web:
	$(call INFO,Building dashboard-frontend assets inside the container...)
	@DASHBOARD_FRONTEND_CONTAINER=$$(docker ps --filter "name=web" --format "{{.ID}}"); \
	if [ -z "$$WEB_CONTAINER" ]; then \
	    echo "❌ Dashboard container is not running. Please check your setup."; \
	    exit 1; \
	fi; \
	echo "🚀 Running 'npm run build'..."; \
	docker exec -it $$DASHBOARD_FRONTEND_CONTAINER npm run build; \
	echo "✅ Web build completed!"

# ───────────────────────────────────────────────
# 🧹 Docker Utilities
# ───────────────────────────────────────────────
clean-docker:
	$(call INFO,Starting Docker cleanup process...)
	@docker ps -q | xargs -r docker stop
	@docker ps -aq | xargs -r docker rm
	@docker images -aq | xargs -r docker rmi -f
	@docker volume prune -f
	@docker network prune -f
	@docker system prune -af --volumes
	$(call SUCCESS,Docker cleanup completed!)

clear-docker-logs:
	$(call INFO,Clearing Docker logs...)
	@sudo find /var/lib/docker/containers/ -name '*-json.log' -exec truncate -s 0 {} \;
	$(call SUCCESS,Logs cleared.)

# ───────────────────────────────────────────────
# ✅ PHONY targets
# ───────────────────────────────────────────────
.PHONY: \
	clean-docker clear-docker-logs \
	build-web enter-web \
	build-services restart-services start-services stop-services
