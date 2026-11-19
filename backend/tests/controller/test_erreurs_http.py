"""Tests de la traduction des erreurs métier en réponses HTTP."""

import asyncio
import json

import pytest
from fastapi import FastAPI, HTTPException

from controller.erreurs_http import (
    code_http,
    en_tetes,
    enregistrer_gestionnaires,
    erreur_http,
    gerer_erreur_metier,
)
from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    DonneesInvalides,
    ErreurMetier,
    RessourceIntrouvable,
)

CORRESPONDANCES = [
    (AuthentificationEchouee, 401),
    (AccesRefuse, 403),
    (RessourceIntrouvable, 404),
    (ConflitRessource, 409),
    (DonneesInvalides, 422),
]


@pytest.mark.parametrize(("classe_erreur", "code_attendu"), CORRESPONDANCES)
def test_code_http(classe_erreur, code_attendu):
    """Chaque erreur métier correspond au code HTTP prévu."""
    assert code_http(classe_erreur("message")) == code_attendu


def test_code_http_erreur_metier_generique():
    """Une erreur métier sans classe particulière donne 400."""
    assert code_http(ErreurMetier("message")) == 400


def test_en_tetes_401():
    """Une réponse 401 indique le schéma d'authentification attendu."""
    assert en_tetes(401) == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize("code", [400, 403, 404, 409, 422])
def test_en_tetes_autres_codes(code):
    """Les autres codes n'ajoutent aucun en-tête."""
    assert en_tetes(code) is None


@pytest.mark.parametrize(("classe_erreur", "code_attendu"), CORRESPONDANCES)
def test_erreur_http(classe_erreur, code_attendu):
    """erreur_http renvoie une HTTPException avec le bon code et le message d'origine."""
    resultat = erreur_http(classe_erreur("Un message"))

    assert isinstance(resultat, HTTPException)
    assert resultat.status_code == code_attendu
    assert resultat.detail == "Un message"


def test_erreur_http_401_contient_l_en_tete_www_authenticate():
    """L'HTTPException 401 porte l'en-tête WWW-Authenticate."""
    resultat = erreur_http(AuthentificationEchouee("Pas connecté"))

    assert resultat.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize(("classe_erreur", "code_attendu"), CORRESPONDANCES)
def test_gestionnaire_global(classe_erreur, code_attendu):
    """Le gestionnaire global renvoie une réponse JSON {"detail": message} avec le bon code."""
    reponse = asyncio.run(gerer_erreur_metier(None, classe_erreur("Un message")))

    assert reponse.status_code == code_attendu
    assert json.loads(reponse.body) == {"detail": "Un message"}


def test_gestionnaire_global_401_contient_l_en_tete():
    """La réponse 401 du gestionnaire global contient WWW-Authenticate."""
    reponse = asyncio.run(gerer_erreur_metier(None, AuthentificationEchouee("Non connecté")))

    assert reponse.headers["www-authenticate"] == "Bearer"


def test_enregistrer_gestionnaires():
    """Le gestionnaire est bien branché sur ErreurMetier (donc sur toutes ses sous-classes)."""
    app = FastAPI()

    enregistrer_gestionnaires(app)

    assert app.exception_handlers[ErreurMetier] is gerer_erreur_metier
