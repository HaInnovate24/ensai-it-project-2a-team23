import sys
import os
import pytest
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from utils.config import load_environment_variables
load_environment_variables()

from dao.db_connection import DBConnection

def test_singleton_pattern():
    """Vérifie que DBConnection ne crée qu'une seule et unique instance."""
    db1 = DBConnection()
    db2 = DBConnection()
    
    assert db1 is db2
    
    assert db1.connection is db2.connection

def test_connection_is_active():
    """Vérifie que la connexion est bien établie et fonctionnelle."""
    db = DBConnection()
    conn = db.connection
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 AS numero;")
        result = cursor.fetchone()
        
        assert result is not None
        assert result['numero'] == 1

def test_real_dict_cursor_is_used():
    """Vérifie que le curseur renvoie bien des dictionnaires comme demandé."""
    db = DBConnection()
    with db.connection.cursor() as cursor:
        assert isinstance(cursor, RealDictCursor)