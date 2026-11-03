"""Tests unitaires de l'objet métier Observation."""

from datetime import datetime

from business_object.enums import Sexe
from business_object.observation import Observation


def test_initialisation_par_defaut_tout_none():
    """Une Observation sans argument a tous ses attributs à None."""
    obs = Observation()

    assert obs.id is None
    assert obs.code_indicateur is None
    assert obs.code_pays is None
    assert obs.periode is None
    assert obs.valeur is None
    assert obs.sexe is None
    assert obs.code_classification is None
    assert obs.import_id is None
    assert obs.source is None
    assert obs.date_import is None


def test_initialisation_complete():
    """Une Observation construite avec tous les attributs les conserve tels quels."""
    date_import = datetime(2024, 1, 15, 10, 30, 0)
    obs = Observation(
        id=42,
        code_indicateur="EMP",
        code_pays="FRA",
        periode="2024",
        valeur=78.3,
        sexe=Sexe.FEMME,
        code_classification="25-49",
        import_id=7,
        source="ILOSTAT",
        date_import=date_import,
    )

    assert obs.id == 42
    assert obs.code_indicateur == "EMP"
    assert obs.code_pays == "FRA"
    assert obs.periode == "2024"
    assert obs.valeur == 78.3
    assert obs.sexe == Sexe.FEMME
    assert obs.code_classification == "25-49"
    assert obs.import_id == 7
    assert obs.source == "ILOSTAT"
    assert obs.date_import == date_import


def test_string_homme_converti_en_enum():
    """Un string 'homme' est converti en Sexe.HOMME."""
    obs = Observation(sexe="homme")

    assert obs.sexe == Sexe.HOMME
    assert isinstance(obs.sexe, Sexe)


def test_string_femme_converti_en_enum():
    """Un string 'femme' est converti en Sexe.FEMME."""
    obs = Observation(sexe="femme")

    assert obs.sexe == Sexe.FEMME
    assert isinstance(obs.sexe, Sexe)


def test_string_total_converti_en_enum():
    """Un string 'total' est converti en Sexe.TOTAL."""
    obs = Observation(sexe="total")

    assert obs.sexe == Sexe.TOTAL
    assert isinstance(obs.sexe, Sexe)


def test_enum_pass_chez_lui():
    """Un enum Sexe déjà passé n'est pas reconverti."""
    obs = Observation(sexe=Sexe.HOMME)

    assert obs.sexe == Sexe.HOMME
    assert type(obs.sexe) is Sexe


def test_sexe_none_reste_none():
    """Un sexe à None reste None (pas de conversion)."""
    obs = Observation(sexe=None)

    assert obs.sexe is None


def test_valeur_negative():
    """La valeur peut être négative."""
    obs = Observation(valeur=-3.14)

    assert obs.valeur == -3.14


def test_valeur_zero():
    """La valeur peut être nulle."""
    obs = Observation(valeur=0.0)

    assert obs.valeur == 0.0


def test_code_classification_occupation():
    """La classification peut être une occupation."""
    obs = Observation(code_classification="independant")

    assert obs.code_classification == "independant"


def test_code_classification_age():
    """La classification peut être une tranche d'âge."""
    obs = Observation(code_classification="15-24")

    assert obs.code_classification == "15-24"
