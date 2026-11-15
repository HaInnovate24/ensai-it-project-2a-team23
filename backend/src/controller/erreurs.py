"""Traduction centralisée des erreurs métier en réponses HTTP.

Toutes les routes laissent remonter les exceptions définies dans
``utils.exceptions``. Le gestionnaire enregistré par
``installer_gestionnaires_erreurs`` les intercepte au niveau de l'application
et renvoie le bon code HTTP, ce qui évite de dupliquer la correspondance
erreur -> code dans chaque controller (et évite les 500 lorsqu'une erreur
métier n'est pas attrapée localement).
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    ErreurMetier,
    RessourceIntrouvable,
)

# Correspondance erreur métier -> code HTTP. L'ordre n'importe pas : on teste
# les sous-classes les plus spécifiques via isinstance dans code_http.
_CODES_HTTP: list[tuple[type[ErreurMetier], int]] = [
    (AuthentificationEchouee, 401),  # jeton absent, invalide ou expiré
    (AccesRefuse, 403),  # droits insuffisants / compte désactivé
    (RessourceIntrouvable, 404),  # élément ou donnée inexistant
    (ConflitRessource, 409),  # ressource déjà existante / état déjà atteint
]

# Toute autre erreur métier (DonneesInvalides, ErreurMetier de base) : paramètres
# invalides.
_CODE_PAR_DEFAUT = 422


def code_http(erreur: ErreurMetier) -> int:
    """Renvoie le code HTTP correspondant à une erreur métier."""
    for type_erreur, code in _CODES_HTTP:
        if isinstance(erreur, type_erreur):
            return code
    return _CODE_PAR_DEFAUT


def installer_gestionnaires_erreurs(app: FastAPI) -> None:
    """Enregistre le gestionnaire central des erreurs métier sur l'application."""

    @app.exception_handler(ErreurMetier)
    async def _gerer_erreur_metier(request: Request, erreur: ErreurMetier) -> JSONResponse:
        return JSONResponse(
            status_code=code_http(erreur),
            content={"detail": str(erreur)},
        )
