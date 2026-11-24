"""Tests du PaysDao avec une connexion mockée (aucune base réelle)."""

from business_object.pays import Pays
from dao.pays_dao import PaysDao


def test_lister_renvoie_des_pays(curseur):
    """lister() mappe chaque ligne renvoyée par la base en objet Pays."""
    curseur.fetchall.return_value = [
        {"code_pays": "FRA", "nom_pays": "France"},
        {"code_pays": "DEU", "nom_pays": "Allemagne"},
    ]

    pays = PaysDao().lister()

    assert len(pays) == 2
    assert all(isinstance(p, Pays) for p in pays)
    assert pays[0].code_pays == "FRA"
    assert pays[0].nom_pays == "France"


def test_lister_sans_resultat(curseur):
    """lister() renvoie une liste vide si la base ne renvoie rien."""
    curseur.fetchall.return_value = []
    assert PaysDao().lister() == []


def test_trouver_par_code_existant(curseur):
    """trouver_par_code() renvoie le Pays correspondant quand il existe."""
    curseur.fetchone.return_value = {"code_pays": "FRA", "nom_pays": "France"}

    pays = PaysDao().trouver_par_code("FRA")

    assert pays is not None
    assert pays.code_pays == "FRA"
    assert pays.nom_pays == "France"


def test_trouver_par_code_inexistant(curseur):
    """trouver_par_code() renvoie None quand le pays n'existe pas."""
    curseur.fetchone.return_value = None
    assert PaysDao().trouver_par_code("XYZ") is None


def test_creer_renvoie_le_pays_insere(curseur, connexion):
    """creer() renvoie l'objet inséré et valide la transaction (commit)."""
    curseur.fetchone.return_value = {"code_pays": "ITA", "nom_pays": "Italie"}

    cree = PaysDao().creer(Pays(code_pays="ITA", nom_pays="Italie"))

    assert cree.code_pays == "ITA"
    assert cree.nom_pays == "Italie"
    connexion.commit.assert_called()
