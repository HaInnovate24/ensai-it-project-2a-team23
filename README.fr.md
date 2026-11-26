# LaborScope

[English](README.md) | **Français**

> 🎥 **Une vidéo de guide est accessible ici :** https://drive.google.com/file/d/1MH8HUZVSFC-x1t9fRpUtF36HegpH6WKe/view?usp=sharing

Application d'analyse du marché du travail à partir des données ouvertes
[ILOSTAT](https://ilostat.ilo.org/). Elle collecte des indicateurs d'emploi,
les stocke dans PostgreSQL, et propose des analyses (évolutions, comparaisons
entre pays, carte) via une API **FastAPI** et une interface **Streamlit**.

- **Backend** : API REST FastAPI (collecte, stockage, analyses, comptes, rapports PDF).
- **Frontend** : interface web Streamlit.
- **Base de données** : PostgreSQL (schéma applicatif dédié).

---

## Démarrage rapide (une seule commande)

Une fois les prérequis installés (voir section 1), depuis la racine du projet :

```bash
make go
```

`make go` demande si vous voulez lancer avec **Docker** ou **en local**, puis fait tout en une
fois : installe les dépendances, initialise la base (schéma + référentiels), importe les
observations **depuis les fichiers CSV locaux** de `backend/src/client/data/` (hors ligne,
aucun appel réseau), crée un administrateur par défaut, et démarre le backend **et** le
frontend ensemble.

Compte administrateur par défaut :

| Identifiant | Mot de passe |
|-------------|--------------|
| `admin`     | `admin1234@` |

> En mode **Docker**, `make go` provisionne PostgreSQL automatiquement. En mode **local**, un
> serveur PostgreSQL doit déjà tourner (voir section 1), ou démarrez-en un avec `make db-docker`.

Les sections ci-dessous détaillent chaque étape si vous préférez les lancer manuellement.

---

## 1. Prérequis

Installez ces outils avant de commencer :

| Outil | Version | Rôle |
|-------|---------|------|
| [Python](https://www.python.org/) | **3.13+** | Exécution du backend et du frontend |
| [uv](https://docs.astral.sh/uv/) | récente | Gestionnaire de dépendances et d'environnements |
| [PostgreSQL](https://www.postgresql.org/) | 14+ | **Serveur** de base de données (le client `psql` est optionnel — utilisé seulement par `make db-shell`) |
| [Make](https://www.gnu.org/software/make/) | — | Orchestration des commandes (`make init`, etc.) |
| Git | — | Clonage du dépôt |

> La mise en place de la base (`make db-push` / `db-load`) exécute les fichiers SQL via
> Python (`psycopg2`) : le client en ligne de commande `psql` n'a donc **pas** besoin d'être
> installé. Pas de serveur PostgreSQL en local ? Démarrez-en un avec `make db-docker`.

> **Note Windows** : le `Makefile` est compatible `cmd.exe`, PowerShell et Git Bash.
> Assurez-vous que `uv` et `make` sont accessibles depuis le terminal.
> `make` peut s'installer via [Chocolatey](https://chocolatey.org/) (`choco install make`)
> ou est fourni avec Git Bash / MSYS2.

Une instance PostgreSQL doit être **démarrée et accessible** (en local par défaut).
Si vous n'avez pas PostgreSQL installé, voir la [section Docker](#6-alternative-tout-en-docker).

---

## 2. Récupération du projet

```bash
git clone <url-du-depot>
cd ensai-it-project-2a-team23
```

---

## 3. Configuration (`.env`)

Le projet lit sa configuration depuis un fichier `.env` à la racine. Créez-le  
en copiant le modèle ci-dessous et en adaptant les valeurs à votre installation  
PostgreSQL : 

A adapter en fonction des vos informations de connexion

```dotenv
# --- Base de données PostgreSQL ---
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=defaultdb
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_SCHEMA=project

# --- Sécurité (jetons d'authentification) ---
JWT_SECRET_KEY=changez-moi-par-une-chaine-longue-et-aleatoire

# --- Serveur API (backend) ---
UVICORN_HOST=0.0.0.0
UVICORN_PORT=5000

# --- Accès à l'API depuis le frontend ---
BACKEND_URL=http://localhost:5000
BACKEND_TIMEOUT=5

# --- Divers ---
ELO_K_FACTOR=32
```

Points importants :

- `POSTGRES_USER` doit pouvoir **créer une base** (`CREATEDB`) pour que `make init`
crée automatiquement `POSTGRES_DATABASE` si elle n'existe pas. Sinon, créez la base
manuellement au préalable.
- `POSTGRES_SCHEMA` est le schéma applicatif (créé automatiquement) — pas besoin de
le créer à la main.
- Changez `JWT_SECRET_KEY` par une valeur secrète (utilisée pour signer les jetons).

---

## 4. Initialisation en une commande

Depuis la racine du projet :

```bash
make init
```

Cette commande fait **tout** :

1. `install` — installe les dépendances du backend et du frontend (via `uv`).
2. `db-create` — crée la base PostgreSQL `POSTGRES_DATABASE` si elle n'existe pas.
3. `db-push` — crée le schéma applicatif et les tables (`data/init_db.sql`).
4. `db-load` — charge les référentiels : pays, indicateurs, classifications

   (`data/pop_referentiels.sql`).
5. `db-import` — importe les observations de **tous les indicateurs actifs** du référentiel

   depuis les fichiers CSV locaux de `backend/src/client/data/` (hors ligne, aucun appel
   réseau), soit :
   - `EMP_TEMP_SEX_OCU_NB` — Emploi par sexe et profession ;
   - `POP_XWAP_SEX_AGE_NB` — Population en âge de travailler par sexe et âge.

À la fin, la base est entièrement initialisée (structure + référentiels + observations).

> Les observations sont lues depuis les fichiers CSV fournis dans `backend/src/client/data/` :
> l'import est reproductible et fonctionne sans connexion Internet.

---

## 5. Lancer l'application

Dans deux terminaux séparés, à la racine du projet :

```bash
# Terminal 1 — API backend (FastAPI/uvicorn)
make run-back
```

L'API démarre sur `http://127.0.0.1:5000`. Documentation interactive : **http://127.0.0.1:5000/docs**.

```bash
# Terminal 2 — interface web (Streamlit)
make run-front
```

Le frontend s'ouvre dans le navigateur (par défaut `http://localhost:8501`) et
communique avec l'API via `BACKEND_URL`.

### Créer un compte et un administrateur

- Les utilisateurs se créent via la page **Inscription** de l'interface (compte
standard).
- Pour obtenir un **administrateur** (accès à la page d'administration, imports,
gestion des comptes), promouvez un compte existant directement en base :
  ```bash
  make db-shell
  ```

  puis, dans la console `psql` :
  ```sql
  UPDATE utilisateur SET role = 'admin' WHERE nom_utilisateur = '<votre_nom>';
  ```

---

## 6. Alternative : tout en Docker

Si vous préférez ne rien installer en local (PostgreSQL inclus) :

```bash
make up      # construit et démarre backend + frontend + PostgreSQL
make down    # arrête les conteneurs
make clean   # arrête et supprime le volume de données PostgreSQL
```

Vous pouvez aussi ne lancer que la base de données via Docker, puis travailler en
local pour le reste :

```bash
make db-docker   # démarre uniquement PostgreSQL (et attend qu'il soit prêt)
```

---

## 7. Commandes `make` utiles

| Commande | Description |
|----------|-------------|
| `make go` | Une seule commande : demande Docker/local, initialise tout, crée l'admin, démarre back + front |
| `make admin` | Crée (ou réinitialise) l'administrateur par défaut `admin` / `admin1234@` |
| `make init` | Initialise tout (dépendances + base + référentiels + observations) |
| `make install` | Installe les dépendances backend + frontend |
| `make db-create` | Crée la base PostgreSQL si elle n'existe pas |
| `make db-push` | Crée le schéma et les tables |
| `make db-load` | Charge les référentiels (pays, indicateurs, classifications) |
| `make db-import` | Importe les observations depuis les CSV locaux (`backend/src/client/data/`) vers la base |
| `make db-init` | Enchaîne `db-create` + `db-push` + `db-load` |
| `make db-reset` | Réinitialise la structure et les référentiels |
| `make db-shell` | Ouvre une console `psql` (schéma positionné) |
| `make run-back` | Lance l'API backend |
| `make run-front` | Lance le frontend Streamlit |
| `make test` | Lance tous les tests du backend |
| `make cov` | Couverture des tests (console + rapport HTML) |
| `make lint` | Vérifie le style du code (ruff) |
| `make help` | Liste toutes les cibles disponibles |

---

## 8. Dépannage

| Symptôme | Cause probable / solution |
|----------|---------------------------|
| `psql: command not found` | Concerne uniquement `make db-shell` (les autres commandes n'ont pas besoin de `psql`). Installez le client PostgreSQL, ou inspectez la base avec `docker compose exec postgres psql ...`. |
| `CreateProcess(...) psql ... failed` (Windows) | Même cause : `psql` n'est pas installé. Les commandes `make db-push` / `db-load` n'en ont plus besoin — vérifiez que vous avez la dernière version du `Makefile`. |
| `Impossible de se connecter à la base de maintenance 'postgres'` | L'utilisateur ne peut pas créer de base ou PostgreSQL n'est pas démarré. Vérifiez `.env` et que le serveur tourne, ou créez `POSTGRES_DATABASE` à la main. |
| `password authentication failed` | Identifiants `POSTGRES_USER` / `POSTGRES_PASSWORD` incorrects dans `.env`. |
| La collecte ne renvoie aucune donnée | Lancez `make db-load` avant `make db-import` (les indicateurs doivent exister dans le référentiel). |
| Le frontend n'atteint pas l'API | Vérifiez que `make run-back` tourne et que `BACKEND_URL` pointe vers la bonne adresse/port. |

---

## 9. Structure du dépôt

```
.
├── backend/          # API FastAPI (dao, service, controller, business_object, utils)
│   ├── src/
│   └── tests/
├── frontend/         # Interface Streamlit
│   └── src/
├── data/             # Scripts SQL (init_db.sql, pop_referentiels.sql)
├── docker-compose.yml
├── Makefile          # Orchestration (make init, run-back, run-front, ...)
└── README.md
```

Documentation détaillée du backend : [`backend/README.md`](backend/README.md).
