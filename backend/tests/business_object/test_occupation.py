"""Tests unitaires de l'objet métier Occupation."""

from business_object.enums import TypeClassification
from business_object.occupation import Occupation


def test_initialisation_par_defaut():
    """Une Occupation sans argument a ses attributs à None, type forcé à OCCUPATION."""
    occ = Occupation()

    assert occ.code is None
    assert occ.libelle is None
    assert occ.valeur is None
    assert occ.type == TypeClassification.OCCUPATION


def test_initialisation_complete():
    """Une Occupation construite avec tous les attributs les conserve tels quels."""
    occ = Occupation(
        code="OCC_01",
        libelle="Agriculteurs",
        valeur="11",
    )

    assert occ.code == "OCC_01"
    assert occ.libelle == "Agriculteurs"
    assert occ.valeur == "11"
    assert occ.type == TypeClassification.OCCUPATION


def test_type_toujours_occupation():
    """Le type est toujours forcé à TypeClassification.OCCUPATION."""
    occ = Occupation(code="X", libelle="Test", valeur="99")

    assert occ.type == TypeClassification.OCCUPATION
