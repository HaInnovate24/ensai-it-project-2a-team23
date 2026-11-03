"""Tests unitaires de l'objet métier Classification."""

from business_object.classification import Classification
from business_object.enums import TypeClassification


def test_initialisation_par_defaut_tout_none():
    """Une Classification sans argument a tous ses attributs à None."""
    cls = Classification()

    assert cls.code is None
    assert cls.libelle is None
    assert cls.type is None


def test_initialisation_complete():
    """Une Classification construite avec tous les attributs les conserve tels quels."""
    cls = Classification(
        code="AGE_15_24",
        libelle="15-24 ans",
        type=TypeClassification.AGE,
    )

    assert cls.code == "AGE_15_24"
    assert cls.libelle == "15-24 ans"
    assert cls.type == TypeClassification.AGE


def test_string_age_converti_en_enum():
    """Un string 'age' est converti en TypeClassification.AGE."""
    cls = Classification(code="C1", libelle="Test", type="age")

    assert cls.type == TypeClassification.AGE
    assert isinstance(cls.type, TypeClassification)


def test_string_occupation_converti_en_enum():
    """Un string 'occupation' est converti en TypeClassification.OCCUPATION."""
    cls = Classification(code="C2", libelle="Test", type="occupation")

    assert cls.type == TypeClassification.OCCUPATION
    assert isinstance(cls.type, TypeClassification)


def test_enum_pass_chez_lui():
    """Un TypeClassification déjà passé n'est pas reconverti."""
    cls = Classification(code="C3", libelle="Test", type=TypeClassification.OCCUPATION)

    assert cls.type == TypeClassification.OCCUPATION
    assert type(cls.type) is TypeClassification


def test_type_none_reste_none():
    """Un type à None reste None (pas de conversion)."""
    cls = Classification(code="C4", libelle="Test", type=None)

    assert cls.type is None
