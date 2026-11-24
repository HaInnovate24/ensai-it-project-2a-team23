# Frontend - LaborScope Dashboard

**English** | [Français](README.fr.md)

This is the graphical user interface of the application. It is an interactive web
dashboard built with **Streamlit**, designed to consume the backend FastAPI API and
present the labour-market analyses (trends over time, country comparisons, world map,
PDF reports).

## 🚀 Run the application

- Install all dependencies: `uv sync --project frontend --all-extras`

Then move into the *frontend* folder to launch it:

- `cd frontend`
- `uv run --project . streamlit run src/app.py`

The interface opens by default at `http://localhost:8501` and talks to the backend
through the `BACKEND_URL` defined in the root `.env` file. Make sure the backend API
(`make run-back`) is running first.

## 🏛️ Architecture

The frontend follows a modular structure that separates the UI views from the API
interaction logic:

- **Views** (`vues/`) : the individual pages of the dashboard
  (`home.py`, `login.py`, `analyse_temporelle.py`, `comparaison_pays.py`,
  `comparaison_multi.py`, `carte_mondiale.py`, `admin.py`).
- **API client** (`utils/api_client.py`) : centralized logic for communicating with
  the FastAPI backend.
- **Security** (`utils/auth_guard.py`) : session security and token validation.
- **UI toolkit** (`utils/ui.py`) : shared design system (headers, cards, charts styling,
  colour palette).
- **Reference data** (`utils/referentiels.py`) : cached lookups (countries, indicators,
  classifications) fetched from the API.
- **PDF reports** (`utils/rapport_pdf.py`) : client-side assembly of downloadable PDF
  reports.
- **Utilities** (`utils/`) : helpers for logging (`log_init.py`), environment variables
  (`env_variables.py`), map centroids (`centroides_pays.py`).

### Project structure

```text
frontend/
├── Dockerfile                 # Container image for the dashboard
├── logging_config.yml         # Structured logging configuration
├── pyproject.toml             # Project metadata & dependencies (uv)
├── uv.lock                    # Pinned dependency versions
│
└── src/
    ├── app.py                 # Streamlit entry point : navigation and layout
    ├── vues/                  # Dashboard pages
    │   ├── home.py            #   Landing page
    │   ├── login.py           #   Sign in / sign up
    │   ├── analyse_temporelle.py  # Employment trends over time (F3)
    │   ├── comparaison_pays.py    # Country comparison (F4)
    │   ├── comparaison_multi.py   # Multi-indicator comparison (F5)
    │   ├── carte_mondiale.py      # World map view
    │   └── admin.py           #   Administration (imports, accounts, journal)
    └── utils/                 # Cross-cutting tools
        ├── api_client.py      #   HTTP client for the backend API
        ├── auth_guard.py      #   Session security and token validation
        ├── ui.py              #   Shared design system
        ├── referentiels.py    #   Cached reference lookups
        ├── rapport_pdf.py     #   PDF report builder
        ├── centroides_pays.py #   Country centroids for the map
        ├── env_variables.py   #   Environment configuration
        └── log_init.py        #   Logging setup
```

## ⚒️ Debugging & Logs

### Logs

The frontend maintains its own logging system to track user interactions and API
communication errors.

- Logs are written to the `frontend/logs/` directory.
- The logging format is configured via `logging_config.yml`.

### Code quality

The **format on save** with [Ruff](https://docs.astral.sh/ruff/) is enabled by default
in the workspace (cf. *.vscode/settings.json*).

To do it manually from the repository root:

- consistent code style: `uv run --project frontend ruff format frontend/`
- find and fix issues: `uv run --project frontend ruff check --fix frontend/`
