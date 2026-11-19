"""Tests des routes d'authentification, avec un faux service.

On appelle directement les fonctions des routes. On vérifie les paramètres transmis,
le contenu des réponses (jamais d'empreinte de mot de passe) et que les erreurs
métier remontent sans être interceptées (le gestionnaire global les transformera).
"""

from datetime import datetime

import pytest

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from controller.auth_controller import connexion, inscription, profil_courant
from model.auth_model import Identifiants
from model.utilisateur_model import UtilisateurSortie
from utils.exceptions import AuthentificationEchouee, ConflitRessource


class FauxAuthentificationService:
    """Faux service : il note les appels et renvoie des résultats fixes (ou une erreur)."""

    def __init__(self, erreur=None):
        """Si une erreur est fournie, chaque méthode la lève."""
        self.erreur = erreur
        self.appel = None

    def inscrire(self, nom_utilisateur, mot_de_passe):
        """Imite AuthentificationService.inscrire (renvoie un compte avec son empreinte)."""
        self.appel = ("inscrire", nom_utilisateur, mot_de_passe)
        if self.erreur is not None:
            raise self.erreur
        return Utilisateur(
            id=1,
            nom_utilisateur=nom_utilisateur,
            mot_de_passe_hash="hash-secret",
            role=Role.UTILISATEUR,
            actif=True,
            date_creation=datetime(2026, 11, 3),
        )

    def connecter(self, nom_utilisateur, mot_de_passe):
        """Imite AuthentificationService.connecter."""
        self.appel = ("connecter", nom_utilisateur, mot_de_passe)
        if self.erreur is not None:
            raise self.erreur
        return "jeton-123"


def test_inscription_transmet_les_donnees_et_ne_renvoie_pas_d_empreinte():
    """La route transmet nom et mot de passe, puis renvoie le compte sans empreinte."""
    service = FauxAuthentificationService()
    identifiants = Identifiants(nom_utilisateur="alice", mot_de_passe="Motdepasse1")

    resultat = inscription(identifiants, service=service)

    assert service.appel == ("inscrire", "alice", "Motdepasse1")
    assert resultat["statut"] == "succes"
    assert resultat["message"] == "Utilisateur inscrit"
    compte = resultat["data"]
    assert isinstance(compte, UtilisateurSortie)
    assert compte.nom_utilisateur == "alice"
    assert compte.role is Role.UTILISATEUR
    assert "hash-secret" not in compte.model_dump_json()
    assert "Motdepasse1" not in compte.model_dump_json()


def test_inscription_laisse_remonter_le_conflit():
    """Un nom déjà pris (ConflitRessource) remonte tel quel, le gestionnaire global donnera 409."""
    service = FauxAuthentificationService(erreur=ConflitRessource("Nom déjà utilisé."))
    identifiants = Identifiants(nom_utilisateur="alice", mot_de_passe="Motdepasse1")

    with pytest.raises(ConflitRessource):
        inscription(identifiants, service=service)


def test_connexion_renvoie_le_jeton():
    """La route renvoie le jeton du service dans le champ data."""
    service = FauxAuthentificationService()
    identifiants = Identifiants(nom_utilisateur="alice", mot_de_passe="Motdepasse1")

    resultat = connexion(identifiants, service=service)

    assert service.appel == ("connecter", "alice", "Motdepasse1")
    assert resultat == {"message": "Utilisateur connecté", "statut": "succes", "data": "jeton-123"}


def test_connexion_laisse_remonter_l_echec():
    """Des identifiants incorrects (AuthentificationEchouee) remontent, 401 via le gestionnaire."""
    service = FauxAuthentificationService(erreur=AuthentificationEchouee("Incorrect."))
    identifiants = Identifiants(nom_utilisateur="alice", mot_de_passe="mauvais")

    with pytest.raises(AuthentificationEchouee):
        connexion(identifiants, service=service)


def test_profil_courant_ne_renvoie_pas_d_empreinte():
    """Le profil de l'utilisateur connecté ne contient jamais l'empreinte du mot de passe."""
    utilisateur = Utilisateur(
        id=2, nom_utilisateur="bob", mot_de_passe_hash="hash-secret", role=Role.ADMIN, actif=True
    )

    resultat = profil_courant(utilisateur=utilisateur)

    assert resultat["statut"] == "succes"
    assert resultat["data"].id == 2
    assert resultat["data"].role is Role.ADMIN
    assert "hash-secret" not in resultat["data"].model_dump_json()
