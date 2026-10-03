"""Routes HTTP d'administration : imports, données, comptes, journal."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/imports")
def lancer_import():
    """Lance un import de données."""
    ...


@router.get("/imports")
def lister_imports():
    """Renvoie l'historique des imports."""
    ...


@router.put("/observations/{observation_id}")
def corriger_observation(observation_id: int):
    """Corrige une observation."""
    ...


@router.delete("/observations/{observation_id}")
def supprimer_observation(observation_id: int):
    """Supprime une observation."""
    ...


@router.get("/utilisateurs")
def lister_utilisateurs():
    """Renvoie la liste des comptes."""
    ...


@router.put("/utilisateurs/{utilisateur_id}")
def gerer_utilisateur(utilisateur_id: int):
    """Gère un compte (promotion, désactivation)."""
    ...


@router.get("/journal")
def consulter_journal():
    """Renvoie le journal des actions sensibles."""
    ...
