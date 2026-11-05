"""Tests du service de gestion des comptes, sans base de données.

Le principe est tel qu'on donne au service un faux DAO et un vrai JournalService
branché sur un faux DAO de journal, pour vérifier ce qui est tracé.
"""

from datetime import datetime

import pytest

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from service.authentification_service import AuthentificationService
from service.journal_service import JournalService
from service.utilisateur_service import (
    ACTION_DESACTIVATION,
    ACTION_PROMOTION,
    ACTION_REACTIVATION,
    ACTION_RETROGRADATION,
    UtilisateurService,
)
from utils.exceptions import (
    AccesRefuse,
    ConflitRessource,
    DonneesInvalides,
    RessourceIntrouvable,
)

# Faux DAO et outils de test


class FauxUtilisateurDao:
    """Faux DAO d'utilisateurs garde les comptes dans une liste en mémoire."""

    def __init__(self, utilisateurs):
        """Garde la liste de comptes fournie."""
        self.utilisateurs = utilisateurs

    def lister(self):
        """Renvoie tous les comptes triés par identifiant."""
        return sorted(self.utilisateurs, key=lambda utilisateur: utilisateur.id)

    def trouver_par_id(self, id):
        """Renvoie le compte portant cet identifiant, ou None."""
        for utilisateur in self.utilisateurs:
            if utilisateur.id == id:
                return utilisateur
        return None

    def trouver_par_nom(self, nom_utilisateur):
        """Renvoie le compte portant ce nom, ou None."""
        for utilisateur in self.utilisateurs:
            if utilisateur.nom_utilisateur == nom_utilisateur:
                return utilisateur
        return None

    def modifier(self, utilisateur):
        """Imite la mise à jour en base ; renvoie True si le compte existe."""
        return self.trouver_par_id(utilisateur.id) is not None


class FauxJournalDao:
    """Faux DAO du journal garde les entrées dans une liste en mémoire."""

    def __init__(self):
        """Démarre avec un journal vide."""
        self.entrees = []

    def creer(self, entree):
        """Ajoute l'entrée avec un identifiant et une date, puis la renvoie."""
        entree.id = len(self.entrees) + 1
        entree.date_heure = datetime.now()
        self.entrees.append(entree)
        return entree

    def lister(self):
        """Renvoie les entrées de la plus récente à la plus ancienne."""
        return list(reversed(self.entrees))


class FausseSecurite:
    """Fausse sécurité minimale, utilisée seulement pour lire un jeton 'jeton-<id>'."""

    def lire_jeton(self, jeton):
        """Renvoie l'identifiant d'un jeton 'jeton-<id>', sinon lève ValueError."""
        if not jeton.startswith("jeton-"):
            raise ValueError("Jeton invalide")
        return int(jeton.removeprefix("jeton-"))


def creer_comptes():
    """Fabrique 4 comptes à savoir 2 administrateurs actifs, 1 utilisateur actif, 1 désactivé."""
    return [
        Utilisateur(id=1, nom_utilisateur="jade", mot_de_passe_hash="hash:secret1",
                    role=Role.ADMIN, actif=True),
        Utilisateur(id=2, nom_utilisateur="vicram", mot_de_passe_hash="hash:secret2",
                    role=Role.UTILISATEUR, actif=True),
        Utilisateur(id=3, nom_utilisateur="salim", mot_de_passe_hash="hash:secret3",
                    role=Role.UTILISATEUR, actif=False),
        Utilisateur(id=4, nom_utilisateur="alexandre", mot_de_passe_hash="hash:secret4",
                    role=Role.ADMIN, actif=True),
    ]  # fmt: skip


def creer_service():
    """Fabrique un service branché sur de faux DAO, avec les 4 comptes de test."""
    journal = JournalService(journal_dao=FauxJournalDao())
    return UtilisateurService(
        utilisateur_dao=FauxUtilisateurDao(creer_comptes()), journal_service=journal
    )


def compte(service, nom):
    """Renvoie le compte de ce nom (pour vérifier son état après une action)."""
    return service.utilisateur_dao.trouver_par_nom(nom)


def entrees_journal(service):
    """Renvoie les entrées écrites dans le journal."""
    return service.journal_service.journal_dao.entrees


# Consultation


def test_lister_utilisateurs():
    """Un administrateur obtient tous les comptes."""
    service = creer_service()

    resultat = service.lister_utilisateurs(compte(service, "jade"))

    assert [u.nom_utilisateur for u in resultat] == ["jade", "vicram", "salim", "alexandre"]


def test_lister_utilisateurs_refuse_a_un_utilisateur_standard():
    """Un utilisateur standard ne peut pas lister les comptes."""
    service = creer_service()

    with pytest.raises(AccesRefuse):
        service.lister_utilisateurs(compte(service, "vicram"))


def test_acteur_administrateur_desactive_refuse():
    """Un administrateur dont le compte est désactivé n'a plus aucun droit."""
    service = creer_service()
    compte(service, "jade").actif = False

    with pytest.raises(AccesRefuse):
        service.lister_utilisateurs(compte(service, "jade"))


def test_acteur_absent_refuse():
    """Sans acteur (None), l'accès est refusé."""
    service = creer_service()

    with pytest.raises(AccesRefuse):
        service.lister_utilisateurs(None)


def test_trouver_utilisateur():
    """Un administrateur retrouve un compte par son identifiant."""
    service = creer_service()

    assert service.trouver_utilisateur(compte(service, "jade"), 2).nom_utilisateur == "vicram"


def test_trouver_utilisateur_inconnu():
    """Un identifiant inexistant leve RessourceIntrouvable."""
    service = creer_service()

    with pytest.raises(RessourceIntrouvable):
        service.trouver_utilisateur(compte(service, "jade"), 999)


@pytest.mark.parametrize("identifiant_invalide", [0, -1, "2", None, 2.5, True])
def test_trouver_utilisateur_identifiant_invalide(identifiant_invalide):
    """Un identifiant qui n'est pas un entier positif lève DonneesInvalides."""
    service = creer_service()

    with pytest.raises(DonneesInvalides):
        service.trouver_utilisateur(compte(service, "jade"), identifiant_invalide)


def test_trouver_utilisateur_refuse_a_un_utilisateur_standard():
    """Un utilisateur standard ne peut pas consulter un compte."""
    service = creer_service()

    with pytest.raises(AccesRefuse):
        service.trouver_utilisateur(compte(service, "vicram"), 1)


# Promotion et rétrogradation


def test_promouvoir_admin():
    """Le compte devient administrateur et l'action est tracée dans le journal."""
    service = creer_service()
    jade = compte(service, "jade")

    resultat = service.promouvoir_admin(jade, 2)

    assert resultat.role is Role.ADMIN
    assert compte(service, "vicram").role is Role.ADMIN
    assert len(entrees_journal(service)) == 1
    entree = entrees_journal(service)[0]
    assert entree.action == ACTION_PROMOTION
    assert entree.utilisateur_id == jade.id
    assert entree.cible == "utilisateur:2"


def test_promouvoir_admin_deja_administrateur():
    """Promouvoir un administrateur lève ConflitRessource et n'écrit rien dans le journal."""
    service = creer_service()

    with pytest.raises(ConflitRessource):
        service.promouvoir_admin(compte(service, "jade"), 4)

    assert entrees_journal(service) == []


def test_promouvoir_admin_refuse_a_un_utilisateur_standard():
    """Un utilisateur standard ne peut pas se promouvoir, rien ne change."""
    service = creer_service()

    with pytest.raises(AccesRefuse):
        service.promouvoir_admin(compte(service, "vicram"), 2)

    assert compte(service, "vicram").role is Role.UTILISATEUR
    assert entrees_journal(service) == []


def test_promouvoir_admin_compte_inconnu():
    """Promouvoir un compte inexistant leve RessourceIntrouvable."""
    service = creer_service()

    with pytest.raises(RessourceIntrouvable):
        service.promouvoir_admin(compte(service, "jade"), 999)


def test_retrograder_admin():
    """Le compte redevient utilisateur standard et l'action est tracée."""
    service = creer_service()

    resultat = service.retrograder_admin(compte(service, "jade"), 4)

    assert resultat.role is Role.UTILISATEUR
    assert compte(service, "alexandre").role is Role.UTILISATEUR
    assert entrees_journal(service)[0].action == ACTION_RETROGRADATION
    assert entrees_journal(service)[0].cible == "utilisateur:4"


def test_retrograder_admin_cible_non_administrateur():
    """Rétrograder un utilisateur standard lève ConflitRessource."""
    service = creer_service()

    with pytest.raises(ConflitRessource):
        service.retrograder_admin(compte(service, "jade"), 2)

    assert entrees_journal(service) == []


def test_retrograder_admin_son_propre_compte():
    """Un administrateur ne peut pas retirer ses propres droits."""
    service = creer_service()

    with pytest.raises(DonneesInvalides):
        service.retrograder_admin(compte(service, "jade"), 1)

    assert compte(service, "jade").role is Role.ADMIN
    assert entrees_journal(service) == []


def test_il_reste_toujours_un_administrateur_actif():
    """Après avoir rétrogradé l'autre administrateur, le dernier ne peut plus se rétrograder."""
    service = creer_service()
    jade = compte(service, "jade")

    service.retrograder_admin(jade, 4)
    with pytest.raises(DonneesInvalides):
        service.retrograder_admin(jade, 1)

    assert compte(service, "jade").role is Role.ADMIN


# Désactivation et réactivation


def test_desactiver():
    """Le compte est désactivé et l'action est tracée dans le journal."""
    service = creer_service()
    jade = compte(service, "jade")

    resultat = service.definir_activation(jade, 2, actif=False)

    assert resultat.actif is False
    assert compte(service, "vicram").actif is False
    entree = entrees_journal(service)[0]
    assert entree.action == ACTION_DESACTIVATION
    assert entree.utilisateur_id == jade.id
    assert entree.cible == "utilisateur:2"


def test_desactiver_un_autre_administrateur():
    """Un administrateur peut désactiver un autre administrateur."""
    service = creer_service()

    assert service.definir_activation(compte(service, "jade"), 4, actif=False).actif is False


def test_desactiver_deja_desactive():
    """Désactiver un compte déjà désactivé lève ConflitRessource."""
    service = creer_service()

    with pytest.raises(ConflitRessource):
        service.definir_activation(compte(service, "jade"), 3, actif=False)

    assert entrees_journal(service) == []


def test_desactiver_son_propre_compte():
    """Un administrateur ne peut pas désactiver son propre compte."""
    service = creer_service()

    with pytest.raises(DonneesInvalides):
        service.definir_activation(compte(service, "jade"), 1, actif=False)

    assert compte(service, "jade").actif is True


def test_desactiver_refuse_a_un_utilisateur_standard():
    """Un utilisateur standard ne peut pas désactiver un compte."""
    service = creer_service()

    with pytest.raises(AccesRefuse):
        service.definir_activation(compte(service, "vicram"), 4, actif=False)

    assert compte(service, "alexandre").actif is True


def test_reactiver():
    """Le compte est réactivé et l'action est tracée dans le journal."""
    service = creer_service()

    resultat = service.definir_activation(compte(service, "jade"), 3, actif=True)

    assert resultat.actif is True
    assert compte(service, "salim").actif is True
    assert entrees_journal(service)[0].action == ACTION_REACTIVATION


def test_reactiver_deja_actif():
    """Réactiver un compte déjà actif lève ConflitRessource."""
    service = creer_service()

    with pytest.raises(ConflitRessource):
        service.definir_activation(compte(service, "jade"), 2, actif=True)

    assert entrees_journal(service) == []


@pytest.mark.parametrize("etat_invalide", ["false", "true", 0, 1, None])
def test_definir_activation_etat_invalide(etat_invalide):
    """L'état demandé doit être un vrai booléen. texte, nombre ou None sont refusés."""
    service = creer_service()

    with pytest.raises(DonneesInvalides):
        service.definir_activation(compte(service, "jade"), 2, actif=etat_invalide)

    assert compte(service, "vicram").actif is True
    assert entrees_journal(service) == []


def test_definir_activation_droits_verifies_avant_l_etat():
    """Un utilisateur standard reçoit AccesRefuse, même avec un état invalide."""
    service = creer_service()

    with pytest.raises(AccesRefuse):
        service.definir_activation(compte(service, "vicram"), 2, actif="n-importe-quoi")


def test_definir_activation_compte_inconnu():
    """Un compte inexistant lève RessourceIntrouvable."""
    service = creer_service()

    with pytest.raises(RessourceIntrouvable):
        service.definir_activation(compte(service, "jade"), 999, actif=False)


@pytest.mark.parametrize("identifiant_invalide", [0, -1, "2", None])
def test_definir_activation_identifiant_invalide(identifiant_invalide):
    """Un identifiant qui n'est pas un entier positif lève DonneesInvalides."""
    service = creer_service()

    with pytest.raises(DonneesInvalides):
        service.definir_activation(compte(service, "jade"), identifiant_invalide, actif=False)


def test_definir_activation_aller_retour():
    """On peut désactiver puis réactiver le même compte : deux entrées dans le journal."""
    service = creer_service()
    jade = compte(service, "jade")

    service.definir_activation(jade, 2, actif=False)
    assert compte(service, "vicram").actif is False
    service.definir_activation(jade, 2, actif=True)
    assert compte(service, "vicram").actif is True

    assert [e.action for e in entrees_journal(service)] == [
        ACTION_DESACTIVATION,
        ACTION_REACTIVATION,
    ]


# Journal, modification disparue et effet immédiat


def test_le_journal_ne_contient_jamais_d_empreinte_de_mot_de_passe():
    """Ni la cible ni les détails de l'entrée ne contiennent l'empreinte du mot de passe."""
    service = creer_service()

    service.definir_activation(compte(service, "jade"), 2, actif=False)

    entree = entrees_journal(service)[0]
    assert "secret2" not in (entree.cible or "")
    assert "secret2" not in (entree.details or "")
    assert "vicram" in entree.details  # le nom, lui, est utile pour le suivi


def test_chaque_action_ajoute_une_entree_au_journal():
    """Trois actions successives donnent trois entrées, dans l'ordre."""
    service = creer_service()
    jade = compte(service, "jade")

    service.promouvoir_admin(jade, 2)
    service.definir_activation(jade, 4, actif=False)  # désactive salim
    service.definir_activation(jade, 3, actif=True)

    assert [e.action for e in entrees_journal(service)] == [
        ACTION_PROMOTION,
        ACTION_DESACTIVATION,
        ACTION_REACTIVATION,
    ]


def test_modification_refusee_par_le_dao_leve_ressource_introuvable():
    """Si le DAO ne trouve plus le compte à la modification, rien n'est tracé."""
    service = creer_service()
    service.utilisateur_dao.modifier = lambda utilisateur: False

    with pytest.raises(RessourceIntrouvable):
        service.definir_activation(compte(service, "jade"), 2, actif=False)

    assert entrees_journal(service) == []


def test_desactivation_bloque_immediatement_le_jeton_existant():
    """Après désactivation, le jeton déjà émis par le compte ne fonctionne plus."""
    service = creer_service()
    authentification = AuthentificationService(
        utilisateur_dao=service.utilisateur_dao, securite=FausseSecurite()
    )
    assert authentification.utilisateur_depuis_jeton("jeton-2").nom_utilisateur == "vicram"

    service.definir_activation(compte(service, "jade"), 2, actif=False)

    with pytest.raises(AccesRefuse):
        authentification.utilisateur_depuis_jeton("jeton-2")
