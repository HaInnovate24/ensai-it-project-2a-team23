"""Point d'entrée du service web FastAPI.

Crée l'application, branche les routeurs et démarre le planificateur.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from controller import (
    admin_comptes_controller,
    admin_controller,
    analyse_controller,
    auth_controller,
    rapport_controller,
    referentiel_controller,
)
from controller.erreurs_http import enregistrer_gestionnaires
from utils.config import display_values, load_environment_variables
from utils.journalisation import LogMiddleware, get_logger, initialize_logs

logger = get_logger(__name__)

# Initialisation
initialize_logs("Webservice")

load_environment_variables()
display_values()


app = FastAPI(title="LaborScope")

app.add_middleware(LogMiddleware)

# Transforme les erreurs métier (401, 403, 404, 409, 422...) en réponses HTTP.
enregistrer_gestionnaires(app)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Intercepte les erreurs 422 de Pydantic pour les journaliser."""
    body = await request.body()
    body_str = body.decode() if body else "empty body"
    erreurs = exc.errors()

    # Sécurité : sur les routes d'authentification, le corps contient un mot de passe et
    # les erreurs Pydantic recopient les valeurs reçues ("input"). On ne les journalise
    # ni ne les renvoie : on garde seulement l'emplacement, le message et le type d'erreur.
    if request.url.path.startswith("/auth"):
        body_str = "[masqué : routes d'authentification]"
        erreurs = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in erreurs]

    logger.error(f"Validation Error\nErrors: {erreurs}\nBody: {body_str}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": erreurs, "body": body_str},
    )


app.include_router(auth_controller.router, prefix="/auth", tags=["Authentification"])
app.include_router(referentiel_controller.router, prefix="/referentiels", tags=["Référentiels"])
app.include_router(analyse_controller.router, prefix="/analyses", tags=["Analyses"])
app.include_router(rapport_controller.router, prefix="/rapports", tags=["Rapports"])
app.include_router(admin_controller.router, prefix="/admin", tags=["Administration"])
app.include_router(admin_comptes_controller.router, prefix="/admin", tags=["Administration"])


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """Redirige vers la documentation de l'API."""
    return RedirectResponse(url="/docs")


# Lancement de l'application FastAPI
if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=int(os.getenv("UVICORN_PORT", "5000")),
    )

    logger.info("Webservice stopped")
