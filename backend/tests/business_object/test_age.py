"""Tests unitaires de l'objet métier Age."""

from business_object.age import Age
from business_object.enums import TypeClassification


def test_initialisation_par_defaut():
    """Une Age sans argument a ses attributs à None, type forcé à AGE."""
    age = Age()

    assert age.code is None
    assert age.libelle is None
    assert age.age_min is None
    assert age.age_max is None
    assert age.type == TypeClassification.AGE


def test_initialisation_complete():
    """Une Age construite avec tous les attributs les conserve tels quels."""
    age = Age(
        code="AGE_15_24",
        libelle="15-24 ans",
        age_min=15,
        age_max=24,
    )

    assert age.code == "AGE_15_24"
    assert age.libelle == "15-24 ans"
    assert age.age_min == 15
    assert age.age_max == 24
    assert age.type == TypeClassification.AGE


def test_type_toujours_age():
    """Le type est toujours forcé à TypeClassification.AGE."""
    age = Age(code="X", libelle="Test", age_min=0, age_max=14)

    assert age.type == TypeClassification.AGE


def test_age_min_max_zero():
    """Les bornes d'âge peuvent être zero."""
    age = Age(code="AGE_0", libelle="0 ans", age_min=0, age_max=0)

    assert age.age_min == 0
    assert age.age_max == 0
