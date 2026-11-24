# LaborScope

**English** | [Français](README.fr.md)

A labour-market analysis application built on the [ILOSTAT](https://ilostat.ilo.org/)
open data. It collects employment indicators, stores them in PostgreSQL, and provides
analyses (trends, country comparisons, map) through a **FastAPI** API and a
**Streamlit** interface.

- **Backend**: FastAPI REST API (collection, storage, analyses, accounts, PDF reports).
- **Frontend**: Streamlit web interface.
- **Database**: PostgreSQL (dedicated application schema).

---

## Quick start (one command)

Once the prerequisites are installed (see section 1), from the project root:

```bash
make go
```

`make go` asks whether to run with **Docker** or **locally**, then does everything in one
shot: installs the dependencies, initializes the database (schema + reference data), imports
the observations **from the local CSV files** in `backend/src/client/data/` (offline, no
network call), creates a default administrator, and starts the backend **and** the frontend
together.

Default administrator account:

| Username | Password |
|----------|-------------|
| `admin`  | `admin1234@` |

> In **Docker** mode, `make go` provisions PostgreSQL automatically. In **local** mode, a
> PostgreSQL server must already be running (see section 1), or start one with `make db-docker`.

The sections below detail each step if you prefer to run them manually.

---

## 1. Prerequisites

Install these tools before you start:

| Tool | Version | Role |
|------|---------|------|
| [Python](https://www.python.org/) | **3.13+** | Runs the backend and the frontend |
| [uv](https://docs.astral.sh/uv/) | recent | Dependency and environment manager |
| [PostgreSQL](https://www.postgresql.org/) | 14+ | Database **server** (the `psql` client is optional — only used by `make db-shell`) |
| [Make](https://www.gnu.org/software/make/) | — | Command orchestration (`make init`, etc.) |
| Git | — | Cloning the repository |

> The database setup (`make db-push` / `db-load`) runs the SQL files through Python
> (`psycopg2`), so the `psql` command-line client does **not** need to be installed.
> No PostgreSQL server locally? Start one in Docker with `make db-docker`.

> **Windows note**: the `Makefile` is compatible with `cmd.exe`, PowerShell and Git Bash.
> Make sure `uv` and `make` are reachable from the terminal.
> `make` can be installed via [Chocolatey](https://chocolatey.org/) (`choco install make`)
> or comes with Git Bash / MSYS2.

A PostgreSQL instance must be **started and reachable** (local by default).
If you do not have PostgreSQL installed, see the [Docker section](#6-alternative-all-in-docker).

---

## 2. Getting the project

```bash
git clone <repository-url>
cd ensai-it-project-2a-team23
```

---

## 3. Configuration (`.env`)

The project reads its configuration from a `.env` file at the root. Create it by
copying the template below and adapting the values to your PostgreSQL installation:

Adapt it to your own connection details.

```dotenv
# --- PostgreSQL database ---
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=defaultdb
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_SCHEMA=project

# --- Security (authentication tokens) ---
JWT_SECRET_KEY=change-me-to-a-long-random-string

# --- API server (backend) ---
UVICORN_HOST=0.0.0.0
UVICORN_PORT=5000

# --- API access from the frontend ---
BACKEND_URL=http://localhost:5000
BACKEND_TIMEOUT=5

# --- Miscellaneous ---
ELO_K_FACTOR=32
```

Important points:

- `POSTGRES_USER` must be able to **create a database** (`CREATEDB`) so that `make init`
  automatically creates `POSTGRES_DATABASE` if it does not exist. Otherwise, create the
  database manually beforehand.
- `POSTGRES_SCHEMA` is the application schema (created automatically) — no need to create
  it by hand.
- Change `JWT_SECRET_KEY` to a secret value (used to sign the tokens).

---

## 4. One-command initialization

From the project root:

```bash
make init
```

This command does **everything**:

1. `install` — installs the backend and frontend dependencies (via `uv`).
2. `db-create` — creates the PostgreSQL database `POSTGRES_DATABASE` if it does not exist.
3. `db-push` — creates the application schema and the tables (`data/init_db.sql`).
4. `db-load` — loads the reference data: countries, indicators, classifications

   (`data/pop_referentiels.sql`).
5. `db-import` — imports the observations of **all active indicators** from the local CSV
   files in `backend/src/client/data/` (offline, no network call), namely:
   - `EMP_TEMP_SEX_OCU_NB` — Employment by sex and occupation;
   - `POP_XWAP_SEX_AGE_NB` — Working-age population by sex and age.

At the end, the database is fully initialized (structure + reference data + observations).

> The observations are read from the CSV files bundled in `backend/src/client/data/`, so the
> import is reproducible and works without an Internet connection.

---

## 5. Running the application

In two separate terminals, from the project root:

```bash
# Terminal 1 — backend API (FastAPI/uvicorn)
make run-back
```

The API starts on `http://127.0.0.1:5000`. Interactive documentation: **http://127.0.0.1:5000/docs**.

```bash
# Terminal 2 — web interface (Streamlit)
make run-front
```

The frontend opens in the browser (by default `http://localhost:8501`) and
communicates with the API via `BACKEND_URL`.

### Create an account and an administrator

- Users are created via the **Sign up** page of the interface (standard account).
- To obtain an **administrator** (access to the admin page, imports, account
  management), promote an existing account directly in the database:
  ```bash
  make db-shell
  ```

  then, in the `psql` console:
  ```sql
  UPDATE utilisateur SET role = 'admin' WHERE nom_utilisateur = '<your_name>';
  ```

---

## 6. Alternative: all in Docker

If you prefer not to install anything locally (PostgreSQL included):

```bash
make up      # builds and starts backend + frontend + PostgreSQL
make down    # stops the containers
make clean   # stops and removes the PostgreSQL data volume
```

You can also run only the database via Docker, then work locally for the rest:

```bash
make db-docker   # starts only PostgreSQL (and waits until it is ready)
```

---

## 7. Useful `make` commands

| Command | Description |
|---------|-------------|
| `make go` | One command: asks Docker/local, initializes everything, creates the admin, starts back + front |
| `make admin` | Creates (or resets) the default administrator `admin` / `admin1234@` |
| `make init` | Initializes everything (dependencies + database + reference data + observations) |
| `make install` | Installs the backend + frontend dependencies |
| `make db-create` | Creates the PostgreSQL database if it does not exist |
| `make db-push` | Creates the schema and the tables |
| `make db-load` | Loads the reference data (countries, indicators, classifications) |
| `make db-import` | Imports the observations from the local CSV files (`backend/src/client/data/`) into the database |
| `make db-init` | Chains `db-create` + `db-push` + `db-load` |
| `make db-reset` | Resets the structure and the reference data |
| `make db-shell` | Opens a `psql` console (schema set) |
| `make run-back` | Starts the backend API |
| `make run-front` | Starts the Streamlit frontend |
| `make test` | Runs all the backend tests |
| `make cov` | Test coverage (console + HTML report) |
| `make lint` | Checks the code style (ruff) |
| `make help` | Lists all available targets |

---

## 8. Troubleshooting

| Symptom | Likely cause / solution |
|---------|-------------------------|
| `psql: command not found` | Only affects `make db-shell` (the other commands do not need `psql`). Install the PostgreSQL client, or inspect the database with `docker compose exec postgres psql ...`. |
| `CreateProcess(...) psql ... failed` (Windows) | Same cause: `psql` is not installed. The `make db-push` / `db-load` commands no longer need it — make sure you are on the latest version of the `Makefile`. |
| `Unable to connect to the maintenance database 'postgres'` | The user cannot create a database or PostgreSQL is not started. Check `.env` and that the server is running, or create `POSTGRES_DATABASE` by hand. |
| `password authentication failed` | Incorrect `POSTGRES_USER` / `POSTGRES_PASSWORD` credentials in `.env`. |
| Collection returns no data | Run `make db-load` before `make db-import` (the indicators must exist in the reference data). |
| The frontend cannot reach the API | Check that `make run-back` is running and that `BACKEND_URL` points to the correct address/port. |

---

## 9. Repository structure

```
.
├── backend/          # FastAPI API (dao, service, controller, business_object, utils)
│   ├── src/
│   └── tests/
├── frontend/         # Streamlit interface
│   └── src/
├── data/             # SQL scripts (init_db.sql, pop_referentiels.sql)
├── docker-compose.yml
├── Makefile          # Orchestration (make init, run-back, run-front, ...)
└── README.md
```

Detailed backend documentation: [`backend/README.md`](backend/README.md).
