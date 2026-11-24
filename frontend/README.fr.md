# Frontend - Tableau de bord LaborScope

[English](README.md) | **Français**

Il s'agit de l'interface graphique de l'application. C'est un tableau de bord web
interactif construit avec **Streamlit**, conçu pour consommer l'API FastAPI du backend
et présenter les analyses du marché du travail (évolutions dans le temps, comparaisons
entre pays, carte mondiale, rapports PDF).

## 🚀 Lancer l'application

- Installer toutes les dépendances : `uv sync --project frontend --all-extras`

Placez-vous ensuite dans le dossier *frontend* pour le lancer :

- `cd frontend`
- `uv run --project . streamlit run src/app.py`

L'interface s'ouvre par défaut sur `http://localhost:8501` et dialogue avec le backend
via le `BACKEND_URL` défini dans le fichier `.env` à la racine. Assurez-vous que l'API
backend (`make run-back`) tourne au préalable.

## 🏛️ Architecture

Le frontend suit une structure modulaire qui sépare les vues de l'interface de la
logique d'interaction avec l'API :

- **Vues** (`vues/`) : les pages individuelles du tableau de bord
  (`home.py`, `login.py`, `analyse_temporelle.py`, `comparaison_pays.py`,
  `comparaison_multi.py`, `carte_mondiale.py`, `admin.py`).
- **Client API** (`utils/api_client.py`) : logique centralisée de communication avec
  le backend FastAPI.
- **Sécurité** (`utils/auth_guard.py`) : sécurité de session et validation des jetons.
- **Boîte à outils UI** (`utils/ui.py`) : système de design partagé (en-têtes, cartes,
  styles de graphiques, palette de couleurs).
- **Référentiels** (`utils/referentiels.py`) : listes mises en cache (pays, indicateurs,
  classifications) récupérées depuis l'API.
- **Rapports PDF** (`utils/rapport_pdf.py`) : assemblage côté client des rapports PDF
  téléchargeables.
- **Utilitaires** (`utils/`) : aides pour la journalisation (`log_init.py`), les
  variables d'environnement (`env_variables.py`), les centroïdes des pays
  (`centroides_pays.py`).

### Structure du projet

```text
frontend/
├── Dockerfile                 # Image conteneur du tableau de bord
├── logging_config.yml         # Configuration de la journalisation structurée
├── pyproject.toml             # Métadonnées du projet & dépendances (uv)
├── uv.lock                    # Versions figées des dépendances
│
└── src/
    ├── app.py                 # Point d'entrée Streamlit : navigation et mise en page
    ├── vues/                  # Pages du tableau de bord
    │   ├── home.py            #   Page d'accueil
    │   ├── login.py           #   Connexion / inscription
    │   ├── analyse_temporelle.py  # Évolution de l'emploi dans le temps (F3)
    │   ├── comparaison_pays.py    # Comparaison entre pays (F4)
    │   ├── comparaison_multi.py   # Comparaison multi-indicateurs (F5)
    │   ├── carte_mondiale.py      # Vue carte mondiale
    │   └── admin.py           #   Administration (imports, comptes, journal)
    └── utils/                 # Outils transversaux
        ├── api_client.py      #   Client HTTP vers l'API backend
        ├── auth_guard.py      #   Sécurité de session et validation des jetons
        ├── ui.py              #   Système de design partagé
        ├── referentiels.py    #   Référentiels mis en cache
        ├── rapport_pdf.py     #   Générateur de rapports PDF
        ├── centroides_pays.py #   Centroïdes des pays pour la carte
        ├── env_variables.py   #   Configuration de l'environnement
        └── log_init.py        #   Mise en place de la journalisation
```

## ⚒️ Débogage & Logs

### Logs

Le frontend maintient son propre système de journalisation pour suivre les interactions
utilisateur et les erreurs de communication avec l'API.

- Les logs sont écrits dans le dossier `frontend/logs/`.
- Le format de journalisation est configuré via `logging_config.yml`.

### Qualité du code

Le **formatage à la sauvegarde** avec [Ruff](https://docs.astral.sh/ruff/) est activé par
défaut dans l'espace de travail (cf. *.vscode/settings.json*).

Pour le faire manuellement depuis la racine du dépôt :

- style de code cohérent : `uv run --project frontend ruff format frontend/`
- détecter et corriger les problèmes : `uv run --project frontend ruff check --fix frontend/`
