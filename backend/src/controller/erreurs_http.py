"""Traduction des erreurs métier en réponses HTTP.

Correspondance :
    AuthentificationEchouee -> 401 (identité non établie : identifiants ou jeton)
    AccesRefuse             -> 403 (identité connue mais droits insuffisants)
    RessourceIntrouvable    -> 404
    ConflitRessource        -> 409 (la ressource existe déjà, ou état déjà atteint)
    DonneesInvalides        -> 422
    autre erreur métier     -> 400
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    DonneesInvalides,
    ErreurMetier,
    RessourceIntrouvable,
)

CODES_HTTP = [
    (AuthentificationEchouee, 401),
    (AccesRefuse, 403),
    (RessourceIntrouvable, 404),
    (ConflitRessource, 409),
    (DonneesInvalides, 422),
]
CODE_PAR_DEFAUT = 400


def code_http(erreur: ErreurMetier) -> int:
    """Renvoie le code HTTP correspondant à une erreur métier."""
    for classe_erreur, code in CODES_HTTP:
        if isinstance(erreur, classe_erreur):
            return code
    return CODE_PAR_DEFAUT


def en_tetes(code: int) -> dict[str, str] | None:
    """Renvoie les en-têtes à ajouter à la réponse.

    Une réponse 401 doit indiquer comment s'authentifier (norme HTTP).
    """
    if code == 401:
        return {"WWW-Authenticate": "Bearer"}
    return None


def erreur_http(erreur: ErreurMetier) -> HTTPException:
    """Transforme une erreur métier en HTTPException (à lever dans un controller)."""
    code = code_http(erreur)
    return HTTPException(status_code=code, detail=str(erreur), headers=en_tetes(code))


async def gerer_erreur_metier(request: Request, erreur: ErreurMetier) -> JSONResponse:
    """Gestionnaire global : transforme toute erreur métier non interceptée en réponse JSON.

    Grâce à lui, les routes n'ont pas besoin de try/except, elles laissent
    l'erreur métier remonter et FastAPI appelle cette fonction.
    """
    code = code_http(erreur)
    return JSONResponse(status_code=code, content={"detail": str(erreur)}, headers=en_tetes(code))


def enregistrer_gestionnaires(app: FastAPI) -> None:
    """Branche le gestionnaire d'erreurs métier sur l'application (à appeler dans main.py)."""
    app.add_exception_handler(ErreurMetier, gerer_erreur_metier)