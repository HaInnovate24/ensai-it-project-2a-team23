"""Lanceur tout-en-un de LaborScope (appelé par ``make go``).

Pose une seule question (Docker ou local), puis enchaîne automatiquement :
installation des dépendances, initialisation de la base (schéma + référentiels),
collecte initiale ILOSTAT, création d'un administrateur par défaut
(admin / admin1234@) et démarrage SIMULTANÉ du backend et du frontend.

Script en bibliothèque standard uniquement : il orchestre les cibles ``make``
déjà testées (mode local) ou ``docker compose`` (mode Docker).
"""

from __future__ import annotations

import os
import subprocess
import sys

IS_WINDOWS = os.name == "nt"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADMIN_NOM = "admin"
ADMIN_MOT_DE_PASSE = "admin1234@"

# --- Couleurs ANSI (activées si la sortie est un terminal) -------------------
if IS_WINDOWS:
    os.system("")  # active le traitement des séquences ANSI sur Windows 10+

# Sécurité : on remplace les caractères non encodables au lieu de planter
# (sans changer l'encodage du terminal, donc sans dégrader l'affichage).
try:
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass

_COULEUR = sys.stdout.isatty()


def _c(code: str, texte: str) -> str:
    """Enrobe le texte dans une couleur ANSI si le terminal le supporte."""
    return f"\033[{code}m{texte}\033[0m" if _COULEUR else texte


def vert(t: str) -> str:
    return _c("92", t)


def cyan(t: str) -> str:
    return _c("96", t)


def jaune(t: str) -> str:
    return _c("93", t)


def gras(t: str) -> str:
    return _c("1", t)


def gris(t: str) -> str:
    return _c("90", t)


# --- Affichage ---------------------------------------------------------------

LARGEUR = 64


def cadre(lignes: list[str]) -> None:
    """Affiche une liste de lignes dans un cadre (ASCII, sans bordure droite).

    On évite les caractères Unicode de cadre et l'alignement d'une bordure droite :
    les chaînes contiennent des codes couleur ANSI dont la largeur fausserait le
    calcul, et la console Windows (cp1252) ne sait pas afficher les caractères de
    cadre Unicode.
    """
    bord = "+" + "-" * (LARGEUR - 2) + "+"
    print(cyan(bord))
    for ligne in lignes:
        print(cyan("|") + "  " + ligne)
    print(cyan(bord))


def banniere() -> None:
    """Affiche la bannière de lancement et les cibles make disponibles."""
    print()
    cadre(
        [
            gras(vert("LaborScope") + "  -  lancement tout-en-un"),
            gris("Analyse du marché du travail (ILOSTAT)"),
        ]
    )
    print()
    print(gras("  Commandes make utiles :"))
    options = [
        ("make go", "Tout faire et démarrer (cette commande)"),
        ("make init", "Initialise tout (deps + base + import)"),
        ("make admin", "Crée l'administrateur admin / admin1234@"),
        ("make run-back", "Lance seulement l'API backend"),
        ("make run-front", "Lance seulement le frontend"),
        ("make test", "Lance les tests du backend"),
        ("make up / down", "Pile complète via Docker"),
        ("make help", "Liste toutes les cibles"),
    ]
    for nom, desc in options:
        print("   " + jaune(nom.ljust(16)) + gris(desc))
    print()


# --- Exécution de commandes --------------------------------------------------


def etape(titre: str) -> None:
    """Annonce une étape."""
    print()
    print(gras(cyan(">> " + titre)))


def lancer(cmd: list[str], *, cwd: str | None = None, obligatoire: bool = True) -> bool:
    """Exécute une commande en affichant son appel. Renvoie True si succès.

    Si ``obligatoire`` est False, un échec n'interrompt pas le script.
    """
    print(gris("  $ " + " ".join(cmd)))
    resultat = subprocess.run(cmd, cwd=cwd or ROOT)
    if resultat.returncode != 0:
        if obligatoire:
            print(_c("91", f"  Échec de : {' '.join(cmd)}"))
            sys.exit(resultat.returncode)
        print(jaune(f"  Avertissement : {' '.join(cmd)} a échoué (étape optionnelle, on continue)."))
        return False
    return True


def demander_mode() -> str:
    """Demande à l'utilisateur le mode de lancement. Renvoie 'docker' ou 'local'."""
    print(gras("  Comment voulez-vous lancer l'application ?"))
    print("   " + jaune("[L]") + " Local   " + gris("(PostgreSQL local + uv, recommandé)"))
    print("   " + jaune("[D]") + " Docker  " + gris("(tout en conteneurs : docker compose)"))
    while True:
        try:
            choix = input(gras("  Votre choix [L/d] : ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(1)
        if choix in ("", "l", "local"):
            return "local"
        if choix in ("d", "docker"):
            return "docker"
        print(jaune("  Répondez par L (local) ou D (docker)."))


# --- Mode local --------------------------------------------------------------


def demarrer_local() -> None:
    """Initialise puis démarre backend + frontend en local."""
    etape("Installation des dépendances (backend + frontend)")
    lancer(["make", "install"])

    etape("Initialisation de la base (création + schéma + référentiels)")
    lancer(["make", "db-init"])

    etape("Import des données locales (backend/src/client/data/) et stockage en base")
    lancer(["make", "db-import"], obligatoire=False)

    etape("Création de l'administrateur par défaut")
    lancer(["make", "admin"])

    etape("Démarrage du backend et du frontend")
    _demarrer_serveurs_local()


def _demarrer_serveurs_local() -> None:
    """Lance l'API en arrière-plan puis le frontend au premier plan."""
    backend_cmd = ["uv", "run", "--project", "backend", "python", "backend/src/main.py"]
    frontend_cmd = ["uv", "run", "--project", ".", "streamlit", "run", "src/app.py"]
    frontend_cwd = os.path.join(ROOT, "frontend")

    print(gris("  $ " + " ".join(backend_cmd) + "   (nouvelle fenêtre / arrière-plan)"))
    if IS_WINDOWS:
        backend = subprocess.Popen(
            backend_cmd, cwd=ROOT, creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        backend = subprocess.Popen(backend_cmd, cwd=ROOT)

    _resume_demarrage("http://localhost:8501", "http://127.0.0.1:5000/docs")

    print(gris("  $ " + " ".join(frontend_cmd)))
    try:
        subprocess.run(frontend_cmd, cwd=frontend_cwd)
    except KeyboardInterrupt:
        pass
    finally:
        print()
        print(jaune("  Arrêt du frontend détecté : fermeture du backend..."))
        backend.terminate()


# --- Mode Docker -------------------------------------------------------------


def demarrer_docker() -> None:
    """Initialise et démarre toute la pile via docker compose."""
    compose = ["docker", "compose"]

    etape("Démarrage de PostgreSQL (conteneur) et attente qu'il soit prêt")
    lancer(compose + ["up", "-d", "--build", "--wait", "postgres"])

    etape("Initialisation de la base dans le conteneur (schéma + référentiels)")
    uri = "postgresql://user:password@localhost:5432/defaultdb"
    psql = compose + ["exec", "-T", "postgres", "psql", uri, "-v", "ON_ERROR_STOP=1"]
    lancer(psql + ["-c", "CREATE SCHEMA IF NOT EXISTS project"])
    lancer(psql + ["-c", "SET search_path TO project", "-f", "/data/init_db.sql"])
    lancer(psql + ["-c", "SET search_path TO project", "-f", "/data/pop_referentiels.sql"])

    etape("Démarrage du backend et du frontend (conteneurs)")
    lancer(compose + ["up", "-d", "--build", "backend", "frontend"])

    etape("Import des données locales + création de l'administrateur (dans le conteneur)")
    dans_backend = compose + ["exec", "-T", "backend", "uv", "run", "--project", "backend", "python"]
    lancer(dans_backend + ["backend/src/service/init_donnees.py"], obligatoire=False)
    lancer(dans_backend + ["backend/src/utils/creer_admin.py"])

    _resume_demarrage("http://localhost:8000", "http://localhost:5000/docs")
    print(gras("  Suivi des logs (Ctrl+C pour quitter, les conteneurs continuent) :"))
    print(gris("  $ docker compose logs -f"))
    subprocess.run(compose + ["logs", "-f"], cwd=ROOT)


# --- Résumé ------------------------------------------------------------------


def _resume_demarrage(url_front: str, url_docs: str) -> None:
    """Affiche le récapitulatif d'accès (URLs + identifiants admin)."""
    print()
    cadre(
        [
            gras(vert("Application prête !")),
            "",
            "Frontend  : " + cyan(url_front),
            "API (docs): " + cyan(url_docs),
            "",
            gras("Compte administrateur :"),
            "  identifiant : " + jaune(ADMIN_NOM),
            "  mot de passe: " + jaune(ADMIN_MOT_DE_PASSE),
        ]
    )
    print()


def main() -> int:
    """Point d'entrée : affiche la bannière, demande le mode, lance tout."""
    banniere()
    mode = demander_mode()
    if mode == "docker":
        demarrer_docker()
    else:
        demarrer_local()
    return 0


if __name__ == "__main__":
    sys.exit(main())
