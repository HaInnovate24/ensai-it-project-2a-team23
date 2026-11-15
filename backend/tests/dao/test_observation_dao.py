"""Tests unitaires de la recherche d'observations dans le DAO."""

import pytest

from business_object.enums import Sexe
from business_object.observation import Observation
from dao import observation_dao as observation_dao_module
from dao.observation_dao import ObservationDao

LIGNE_EXEMPLE = {
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


class FauxCurseur:
    """Curseur qui mémorise la requête sans ouvrir de connexion PostgreSQL."""

    def __init__(self, rows, rowcount=0):
        self.rows = rows
        self.requete = None
        self.parametres = None
        self.rowcount = rowcount

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, requete, parametres=None):
        self.requete = requete
        self.parametres = parametres

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FauxConnexion:
    """Connexion factice fournissant le curseur préparé."""

    def __init__(self, rows, rowcount=0):
        self.faux_curseur = FauxCurseur(rows, rowcount)
        self.commits = 0

    def cursor(self):
        return self.faux_curseur

    def commit(self):
        self.commits += 1


def creer_dao(rows=None, rowcount=0):
    """Construit un DAO sans lancer DBConnection."""
    dao = object.__new__(ObservationDao)
    dao.conn = FauxConnexion(rows or [], rowcount)
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


# ---------------------------------------------------------------------------
# inserer_ou_mettre_a_jour_par_lot
# ---------------------------------------------------------------------------


def test_inserer_par_lot_appelle_execute_values_et_renvoie_le_nombre(monkeypatch):
    appels = {}

    def faux_execute_values(cursor, requete, valeurs):
        appels["requete"] = requete
        appels["valeurs"] = valeurs

    monkeypatch.setattr(observation_dao_module, "execute_values", faux_execute_values)

    dao = creer_dao()
    observations = [
        Observation(
            code_indicateur="EMP",
            code_pays="FRA",
            periode="2020",
            valeur=10.0,
            sexe=Sexe.TOTAL,
            source="ILOSTAT",
        ),
        Observation(
            code_indicateur="EMP",
            code_pays="DEU",
            periode="2020",
            valeur=20.0,
            sexe="homme",
            source="ILOSTAT",
        ),
    ]

    nombre = dao.inserer_ou_mettre_a_jour_par_lot(observations)

    assert nombre == 2
    assert dao.conn.commits == 1
    assert "INSERT INTO observation" in appels["requete"]
    # Le sexe enum est converti en sa valeur texte ; la chaîne reste telle quelle.
    assert appels["valeurs"][0][4] == "total"
    assert appels["valeurs"][1][4] == "homme"


# ---------------------------------------------------------------------------
# lire_serie
# ---------------------------------------------------------------------------


def test_lire_serie_sans_filtre_optionnel():
    dao = creer_dao([LIGNE_EXEMPLE])

    resultat = dao.lire_serie("EMP", "FRA")

    assert len(resultat) == 1
    assert isinstance(resultat[0], Observation)
    assert dao.conn.faux_curseur.parametres == ("EMP", "FRA")
    assert "sexe = %s" not in dao.conn.faux_curseur.requete
    assert "ORDER BY periode ASC" in dao.conn.faux_curseur.requete


def test_lire_serie_avec_sexe_et_classification():
    dao = creer_dao([])

    dao.lire_serie("EMP", "FRA", sexe=Sexe.FEMME, code_classification="OCU_1")

    assert dao.conn.faux_curseur.parametres == ("EMP", "FRA", "femme", "OCU_1")
    assert "sexe = %s" in dao.conn.faux_curseur.requete
    assert "code_classification = %s" in dao.conn.faux_curseur.requete


# ---------------------------------------------------------------------------
# lire_par_periode
# ---------------------------------------------------------------------------


def test_lire_par_periode_sans_pays():
    dao = creer_dao([LIGNE_EXEMPLE])

    resultat = dao.lire_par_periode("EMP", "2024")

    assert len(resultat) == 1
    assert dao.conn.faux_curseur.parametres == ("EMP", "2024")
    assert "code_pays = ANY" not in dao.conn.faux_curseur.requete


def test_lire_par_periode_avec_liste_de_pays():
    dao = creer_dao([])

    dao.lire_par_periode("EMP", "2024", codes_pays=["FRA", "DEU"])

    assert dao.conn.faux_curseur.parametres == ("EMP", "2024", ["FRA", "DEU"])
    assert "code_pays = ANY(%s)" in dao.conn.faux_curseur.requete


# ---------------------------------------------------------------------------
# trouver_par_id
# ---------------------------------------------------------------------------


def test_trouver_par_id_existant():
    dao = creer_dao([LIGNE_EXEMPLE])

    observation = dao.trouver_par_id(7)

    assert isinstance(observation, Observation)
    assert observation.id == 7


def test_trouver_par_id_inexistant_renvoie_none():
    dao = creer_dao([])

    assert dao.trouver_par_id(999) is None


# ---------------------------------------------------------------------------
# modifier / supprimer
# ---------------------------------------------------------------------------


def test_modifier_renvoie_true_si_ligne_affectee():
    dao = creer_dao([], rowcount=1)

    resultat = dao.modifier(Observation(id=7, valeur=99.0, source="MANUEL"))

    assert resultat is True
    assert dao.conn.commits == 1
    assert dao.conn.faux_curseur.parametres == (99.0, "MANUEL", 7)


def test_modifier_renvoie_false_si_aucune_ligne():
    dao = creer_dao([], rowcount=0)

    assert dao.modifier(Observation(id=404, valeur=1.0, source="X")) is False


def test_supprimer_renvoie_true_si_ligne_affectee():
    dao = creer_dao([], rowcount=1)

    assert dao.supprimer(7) is True
    assert dao.conn.faux_curseur.parametres == (7,)


def test_supprimer_renvoie_false_si_aucune_ligne():
    dao = creer_dao([], rowcount=0)

    assert dao.supprimer(404) is False
