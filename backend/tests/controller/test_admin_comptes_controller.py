"""Tests des routes d'administration des comptes et du journal, avec de faux services.

On appelle directement les fonctions des routes. Les erreurs métier doivent remonter
sans être interceptées (le gestionnaire global les transformera en codes HTTP).
"""

from datetime import datetime

import pytest

from business_object.enums import Role
from business_object.journal_activite import JournalActivite
from business_object.utilisateur import Utilisateur
from controller.admin_comptes_controller import (
    changer_activation,
    changer_role,
    consulter_journal,
    lister_utilisateurs,
)
from model.utilisateur_model import ChangementActivation, ChangementRole
from utils.exceptions import ConflitRessource, RessourceIntrouvable


def creer_compte(id, nom, role=Role.UTILISATEUR, actif=True):
    """Fabrique un compte de test (avec une empreinte qui ne doit jamais sortir)."""
    return Utilisateur(
        id=id, nom_utilisateur=nom, mot_de_passe_hash="hash-secret", role=role, actif=actif
    )


class FauxUtilisateurService:
    """Faux service des comptes, il note les appels et renvoie des comptes fixes."""

    def __init__(self, erreur=None):
        """Si une erreur est fournie, chaque méthode la lève."""
        self.erreur = erreur
        self.appel = None

    def _repondre(self, appel, resultat):
        """Note l'appel, lève l'erreur prévue ou renvoie le résultat."""
        self.appel = appel
        if self.erreur is not None:
            raise self.erreur
        return resultat

    def lister_utilisateurs(self, acteur):
        """Imite UtilisateurService.lister_utilisateurs."""
        return self._repondre(
            ("lister", acteur.id), [creer_compte(1, "chef", Role.ADMIN), creer_compte(2, "alice")]
        )

    def promouvoir_admin(self, acteur, id_utilisateur):
        """Imite UtilisateurService.promouvoir_admin."""
        return self._repondre(
            ("promouvoir", acteur.id, id_utilisateur), creer_compte(id_utilisateur, "x", Role.ADMIN)
        )

    def retrograder_admin(self, acteur, id_utilisateur):
        """Imite UtilisateurService.retrograder_admin."""
        return self._repondre(
            ("retrograder", acteur.id, id_utilisateur), creer_compte(id_utilisateur, "x")
        )

    def definir_activation(self, acteur, id_utilisateur, actif):
        """Imite UtilisateurService.definir_activation."""
        return self._repondre(
            ("activation", acteur.id, id_utilisateur, actif),
            creer_compte(id_utilisateur, "x", actif=actif),
        )


class FauxJournalService:
    """Faux service du journal : il note les paramètres et renvoie une entrée fixe."""

    def __init__(self):
        """Démarre sans appel enregistré."""
        self.appel = None

    def lister(self, acteur, utilisateur_id=None, action=None, limite=100):
        """Imite JournalService.lister."""
        self.appel = (acteur.id, utilisateur_id, action, limite)
        return [
            JournalActivite(
                id=1,
                utilisateur_id=1,
                action="PROMOTION_ADMIN",
                cible="utilisateur:2",
                details="alice : utilisateur -> admin",
                date_heure=datetime(2026, 11, 3),
            )
        ]


ADMIN = Utilisateur(id=1, nom_utilisateur="chef", role=Role.ADMIN, actif=True)


def test_lister_utilisateurs_sans_empreinte():
    """La liste des comptes ne contient jamais d'empreinte de mot de passe."""
    service = FauxUtilisateurService()

    resultat = lister_utilisateurs(acteur=ADMIN, service=service)

    assert [u.nom_utilisateur for u in resultat] == ["chef", "alice"]
    assert all("hash-secret" not in u.model_dump_json() for u in resultat)
    assert service.appel == ("lister", 1)


def test_changer_role_vers_admin_promeut():
    """Demander le rôle 'admin' appelle promouvoir_admin."""
    service = FauxUtilisateurService()

    resultat = changer_role(2, ChangementRole(role="admin"), acteur=ADMIN, service=service)

    assert service.appel == ("promouvoir", 1, 2)
    assert resultat.role is Role.ADMIN


def test_changer_role_vers_utilisateur_retrograde():
    """Demander le rôle 'utilisateur' appelle retrograder_admin."""
    service = FauxUtilisateurService()

    resultat = changer_role(4, ChangementRole(role="utilisateur"), acteur=ADMIN, service=service)

    assert service.appel == ("retrograder", 1, 4)
    assert resultat.role is Role.UTILISATEUR


@pytest.mark.parametrize("etat", [True, False])
def test_changer_activation_transmet_l_etat(etat):
    """L'état demandé (true ou false) est transmis tel quel au service."""
    service = FauxUtilisateurService()

    resultat = changer_activation(
        3, ChangementActivation(actif=etat), acteur=ADMIN, service=service
    )

    assert service.appel == ("activation", 1, 3, etat)
    assert resultat.actif is etat
    assert "hash-secret" not in resultat.model_dump_json()


def test_changer_role_laisse_remonter_les_erreurs():
    """Un compte inconnu (RessourceIntrouvable) remonte : 404 via le gestionnaire global."""
    service = FauxUtilisateurService(erreur=RessourceIntrouvable("Inconnu."))

    with pytest.raises(RessourceIntrouvable):
        changer_role(99, ChangementRole(role="admin"), acteur=ADMIN, service=service)


def test_changer_activation_laisse_remonter_les_erreurs():
    """Un compte déjà dans l'état demandé (ConflitRessource) remonte : 409 via le gestionnaire."""
    service = FauxUtilisateurService(erreur=ConflitRessource("Déjà désactivé."))

    with pytest.raises(ConflitRessource):
        changer_activation(3, ChangementActivation(actif=False), acteur=ADMIN, service=service)


def test_consulter_journal_transmet_les_filtres():
    """Les filtres et la limite sont transmis au service du journal."""
    service = FauxJournalService()

    resultat = consulter_journal(
        utilisateur_id=1, action="PROMOTION_ADMIN", limite=10, acteur=ADMIN, service=service
    )

    assert service.appel == (1, 1, "PROMOTION_ADMIN", 10)
    assert resultat[0].action == "PROMOTION_ADMIN"
    assert resultat[0].cible == "utilisateur:2"
