"""F6 : gestion des comptes par les administrateurs (promotion, désactivation, liste)."""

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDao
from service.journal_service import JournalService
from utils.exceptions import (
    AccesRefuse,
    ConflitRessource,
    DonneesInvalides,
    RessourceIntrouvable,
)

# Noms des actions écrites dans le journal d'activité.
ACTION_PROMOTION = "PROMOTION_ADMIN"
ACTION_RETROGRADATION = "RETROGRADATION_ADMIN"
ACTION_DESACTIVATION = "DESACTIVATION_COMPTE"
ACTION_REACTIVATION = "REACTIVATION_COMPTE"


class UtilisateurService:
    """Permet aux administrateurs de gérer les comptes.

    Toutes les méthodes reçoivent en premier paramètre l'utilisateur connecté qui fait
    la demande (obtenu par AuthentificationService). Seul un administrateur actif peut
    les utiliser. Chaque modification est tracée dans le journal d'activité.

    L'inscription d'un nouvel utilisateur est dans AuthentificationService.inscrire.
    """

    def __init__(
        self,
        utilisateur_dao: UtilisateurDao | None = None,
        journal_service: JournalService | None = None,
    ):
        """Initialise le service."""
        self.utilisateur_dao = utilisateur_dao if utilisateur_dao is not None else UtilisateurDao()
        self.journal_service = journal_service if journal_service is not None else JournalService()

    # Consultation

    def lister_utilisateurs(self, acteur: Utilisateur | None = None) -> list[Utilisateur]:
        """Renvoie tous les comptes (administrateur uniquement)."""
        self._exiger_admin(acteur)
        return self.utilisateur_dao.lister()

    def trouver_utilisateur(self, acteur: Utilisateur, id_utilisateur: int) -> Utilisateur:
        """Renvoie le compte correspondant à l'identifiant (administrateur uniquement)."""
        self._exiger_admin(acteur)
        return self._trouver(id_utilisateur)

    # --- Modifications (toutes tracées dans le journal) ---

    @staticmethod
    def modifier(utilisateur: Utilisateur) -> bool:
        """Met à jour les informations d'un utilisateur en BDD (compatibilité contrôleur/tests)."""
        return UtilisateurDao().modifier(utilisateur)

    def promouvoir_admin(self, acteur: Utilisateur, id_utilisateur: int) -> Utilisateur:
        """Donne le rôle administrateur à un compte et renvoie le compte modifié."""
        self._exiger_admin(acteur)
        cible = self._trouver(id_utilisateur)
        if cible.role == Role.ADMIN:
            raise ConflitRessource("Cet utilisateur est déjà administrateur.")

        cible.role = Role.ADMIN
        self._enregistrer_modification(
            acteur, cible, ACTION_PROMOTION, f"{cible.nom_utilisateur} : utilisateur -> admin"
        )
        return cible

    def retrograder_admin(self, acteur: Utilisateur, id_utilisateur: int) -> Utilisateur:
        """Retire le rôle administrateur à un compte et renvoie le compte modifié."""
        self._exiger_admin(acteur)
        cible = self._trouver(id_utilisateur)
        self._interdire_son_propre_compte(acteur, cible)
        if cible.role != Role.ADMIN:
            raise ConflitRessource("Cet utilisateur n'est pas administrateur.")

        cible.role = Role.UTILISATEUR
        self._enregistrer_modification(
            acteur, cible, ACTION_RETROGRADATION, f"{cible.nom_utilisateur} : admin -> utilisateur"
        )
        return cible

    def definir_activation(
        self, acteur: Utilisateur, id_utilisateur: int, actif: bool
    ) -> Utilisateur:
        """Active (actif=True) ou désactive (actif=False) un compte et le renvoie."""
        self._exiger_admin(acteur)
        if not isinstance(actif, bool):
            raise DonneesInvalides("L'état d'activation doit être vrai ou faux.")
        cible = self._trouver(id_utilisateur)
        if not actif:
            self._interdire_son_propre_compte(acteur, cible)
        if cible.actif == actif:
            raise ConflitRessource(
                "Ce compte est déjà actif." if actif else "Ce compte est déjà désactivé."
            )

        cible.actif = actif
        if actif:
            action, details = ACTION_REACTIVATION, f"{cible.nom_utilisateur} : compte réactivé"
        else:
            action, details = ACTION_DESACTIVATION, f"{cible.nom_utilisateur} : compte désactivé"
        self._enregistrer_modification(acteur, cible, action, details)
        return cible

    # --- Méthodes privées (outils internes) ---

    def _exiger_admin(self, acteur: Utilisateur | None) -> None:
        """Lève AccesRefuse si l'acteur n'est pas un administrateur actif."""
        if acteur is None or acteur.role != Role.ADMIN or not acteur.actif:
            raise AccesRefuse("Droits d'administrateur requis.")

    def _trouver(self, id_utilisateur: int) -> Utilisateur:
        """Renvoie le compte demandé."""
        if (
            isinstance(id_utilisateur, bool)
            or not isinstance(id_utilisateur, int)
            or id_utilisateur < 1
        ):
            raise DonneesInvalides("L'identifiant de l'utilisateur doit être un entier positif.")
        utilisateur = self.utilisateur_dao.trouver_par_id(id_utilisateur)
        if utilisateur is None:
            raise RessourceIntrouvable(f"Utilisateur inconnu : {id_utilisateur}.")
        return utilisateur

    def _interdire_son_propre_compte(self, acteur: Utilisateur, cible: Utilisateur) -> None:
        """Lève DonneesInvalides si l'acteur essaie d'agir sur son propre compte."""
        if acteur.id == cible.id:
            raise DonneesInvalides

    def _enregistrer_modification(
    self, acteur: Utilisateur, cible: Utilisateur, action: str, details: str
) -> None:
        """Met à jour l'utilisateur en BDD et trace l'action dans le journal."""
        succes = self.utilisateur_dao.modifier(cible)
        if not succes:
            raise RessourceIntrouvable(f"Utilisateur inconnu : {cible.id}.")
        
        if hasattr(self, "journal_service") and self.journal_service:
            self.journal_service.enregistrer(
            utilisateur_id=acteur.id, 
            action=action, 
            cible=f"utilisateur:{cible.id}",
            details=details
        )