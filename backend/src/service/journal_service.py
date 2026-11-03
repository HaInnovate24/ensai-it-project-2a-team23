"""F6 : enregistrement et consultation du journal des actions sensibles."""

from business_object.enums import Role
from business_object.journal_activite import JournalActivite
from business_object.utilisateur import Utilisateur
from dao.journal_dao import JournalDao
from utils.exceptions import AccesRefuse, DonneesInvalides

# Tailles maximales des colonnes de la table journal_activite.
LONGUEUR_ACTION_MAX = 100
LONGUEUR_CIBLE_MAX = 255

# Nombre d'entrées renvoyées par défaut, et maximum autorisé.
LIMITE_PAR_DEFAUT = 100
LIMITE_MAX = 1000


class JournalService:
    """Enregistre les actions sensibles et permet aux administrateurs de les consulter.

    enregistrer est appelé par les autres services (par exemple UtilisateurService)
    chaque fois qu'une action sensible est réalisée. lister est réservé aux
    administrateurs (suivi des activités).
    """

    def __init__(self, journal_dao: JournalDao | None = None):
        """Initialise le service.

        Le DAO est facultatif : en production on laisse la valeur par défaut,
        dans les tests on fournit un faux DAO pour ne pas toucher à la base.
        """
        self.journal_dao = journal_dao if journal_dao is not None else JournalDao()

    def __init__(self):
        self.journal_dao = JournalDao()

    def enregistrer(
        self,
        utilisateur_id: int | None,
        action: str,
        cible: str | None = None,
        details: str | None = None,
    ) -> JournalActivite:

        """Enregistre une action dans le journal et renvoie l'entrée créée.

        utilisateur_id vaut None pour une action automatique (sans utilisateur).
        Ne jamais mettre de mot de passe ni d'empreinte dans cible ou details.

        Lève DonneesInvalides si l'action est vide ou si un texte dépasse la taille
        prévue en base.
        """
        if not isinstance(action, str) or not action.strip():
            raise DonneesInvalides("L'action du journal est obligatoire.")
        if len(action) > LONGUEUR_ACTION_MAX:
            raise DonneesInvalides(
                f"L'action du journal ne peut pas dépasser {LONGUEUR_ACTION_MAX} caractères."
            )
        if cible is not None and len(cible) > LONGUEUR_CIBLE_MAX:
            raise DonneesInvalides(
                f"La cible du journal ne peut pas dépasser {LONGUEUR_CIBLE_MAX} caractères."
            )

        entree = JournalActivite(
            utilisateur_id=utilisateur_id,
            action=action.strip(),
            cible=cible,
            details=details,
        )
        return self.journal_dao.creer(entree)

    def lister(
        self,
        acteur: Utilisateur,
        utilisateur_id: int | None = None,
        action: str | None = None,
        limite: int = LIMITE_PAR_DEFAUT,
    ) -> list[JournalActivite]:
        """Renvoie les entrées du journal, de la plus récente à la plus ancienne.

        Réservé aux administrateurs. On peut filtrer par auteur (utilisateur_id)
        et par type d'action. limite est le nombre maximum d'entrées renvoyées.

        Lève AccesRefuse si l'acteur n'est pas administrateur, DonneesInvalides si
        la limite est incorrecte.
        """
        if acteur is None or acteur.role != Role.ADMIN or not acteur.actif:
            raise AccesRefuse("Droits d'administrateur requis.")
        if isinstance(limite, bool) or not isinstance(limite, int) or not 1 <= limite <= LIMITE_MAX:
            raise DonneesInvalides(f"La limite doit être un entier entre 1 et {LIMITE_MAX}.")

        entrees = self.journal_dao.lister()
        if utilisateur_id is not None:
            entrees = [entree for entree in entrees if entree.utilisateur_id == utilisateur_id]
        if action is not None:
            entrees = [entree for entree in entrees if entree.action == action]
        return entrees[:limite]