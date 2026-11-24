"""Configuration pytest commune : aucun service externe n'est contacté.

La connexion PostgreSQL (``psycopg2.connect``) est remplacée par un mock dès le
chargement de ce fichier — donc avant l'import des modules de test — pour que :

  * les DAO n'ouvrent jamais de vraie connexion à la base ;
  * les controllers qui instancient leurs services au moment de l'import ne
    nécessitent pas une base PostgreSQL en marche.

Les tests DAO configurent le curseur mock via la fixture ``curseur`` (valeurs
renvoyées par ``fetchone`` / ``fetchall`` / ``rowcount``). Ainsi ``make test``
fonctionne sur n'importe quelle machine, sans base de données.
"""

from unittest.mock import MagicMock

import psycopg2
import pytest

from utils.config import load_environment_variables

load_environment_variables()

# --- Mock global de la connexion PostgreSQL (appliqué dès l'import) ----------

# Curseur unique partagé par tous les DAO. Chaque test le réinitialise via la
# fixture autouse ``_reinitialiser_curseur`` : pas de fuite d'état entre tests.
_curseur = MagicMock(name="curseur_bd")


def _nouveau_contexte_curseur(*_args, **_kwargs):
    """Simule ``with conn.cursor() as cursor:`` en renvoyant toujours le même curseur."""
    contexte = MagicMock(name="contexte_curseur")
    contexte.__enter__.return_value = _curseur
    contexte.__exit__.return_value = False
    return contexte


_connexion = MagicMock(name="connexion_bd")
_connexion.cursor.side_effect = _nouveau_contexte_curseur

# Mémorise les paramètres passés à psycopg2.connect (vérifiés par test_db_connection_dao).
_appels_connect: list[dict] = []


def _fausse_connexion(*_args, **kwargs):
    """Remplace psycopg2.connect : ne contacte aucune base, renvoie le mock."""
    _appels_connect.append(kwargs)
    return _connexion


# Patch appliqué dès le chargement du conftest (donc avant la collecte des tests).
psycopg2.connect = _fausse_connexion


@pytest.fixture(autouse=True)
def _reinitialiser_curseur():
    """Remet le curseur mock à zéro avant chaque test (aucune fuite entre tests)."""
    _curseur.reset_mock(return_value=True, side_effect=True)
    _curseur.fetchone.return_value = None
    _curseur.fetchall.return_value = []
    _curseur.rowcount = 0
    yield


@pytest.fixture
def curseur():
    """Curseur mock : les tests DAO y fixent fetchone / fetchall / rowcount."""
    return _curseur


@pytest.fixture
def connexion():
    """Connexion mock (pour vérifier par exemple les appels à commit)."""
    return _connexion


@pytest.fixture
def appels_connect():
    """Liste des kwargs passés à psycopg2.connect (test de DBConnection)."""
    return _appels_connect
