"""Tests unitaires de la recherche d'observations dans le DAO."""

import pytest

from business_object.enums import Sexe
from business_object.observation import Observation
from dao.observation_dao import ObservationDao


class FauxCurseur:
    """Curseur qui mémorise la requête sans ouvrir de connexion PostgreSQL."""

    def __init__(self, rows):
        self.rows = rows
        self.requete = None
        self.parametres = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, requete, parametres):
        self.requete = requete
        self.parametres = parametres

    def fetchall(self):
        return self.rows


class FauxConnexion:
    """Connexion factice fournissant le curseur préparé."""

    def __init__(self, rows):
        self.faux_curseur = FauxCurseur(rows)

    def cursor(self):
        return self.faux_curseur


def creer_dao(rows=None):
    """Construit un DAO sans lancer DBConnection."""
    dao = object.__new__(ObservationDao)
    dao.conn = FauxConnexion(rows or [])
    return dao


def test_rechercher_construit_une_requete_parametree_et_convertit_les_lignes():
    ligne = {
        "id": 7,
        "code_indicateur": "EMP",
        "code_pays": "FRA",
        "periode": "2024",
        "valeur": 12.5,
        "sexe": "femme",
        "code_classification": None,
        "import_id": None,
        "source": "ILOSTAT",
        "date_import": None,
    }
    dao = creer_dao([ligne])

    resultat = dao.rechercher(code_pays="FRA", sexe=Sexe.FEMME)

    assert len(resultat) == 1
    assert isinstance(resultat[0], Observation)
    assert resultat[0].id == ligne["id"]
    assert resultat[0].code_pays == ligne["code_pays"]
    assert resultat[0].sexe == Sexe.FEMME
    assert dao.conn.faux_curseur.parametres == ("FRA", "femme")
    assert "code_pays = %s" in dao.conn.faux_curseur.requete
    assert "sexe = %s" in dao.conn.faux_curseur.requete
    assert "ORDER BY code_indicateur, code_pays, periode, id" in dao.conn.faux_curseur.requete


def test_rechercher_interprete_none_comme_is_null():
    dao = creer_dao()

    resultat = dao.rechercher(code_classification=None)

    assert resultat == []
    assert "code_classification IS NULL" in dao.conn.faux_curseur.requete
    assert dao.conn.faux_curseur.parametres == ()


def test_rechercher_sans_filtre_retourne_toutes_les_observations():
    dao = creer_dao()

    assert dao.rechercher() == []
    assert dao.conn.faux_curseur.requete.startswith("SELECT * FROM observation")
    assert " WHERE " not in dao.conn.faux_curseur.requete


def test_rechercher_refuse_un_filtre_inconnu():
    dao = creer_dao()

    with pytest.raises(ValueError, match="recherche inconnu"):
        dao.rechercher(**{"; DROP TABLE observation": "FRA"})
