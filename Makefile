# =====================================================================
# LaborScope - Makefile d'orchestration du projet
# =====================================================================
# Cibles principales :
#   make init      -> initialise TOUT le projet (deps + base + 1er import)
#   make run-back  -> lance l'API backend (FastAPI)
#   make run-front -> lance le frontend (Streamlit)
#   make help      -> liste toutes les cibles disponibles
#
# La base PostgreSQL est utilisee EN LOCAL (psql direct), pas via Docker.
# Les parametres de connexion sont lus depuis le fichier .env.
# Docker reste disponible en option (cibles up / down / db-docker / clean).
#
# Compatible cmd.exe / PowerShell / Git Bash : aucune recette n'utilise
# de boucle ou de pipe shell. psql est appele via une URI de connexion
# (pas de prefixe PGPASSWORD=), ce qui fonctionne dans tous les shells.
# =====================================================================

# --- Parametres PostgreSQL (lus depuis .env, avec valeurs par defaut) -
-include .env

POSTGRES_HOST     ?= localhost
POSTGRES_PORT     ?= 5432
POSTGRES_USER     ?= user
POSTGRES_PASSWORD ?= password
POSTGRES_DATABASE ?= defaultdb
POSTGRES_SCHEMA   ?= project

# URI de connexion complete (le mot de passe est inclus : pas besoin de
# positionner PGPASSWORD, ce qui evite les problemes inter-shell).
PG_URI := postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DATABASE)

# Meme URI avec le search_path positionne des l'ouverture de session
# (utile pour une console interactive). Les caracteres sont encodes :
#   %20 = espace, %3D = '='  ->  options=-c search_path=<schema>
PG_URI_SCHEMA := $(PG_URI)?options=-c%20search_path%3D$(POSTGRES_SCHEMA)

# psql local, arret immediat a la premiere erreur SQL.
PSQL := psql "$(PG_URI)" -v ON_ERROR_STOP=1

# Positionne le search_path sur le schema applicatif. -c et -f s'executent
# dans la MEME session : le SET persiste donc pour le fichier charge ensuite.
SET_SCHEMA := -c "SET search_path TO $(POSTGRES_SCHEMA)"

# Docker (uniquement pour la pile complete, en option).
COMPOSE := docker compose

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------
.PHONY: help
help: ## Affiche cette aide
	@echo LaborScope - cibles disponibles :
	@echo   make init          Initialise tout : deps + base + 1er import
	@echo   make install       Installe les dependances backend + frontend
	@echo   make install-back  Installe les dependances du backend
	@echo   make install-front Installe les dependances du frontend
	@echo   make db-push       Cree le schema et les tables (init_db.sql)
	@echo   make db-load       Charge les referentiels (pop_referentiels.sql)
	@echo   make db-import     Importe les premieres donnees (collecte ILOSTAT)
	@echo   make db-init       Enchaine db-push + db-load (structure + referentiels)
	@echo   make db-reset      Reinitialise la base (db-init)
	@echo   make db-shell      Ouvre une console psql locale
	@echo   make run-back      Lance l'API backend FastAPI/uvicorn
	@echo   make run-front     Lance le frontend Streamlit
	@echo   make up            (option Docker) Demarre toute la pile
	@echo   make down          (option Docker) Arrete tous les conteneurs
	@echo   make db-docker     (option Docker) Demarre uniquement PostgreSQL
	@echo   make test          Lance tous les tests du backend
	@echo   make test-collecte Lance uniquement les tests de la collecte
	@echo   make cov-collecte  Couverture des modules de collecte
	@echo   make lint          Verifie le style du code
	@echo   make clean         (option Docker) Supprime conteneurs et volume

# ---------------------------------------------------------------------
# Initialisation complete du projet
# ---------------------------------------------------------------------
.PHONY: init
init: install db-init db-import ## Initialise tout (deps + base + premier import)
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
# Base de donnees (PostgreSQL local via psql)
# ---------------------------------------------------------------------
.PHONY: db-push
db-push: ## Cree le schema applicatif et les tables (push de init_db.sql)
	@echo Creation du schema $(POSTGRES_SCHEMA)...
	$(PSQL) -c "CREATE SCHEMA IF NOT EXISTS $(POSTGRES_SCHEMA)"
	@echo Creation des tables depuis data/init_db.sql...
	$(PSQL) $(SET_SCHEMA) -f data/init_db.sql
	@echo Structure de la base en place - schema $(POSTGRES_SCHEMA).

.PHONY: db-load
db-load: ## Charge les referentiels (pays, indicateurs, classifications)
	@echo Chargement des referentiels depuis data/pop_referentiels.sql...
	$(PSQL) $(SET_SCHEMA) -f data/pop_referentiels.sql
	@echo Referentiels charges.

.PHONY: db-import
db-import: ## Importe les premieres donnees via la collecte ILOSTAT
	@echo Import initial des observations (collecte ILOSTAT)...
	uv run --project backend python backend/src/service/collecte_service.py
	@echo Import initial termine.

.PHONY: db-init
db-init: db-push db-load ## Structure + referentiels (push + load)

.PHONY: db-reset
db-reset: db-init ## Reinitialise la base (relance init_db.sql + referentiels)

.PHONY: db-shell
db-shell: ## Ouvre une console psql locale interactive (search_path positionne)
	psql "$(PG_URI_SCHEMA)"

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
# Docker (pile complete) - OPTIONNEL
# ---------------------------------------------------------------------
.PHONY: up
up: ## (option) Demarre toute la pile (backend + frontend + postgres) via Docker
	$(COMPOSE) up --build

.PHONY: down
down: ## (option) Arrete tous les conteneurs
	$(COMPOSE) down

.PHONY: db-docker
db-docker: ## (option) Demarre uniquement PostgreSQL via Docker et attend qu'il soit pret
	$(COMPOSE) up -d --wait postgres

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
clean: ## (option) Supprime les conteneurs et le volume de donnees PostgreSQL
	$(COMPOSE) down -v
