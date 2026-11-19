"""Tests des dépendances d'authentification, avec un faux service."""

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from controller.dependances import exiger_admin, exiger_connexion, utilisateur_courant
from utils.exceptions import AccesRefuse, AuthentificationEchouee


class FauxAuthentificationService:
    """Faux service : il note le jeton reçu et renvoie un utilisateur (ou lève une erreur)."""

    def __init__(self, utilisateur=None, erreur=None):
        """Prépare l'utilisateur à renvoyer ou l'erreur à lever."""
        self.utilisateur = utilisateur
        self.erreur = erreur
        self.jeton_recu = "jamais appelé"

    def utilisateur_depuis_jeton(self, jeton):
        """Imite AuthentificationService.utilisateur_depuis_jeton."""
        self.jeton_recu = jeton
        if self.erreur is not None:
            raise self.erreur
        return self.utilisateur

    def exiger_admin(self, utilisateur):
        """Imite AuthentificationService.exiger_admin."""
        if utilisateur.role != Role.ADMIN:
            raise AccesRefuse("Droits d'administrateur requis.")
        return utilisateur


def creer_utilisateur(role=Role.UTILISATEUR):
    """Fabrique un utilisateur de test."""
    return Utilisateur(id=1, nom_utilisateur="alice", role=role, actif=True)


def test_utilisateur_courant_transmet_le_jeton_et_renvoie_l_utilisateur():
    """Le jeton de l'en-tête est transmis au service, qui renvoie l'utilisateur."""
    alice = creer_utilisateur()
    service = FauxAuthentificationService(utilisateur=alice)
    identifiants = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mon-jeton")

    resultat = utilisateur_courant(identifiants=identifiants, service=service)

    assert resultat is alice
    assert service.jeton_recu == "mon-jeton"


def test_utilisateur_courant_sans_en_tete_transmet_none():
    """Sans en-tête Authorization, le service reçoit None (et lèvera AuthentificationEchouee)."""
    service = FauxAuthentificationService(
        erreur=AuthentificationEchouee("Authentification requise.")
    )

    with pytest.raises(AuthentificationEchouee):
        utilisateur_courant(identifiants=None, service=service)

    assert service.jeton_recu is None


def test_utilisateur_courant_laisse_remonter_les_erreurs():
    """Un compte désactivé (AccesRefuse) remonte tel quel jusqu'au gestionnaire global."""
    service = FauxAuthentificationService(erreur=AccesRefuse("Ce compte est désactivé."))
    identifiants = HTTPAuthorizationCredentials(scheme="Bearer", credentials="x")

    with pytest.raises(AccesRefuse):
        utilisateur_courant(identifiants=identifiants, service=service)


def test_exiger_connexion_renvoie_l_utilisateur_courant():
    """exiger_connexion renvoie l'utilisateur déjà retrouvé par utilisateur_courant."""
    alice = creer_utilisateur()

    assert exiger_connexion(utilisateur=alice) is alice


def test_exiger_admin_avec_un_administrateur():
    """Un administrateur passe le contrôle et est renvoyé."""
    admin = creer_utilisateur(Role.ADMIN)

    assert exiger_admin(utilisateur=admin, service=FauxAuthentificationService()) is admin


def test_exiger_admin_avec_un_utilisateur_standard():
    """Un utilisateur standard lève AccesRefuse (réponse 403)."""
    with pytest.raises(AccesRefuse):
        exiger_admin(utilisateur=creer_utilisateur(), service=FauxAuthentificationService())
