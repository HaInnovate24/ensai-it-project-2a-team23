"""Routes HTTP d'authentification : inscription, connexion, profil courant."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/inscription")
def inscription():
    """Inscrit un nouvel utilisateur."""
    ...


@router.post("/connexion")
def connexion():
    """Authentifie un utilisateur et renvoie un jeton."""
    ...


@router.get("/moi")
def profil_courant():
    """Renvoie le profil de l'utilisateur connecté."""
    ...
