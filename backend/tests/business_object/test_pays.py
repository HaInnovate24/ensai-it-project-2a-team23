"""Tests unitaires de l'objet métier Pays."""

from business_object.pays import Pays


def test_initialisation_par_defaut_tout_none():
    """Un Pays sans argument a tous ses attributs à None."""
    pays = Pays()

    assert pays.code_pays is None
    assert pays.nom_pays is None


def test_initialisation_complete():
    """Un Pays construit avec ses attributs les conserve tels quels."""
    pays = Pays(code_pays="FRA", nom_pays="France")

    assert pays.code_pays == "FRA"
    assert pays.nom_pays == "France"


def test_code_pays_puis_nom_pays():
    """Chaque pays a un code ISO et un nom."""
    pays = Pays(code_pays="DEU", nom_pays="Allemagne")

    assert pays.code_pays == "DEU"
    assert pays.nom_pays == "Allemagne"
