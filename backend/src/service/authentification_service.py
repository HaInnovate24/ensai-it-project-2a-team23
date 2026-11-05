"""F6 : inscription, connexion et contrôle d'accès des utilisateurs."""

import re
from datetime import datetime

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDao
from utils import securite as securite_par_defaut
from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    DonneesInvalides,
)

# Règles sur le nom d'utilisateur (après mise en minuscules).
LONGUEUR_NOM_MIN = 3
LONGUEUR_NOM_MAX = 50
MOTIF_NOM = re.compile(r"[a-z0-9._-]+")

# Règles sur le mot de passe.
LONGUEUR_MOT_DE_PASSE_MIN = 8
LONGUEUR_MOT_DE_PASSE_MAX = 128

# Un seul message pour "utilisateur inconnu" et "mauvais mot de passe"
# on ne révèle pas si un nom d'utilisateur existe.
MESSAGE_IDENTIFIANTS_INCORRECTS = "Nom d'utilisateur ou mot de passe incorrect."
MESSAGE_JETON_INVALIDE = "Jeton invalide ou expiré."
MESSAGE_COMPTE_DESACTIVE = "Ce compte est désactivé."


class AuthentificationService:
    """Gère l'inscription, la connexion et la vérification des droits.

    Petit topo :

    Le service utilise deux outils, fournis de l'extérieur pour pouvoir les
    remplacer dans les tests :
        utilisateur_dao : accès à la table utilisateur et les méthodes utilisées snt :
            creer(utilisateur), trouver_par_nom(nom), trouver_par_id(id),
            modifier(utilisateur).
        securite : fonctions de sécurité (par défaut le module utils.securite).
            Fonctions utilisées : hacher_mot_de_passe, verifier_mot_de_passe,
            creer_jeton, lire_jeton.
    """

    def __init__(self, utilisateur_dao: UtilisateurDao | None = None, securite=None):
        """Initialise le service.

        Les deux paramètres sont facultatifs.
        """
        self.utilisateur_dao = utilisateur_dao if utilisateur_dao is not None else UtilisateurDao()
        self.securite = securite if securite is not None else securite_par_defaut

    # Méthodes publiques

    def inscrire(self, nom_utilisateur: str, mot_de_passe: str) -> Utilisateur:
        """Crée un compte utilisateur et le renvoie.

        Le compte créé est toujours un utilisateur standard. Le rôle ne peut pas
        être choisi à l'inscription (un administrateur est promu par un autre).
        Le nom est enregistré en minuscules.

        Lève DonneesInvalides si le nom ou le mot de passe ne respecte pas les règles,
        ConflitRessource si le nom est déjà pris.
        """
        nom = self._normaliser_nom(nom_utilisateur)
        self._verifier_nom(nom)
        self._verifier_mot_de_passe(mot_de_passe, nom)

        if self.utilisateur_dao.trouver_par_nom(nom) is not None:
            raise ConflitRessource("Ce nom d'utilisateur est déjà utilisé.")

        utilisateur = Utilisateur(
            nom_utilisateur=nom,
            mot_de_passe_hash=self.securite.hacher_mot_de_passe(mot_de_passe),
            role=Role.UTILISATEUR,
            actif=True,
        )
        return self.utilisateur_dao.creer(utilisateur)

    def connecter(self, nom_utilisateur: str, mot_de_passe: str) -> str:
        """Vérifie les identifiants et renvoie un jeton de connexion.

        Lève DonneesInvalides si un champ est vide, AuthentificationEchouee si les
        identifiants sont incorrects, AccesRefuse si le compte est désactivé
        (testé seulement après vérification du mot de passe, pour ne rien révéler
        à quelqu'un qui ne connaît pas le mot de passe).
        """
        if (
            not isinstance(nom_utilisateur, str)
            or not nom_utilisateur.strip()
            or not isinstance(mot_de_passe, str)
            or not mot_de_passe
        ):
            raise DonneesInvalides("Le nom d'utilisateur et le mot de passe sont obligatoires.")

        # Un mot de passe trop long ne peut pas être valide : on évite de le hacher.
        if len(mot_de_passe) > LONGUEUR_MOT_DE_PASSE_MAX:
            raise AuthentificationEchouee(MESSAGE_IDENTIFIANTS_INCORRECTS)

        utilisateur = self.utilisateur_dao.trouver_par_nom(self._normaliser_nom(nom_utilisateur))
        if utilisateur is None or not self.securite.verifier_mot_de_passe(
            mot_de_passe, utilisateur.mot_de_passe_hash
        ):
            raise AuthentificationEchouee(MESSAGE_IDENTIFIANTS_INCORRECTS)

        if not utilisateur.actif:
            raise AccesRefuse(MESSAGE_COMPTE_DESACTIVE)

        utilisateur.derniere_connexion = datetime.now()
        self.utilisateur_dao.modifier(utilisateur)
        return self.securite.creer_jeton(utilisateur.id)

    def utilisateur_depuis_jeton(self, jeton: str | None) -> Utilisateur:
        """Renvoie l'utilisateur à qui appartient le jeton.

        Le rôle est relu en base à chaque appel. Une promotion ou une
        désactivation s'applique tout de suite, sans attendre l'expiration du jeton.

        Lève AuthentificationEchouee si le jeton est absent, invalide, expiré ou
        si l'utilisateur n'existe plus, AccesRefuse si le compte est désactivé.
        """
        if not jeton:
            raise AuthentificationEchouee("Authentification requise.")

        try:
            id_utilisateur = self.securite.lire_jeton(jeton)
        except ValueError as erreur:
            raise AuthentificationEchouee(MESSAGE_JETON_INVALIDE) from erreur

        utilisateur = self.utilisateur_dao.trouver_par_id(id_utilisateur)
        if utilisateur is None:
            raise AuthentificationEchouee(MESSAGE_JETON_INVALIDE)
        if not utilisateur.actif:
            raise AccesRefuse(MESSAGE_COMPTE_DESACTIVE)
        return utilisateur

    def exiger_admin(self, utilisateur: Utilisateur) -> Utilisateur:
        """Renvoie l'utilisateur s'il est administrateur, sinon lève AccesRefuse."""
        if utilisateur.role != Role.ADMIN:
            raise AccesRefuse("Droits d'administrateur requis.")
        return utilisateur

    def exiger_connexion(self, jeton: str) -> Utilisateur:
        """Renvoie l'utilisateur s'il est connecté, sinon lève AccesRefuse."""
        utilisateur = self.utilisateur_depuis_jeton(jeton)
        if utilisateur is None:
            raise AccesRefuse("Authentification requise.")
        return True

    # Méthodes privées (petits outils internes)

    def _normaliser_nom(self, nom_utilisateur: str) -> str:
        """Enlève les espaces autour du nom et le met en minuscules.

        Lève DonneesInvalides si ce n'est pas du texte.
        """
        if not isinstance(nom_utilisateur, str):
            raise DonneesInvalides("Le nom d'utilisateur est obligatoire.")
        return nom_utilisateur.strip().lower()

    def _verifier_nom(self, nom: str) -> None:
        """Vérifie la longueur et les caractères du nom (lettres, chiffres, . _ -)."""
        if not nom:
            raise DonneesInvalides("Le nom d'utilisateur est obligatoire.")
        if not LONGUEUR_NOM_MIN <= len(nom) <= LONGUEUR_NOM_MAX:
            raise DonneesInvalides(
                f"Le nom d'utilisateur doit faire entre {LONGUEUR_NOM_MIN} "
                f"et {LONGUEUR_NOM_MAX} caractères."
            )
        if MOTIF_NOM.fullmatch(nom) is None:
            raise DonneesInvalides(
                "Le nom d'utilisateur ne peut contenir que des lettres sans accent, "
                "des chiffres et les caractères . _ -"
            )

    def _verifier_mot_de_passe(self, mot_de_passe: str, nom: str) -> None:
        """Vérifie que le mot de passe respecte les règles de sécurité.

        Règles : longueur entre 8 et 128, au moins une lettre et un chiffre,
        différent du nom d'utilisateur.
        """
        if not isinstance(mot_de_passe, str) or not mot_de_passe:
            raise DonneesInvalides("Le mot de passe est obligatoire.")
        if not LONGUEUR_MOT_DE_PASSE_MIN <= len(mot_de_passe) <= LONGUEUR_MOT_DE_PASSE_MAX:
            raise DonneesInvalides(
                f"Le mot de passe doit faire entre {LONGUEUR_MOT_DE_PASSE_MIN} "
                f"et {LONGUEUR_MOT_DE_PASSE_MAX} caractères."
            )
        if not any(caractere.isalpha() for caractere in mot_de_passe):
            raise DonneesInvalides("Le mot de passe doit contenir au moins une lettre.")
        if not any(caractere.isdigit() for caractere in mot_de_passe):
            raise DonneesInvalides("Le mot de passe doit contenir au moins un chiffre.")
        if mot_de_passe.lower() == nom:
            raise DonneesInvalides("Le mot de passe doit être différent du nom d'utilisateur.")
