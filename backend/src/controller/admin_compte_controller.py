"""Routes HTTP d'administration des comptes et du journal (administrateurs uniquement).

Ce routeur complète admin_controller (imports, données), il se branche sur le même
préfixe /admin dans main.py. Les erreurs métier sont transformées en codes HTTP par
le gestionnaire global (controller/erreurs_http.py).
"""

from fastapi import APIRouter, Depends

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from controller.dependances import exiger_admin
from model.journal_model import JournalSortie
from model.utilisateur_model import ChangementActivation, ChangementRole, UtilisateurSortie
from service.journal_service import LIMITE_PAR_DEFAUT, JournalService
from service.utilisateur_service import UtilisateurService

router = APIRouter()


def get_utilisateur_service() -> UtilisateurService:
    """Fournit le service de gestion des comptes (remplaçable dans les tests)."""
    return UtilisateurService()


def get_journal_service() -> JournalService:
    """Fournit le service du journal."""
    return JournalService()


@router.get("/utilisateurs", response_model=list[UtilisateurSortie])
def lister_utilisateurs(
    acteur: Utilisateur = Depends(exiger_admin),
    service: UtilisateurService = Depends(get_utilisateur_service),
) -> list[UtilisateurSortie]:
    """Liste tous les comptes, sans mot de passe ni empreinte."""
    return [UtilisateurSortie.model_validate(u) for u in service.lister_utilisateurs(acteur)]


@router.patch("/utilisateurs/{id_utilisateur}/role", response_model=UtilisateurSortie)
def changer_role(
    id_utilisateur: int,
    changement: ChangementRole,
    acteur: Utilisateur = Depends(exiger_admin),
    service: UtilisateurService = Depends(get_utilisateur_service),
) -> UtilisateurSortie:
    """Promeut ("admin") ou rétrograde ("utilisateur") un compte.

    Réponses : 200, 404 compte inconnu, 409 rôle déjà attribué, 422 si on vise son propre compte.
    """
    if changement.role == Role.ADMIN:
        cible = service.promouvoir_admin(acteur, id_utilisateur)
    else:
        cible = service.retrograder_admin(acteur, id_utilisateur)
    return UtilisateurSortie.model_validate(cible)


@router.patch("/utilisateurs/{id_utilisateur}/activation", response_model=UtilisateurSortie)
def changer_activation(
    id_utilisateur: int,
    changement: ChangementActivation,
    acteur: Utilisateur = Depends(exiger_admin),
    service: UtilisateurService = Depends(get_utilisateur_service),
) -> UtilisateurSortie:
    """Active (true) ou désactive (false) un compte.

    Réponses : 200, 404 compte inconnu, 409 déjà dans cet état, 422 si on désactive son propre compte.
    """
    cible = service.definir_activation(acteur, id_utilisateur, changement.actif)
    return UtilisateurSortie.model_validate(cible)


@router.get("/journal", response_model=list[JournalSortie])
def consulter_journal(
    utilisateur_id: int | None = None,
    action: str | None = None,
    limite: int = LIMITE_PAR_DEFAUT,
    acteur: Utilisateur = Depends(exiger_admin),
    service: JournalService = Depends(get_journal_service),
) -> list[JournalSortie]:
    """Consulte le journal d'activité, de la plus récente à la plus ancienne (filtres facultatifs)."""
    entrees = service.lister(acteur, utilisateur_id=utilisateur_id, action=action, limite=limite)
    return [JournalSortie.model_validate(entree) for entree in entrees]