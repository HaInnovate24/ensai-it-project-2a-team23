"""Tests unitaires de l'objet métier Indicateur."""

from business_object.indicateur import Indicateur


def test_initialisation_par_defaut():
    """Un Indicateur sans argument a ses attributs à None, sauf actif (True)."""
    ind = Indicateur()

    assert ind.code_indicateur is None
    assert ind.description is None
    assert ind.unite is None
    assert ind.source is None
    assert ind.actif is True


def test_initialisation_complete():
    """Un Indicateur construit avec tous les attributs les conserve tels quels."""
    ind = Indicateur(
        code_indicateur="EMP",
        description="Taux d'emploi",
        unite="%",
        source="ILOSTAT",
        actif=True,
    )

    assert ind.code_indicateur == "EMP"
    assert ind.description == "Taux d'emploi"
    assert ind.unite == "%"
    assert ind.source == "ILOSTAT"
    assert ind.actif is True


def test_actif_par_defaut_vrai():
    """Un indicateur est actif par défaut."""
    ind = Indicateur(code_indicateur="EMP")

    assert ind.actif is True


def test_actif_explicite_faux():
    """Un indicateur peut être désactivé explicitement."""
    ind = Indicateur(code_indicateur="EMP", actif=False)

    assert ind.actif is False
