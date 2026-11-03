"""Tests des erreurs métier communes."""

import pytest

from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    DonneesInvalides,
    ErreurMetier,
    RessourceIntrouvable,
)

TOUTES_LES_ERREURS = [
    RessourceIntrouvable,
    DonneesInvalides,
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
]


@pytest.mark.parametrize("classe_erreur", TOUTES_LES_ERREURS)
def test_toutes_les_erreurs_heritent_de_erreur_metier(classe_erreur):
    """On peut intercepter toutes les erreurs métier avec ErreurMetier."""
    assert issubclass(classe_erreur, ErreurMetier)


@pytest.mark.parametrize("classe_erreur", TOUTES_LES_ERREURS)
def test_le_message_est_conserve(classe_erreur):
    """Le message donné à l'erreur est bien retrouvé avec str()."""
    erreur = classe_erreur("Un message")

    assert str(erreur) == "Un message"


def test_les_erreurs_sont_distinctes():
    """Intercepter AccesRefuse n'attrape pas AuthentificationEchouee (401 et 403 diffèrent)."""
    with pytest.raises(AuthentificationEchouee):
        try:
            raise AuthentificationEchouee("Pas connecté")
        except AccesRefuse:
            pytest.fail("AccesRefuse ne doit pas attraper AuthentificationEchouee")
