"""Tests de DBConnection : singleton et paramètres de connexion (sans vraie base).

La connexion psycopg2 est mockée par le conftest racine : on vérifie ici le
comportement de DBConnection (singleton, options passées à psycopg2.connect)
sans contacter de base de données.
"""

from psycopg2.extras import RealDictCursor

from dao.db_connection import DBConnection
from utils.singleton import Singleton


def test_singleton_pattern():
    """DBConnection ne crée qu'une seule et unique instance partagée."""
    db1 = DBConnection()
    db2 = DBConnection()

    assert db1 is db2
    assert db1.connection is db2.connection


def test_connection_est_utilisable(curseur):
    """La connexion exposée permet d'exécuter une requête et d'en lire le résultat."""
    curseur.fetchone.return_value = {"numero": 1}

    db = DBConnection()
    with db.connection.cursor() as cursor:
        cursor.execute("SELECT 1 AS numero;")
        resultat = cursor.fetchone()

    assert resultat is not None
    assert resultat["numero"] == 1


def test_connexion_utilise_real_dict_cursor(appels_connect):
    """DBConnection demande bien un RealDictCursor et positionne le search_path."""
    # On force une nouvelle construction pour capturer les paramètres de connexion.
    Singleton._instances.pop(DBConnection, None)
    DBConnection()

    kwargs = appels_connect[-1]
    assert kwargs["cursor_factory"] is RealDictCursor
    assert "search_path" in kwargs["options"]
