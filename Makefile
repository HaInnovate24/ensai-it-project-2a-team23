# =====================================================================
# LaborScope - Makefile d'orchestration du projet
# =====================================================================
# Cibles principales :
#   make init      -> initialise TOUT le projet (deps + base de donnees)
#   make run-back  -> lance l'API backend (FastAPI)
#   make run-front -> lance le frontend (Streamlit)
#   make help      -> liste toutes les cibles disponibles
#
# Compatible cmd.exe / PowerShell / Git Bash : aucune recette n'utilise
# de boucle ou de pipe shell, pour ne pas dependre de /bin/bash.
# =====================================================================

# --- Parametres PostgreSQL (alignes sur docker-compose.yml) ----------
PG_SERVICE := postgres
PG_USER    := user
PG_DB      := defaultdb
PG_SCHEMA  := project

# Commandes de base
COMPOSE := docker compose

# psql dans le conteneur, arret immediat a la premiere erreur SQL
PSQL := $(COMPOSE) exec -T $(PG_SERVICE) psql -v ON_ERROR_STOP=1 -U $(PG_USER) -d $(PG_DB)

# psql avec le search_path positionne sur le schema applicatif.
# PGOPTIONS place search_path des l'ouverture de session (sans espace
# pour ne pas casser l'argument -e de docker compose exec).
PSQL_SCHEMA := $(COMPOSE) exec -T -e PGOPTIONS=--search_path=$(PG_SCHEMA) $(PG_SERVICE) \
	psql -v ON_ERROR_STOP=1 -U $(PG_USER) -d $(PG_DB)

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------
.PHONY: help
help: ## Affiche cette aide
	@echo LaborScope - cibles disponibles :
	@echo   make init          Initialise tout le projet : deps + base de donnees
	@echo   make install       Installe les dependances backend + frontend
	@echo   make install-back  Installe les dependances du backend
	@echo   make install-front Installe les dependances du frontend
	@echo   make db-up         Demarre PostgreSQL et attend qu'il soit pret
	@echo   make db-init       Cree le schema, les tables et peuple les referentiels
	@echo   make db-reset      Reinitialise la base de donnees
	@echo   make db-shell      Ouvre une console psql dans le conteneur
	@echo   make run-back      Lance l'API backend FastAPI/uvicorn
	@echo   make run-front     Lance le frontend Streamlit
	@echo   make up            Demarre toute la pile via Docker
	@echo   make down          Arrete tous les conteneurs
	@echo   make test          Lance tous les tests du backend
	@echo   make test-collecte Lance uniquement les tests de la collecte
	@echo   make cov-collecte  Couverture des modules de collecte
	@echo   make lint          Verifie le style du code
	@echo   make clean         Supprime les conteneurs et le volume PostgreSQL

# ---------------------------------------------------------------------
# Initialisation complete du projet
# ---------------------------------------------------------------------
.PHONY: init
init: install  ## Initialise tout le projet (dependances + base de donnees)
	@echo.
	@echo Projet initialise.
	@echo   Lancez l'API  : make run-back
	@echo   Lancez le web : make run-front

# ---------------------------------------------------------------------
# Dependances (uv)
# ---------------------------------------------------------------------
.PHONY: install install-back install-front
install: install-back install-front ## Installe les dependances backend + frontend

install-back: ## Installe les dependances du backend (uv)
	@echo Installation des dependances backend...
	uv sync --project backend

install-front: ## Installe les dependances du frontend (uv)
	@echo Installation des dependances frontend...
	uv sync --project frontend

# ---------------------------------------------------------------------
# Base de donnees
# ---------------------------------------------------------------------
.PHONY: db-up
db-up: ## Demarre PostgreSQL et attend qu'il soit pret (healthcheck)
	@echo Demarrage de PostgreSQL...
	$(COMPOSE) up -d --wait $(PG_SERVICE)
	@echo PostgreSQL est pret.

.PHONY: db-init
db-init: ## Cree le schema, les tables et peuple les referentiels
	@echo Creation du schema applicatif...
	$(PSQL) -c "CREATE SCHEMA IF NOT EXISTS $(PG_SCHEMA)"
	@echo Creation des tables depuis init_db.sql...
	$(PSQL_SCHEMA) -f /data/init_db.sql
	@echo Peuplement des referentiels depuis pop_referentiels.sql...
	$(PSQL_SCHEMA) -f /data/pop_referentiels.sql
	@echo Base de donnees initialisee - schema $(PG_SCHEMA).

.PHONY: db-reset
db-reset: db-up db-init ## Reinitialise la base (relance init_db.sql + referentiels)

.PHONY: db-shell
db-shell: ## Ouvre une console psql interactive dans le conteneur
	$(COMPOSE) exec -e PGOPTIONS=--search_path=$(PG_SCHEMA) $(PG_SERVICE) psql -U $(PG_USER) -d $(PG_DB)

# ---------------------------------------------------------------------
# Lancement des applications (en local via uv)
# ---------------------------------------------------------------------
.PHONY: run-back
run-back: ## Lance l'API backend (FastAPI/uvicorn)
	uv run --project backend python backend/src/main.py

.PHONY: run-front
run-front: ## Lance le frontend (Streamlit)
	cd frontend && uv run --project . streamlit run src/app.py

# ---------------------------------------------------------------------
# Docker (pile complete)
# ---------------------------------------------------------------------
.PHONY: up
up: ## Demarre toute la pile (backend + frontend + postgres) via Docker
	$(COMPOSE) up --build

.PHONY: down
down: ## Arrete tous les conteneurs
	$(COMPOSE) down

# ---------------------------------------------------------------------
# Qualite & tests
# ---------------------------------------------------------------------
.PHONY: test
test: ## Lance tous les tests du backend
	cd backend && uv run pytest

.PHONY: test-collecte
test-collecte: ## Lance uniquement les tests de la collecte
	cd backend && uv run pytest tests/service/test_collecte_service.py tests/service/test_parser_service.py tests/client/test_ilostat_client.py

.PHONY: cov-collecte
cov-collecte: ## Couverture des modules de collecte (rapport console + HTML)
	cd backend && uv run --extra dev coverage run -m pytest tests/service/test_collecte_service.py tests/service/test_parser_service.py tests/client/test_ilostat_client.py
	cd backend && uv run --extra dev coverage report

.PHONY: lint
lint: ## Verifie le style du code (ruff)
	uv run --project backend ruff check backend/src

.PHONY: clean
clean: ## Supprime les conteneurs et le volume de donnees PostgreSQL
	$(COMPOSE) down -v
