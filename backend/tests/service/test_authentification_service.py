"""Tests du service d'authentification, sans base de données.

Principe : on donne au service un faux DAO (liste d'utilisateurs en mémoire) et une
fausse sécurité (hachage et jetons très simples). On teste ainsi uniquement la
logique du service. Un dernier test utilise la vraie sécurité pour vérifier que
le branchement par défaut fonctionne.
"""

from datetime import datetime

import pytest

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from service.authentification_service import AuthentificationService
from utils import securite
from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    DonneesInvalides,
)

# Faux DAO, fausse sécurité et outils de test


class FauxUtilisateurDao:
    """Faux DAO d'utilisateurs : il garde les comptes dans une liste en mémoire."""

    def __init__(self):
        """Démarre sans aucun compte."""
        self.utilisateurs = []
        self.prochain_id = 1

    def creer(self, utilisateur):
        """Ajoute le compte avec un identifiant et une date de création, puis le renvoie."""
        utilisateur.id = self.prochain_id
        utilisateur.date_creation = datetime.now()
        self.prochain_id += 1
        self.utilisateurs.append(utilisateur)
        return utilisateur

    def trouver_par_nom(self, nom_utilisateur):
        """Renvoie le compte portant ce nom, ou None."""
        for utilisateur in self.utilisateurs:
            if utilisateur.nom_utilisateur == nom_utilisateur:
                return utilisateur
        return None

    def trouver_par_id(self, id):
        """Renvoie le compte portant cet identifiant, ou None."""
        for utilisateur in self.utilisateurs:
            if utilisateur.id == id:
                return utilisateur
        return None

    def modifier(self, utilisateur):
        """Imite la mise à jour en base ; renvoie True si le compte existe."""
        return self.trouver_par_id(utilisateur.id) is not None


class FausseSecurite:
    """Fausse sécurité : hachage et jetons très simples (et rapides) pour les tests."""

    def hacher_mot_de_passe(self, mot_de_passe):
        """'Hache' le mot de passe en ajoutant un préfixe."""
        return "hash:" + mot_de_passe

    def verifier_mot_de_passe(self, mot_de_passe, mot_de_passe_hash):
        """Compare le mot de passe avec l'empreinte."""
        return mot_de_passe_hash == "hash:" + mot_de_passe

    def creer_jeton(self, id_utilisateur):
        """Crée un jeton de la forme 'jeton-<id>'."""
        return f"jeton-{id_utilisateur}"

    def lire_jeton(self, jeton):
        """Renvoie l'identifiant d'un jeton 'jeton-<id>', sinon lève ValueError."""
        if not jeton.startswith("jeton-"):
            raise ValueError("Jeton invalide")
        return int(jeton.removeprefix("jeton-"))


def creer_service():
    """Fabrique un service branché sur un faux DAO et une fausse sécurité."""
    return AuthentificationService(utilisateur_dao=FauxUtilisateurDao(), securite=FausseSecurite())


def creer_service_avec_compte(nom="alice", mot_de_passe="Motdepasse1", **options):
    """Fabrique un service contenant déjà un compte (options : role, actif)."""
    service = creer_service()
    utilisateur = service.inscrire(nom, mot_de_passe)
    for attribut, valeur in options.items():
        setattr(utilisateur, attribut, valeur)
    return service


# Inscription


def test_inscrire_cree_un_compte_standard():
    """L'inscription renvoie un compte actif avec le rôle utilisateur et un identifiant."""
    service = creer_service()

    utilisateur = service.inscrire("alice", "Motdepasse1")

    assert utilisateur.id == 1
    assert utilisateur.nom_utilisateur == "alice"
    assert utilisateur.role is Role.UTILISATEUR
    assert utilisateur.actif is True


def test_inscrire_ne_stocke_pas_le_mot_de_passe_en_clair():
    """Le compte enregistré contient l'empreinte, jamais le mot de passe."""
    service = creer_service()

    utilisateur = service.inscrire("alice", "Motdepasse1")

    assert utilisateur.mot_de_passe_hash == "hash:Motdepasse1"
    assert "Motdepasse1" not in vars(utilisateur).values()


def test_inscrire_nom_normalise_en_minuscules_sans_espaces():
    """Le nom est enregistré en minuscules, sans espaces autour."""
    service = creer_service()

    utilisateur = service.inscrire("  Alice  ", "Motdepasse1")

    assert utilisateur.nom_utilisateur == "alice"


def test_inscrire_nom_deja_pris():
    """Un nom déjà utilisé lève ConflitRessource."""
    service = creer_service()
    service.inscrire("alice", "Motdepasse1")

    with pytest.raises(ConflitRessource):
        service.inscrire("alice", "AutreMotdepasse2")


def test_inscrire_nom_deja_pris_avec_une_autre_casse():
    """'ALICE' est considéré comme le même nom que 'alice'."""
    service = creer_service()
    service.inscrire("alice", "Motdepasse1")

    with pytest.raises(ConflitRessource):
        service.inscrire("ALICE", "AutreMotdepasse2")


@pytest.mark.parametrize(
    "nom_invalide",
    [None, 123, "", "   ", "ab", "a" * 51, "nom avec espace", "né", "alice!", "a/b/c"],
)
def test_inscrire_nom_invalide(nom_invalide):
    """Un nom absent, trop court, trop long ou avec des caractères interdits est refusé."""
    service = creer_service()

    with pytest.raises(DonneesInvalides):
        service.inscrire(nom_invalide, "Motdepasse1")


@pytest.mark.parametrize("nom_valide", ["abc", "a" * 50, "a.b_c-d", "user123"])
def test_inscrire_nom_valide(nom_valide):
    """Les noms aux limites de longueur et avec . _ - sont acceptés."""
    service = creer_service()

    assert service.inscrire(nom_valide, "Motdepasse1").nom_utilisateur == nom_valide


@pytest.mark.parametrize(
    "mot_de_passe_invalide",
    [None, 12345678, "", "court1", "a" * 128 + "1", "motdepasse", "12345678"],
)
def test_inscrire_mot_de_passe_invalide(mot_de_passe_invalide):
    """Un mot de passe absent, trop court, trop long, sans chiffre ou sans lettre est refusé."""
    service = creer_service()

    with pytest.raises(DonneesInvalides):
        service.inscrire("alice", mot_de_passe_invalide)


@pytest.mark.parametrize("mot_de_passe_valide", ["abcdef12", "a" * 127 + "1", "Mdp-éàç-123"])
def test_inscrire_mot_de_passe_valide(mot_de_passe_valide):
    """Les mots de passe aux limites de longueur (8 et 128) sont acceptés."""
    service = creer_service()

    assert service.inscrire("alice", mot_de_passe_valide).id == 1


def test_inscrire_mot_de_passe_egal_au_nom():
    """Un mot de passe identique au nom d'utilisateur est refusé (même avec une autre casse)."""
    service = creer_service()

    with pytest.raises(DonneesInvalides):
        service.inscrire("alice2024", "ALICE2024")


def test_inscrire_refus_ne_cree_aucun_compte():
    """Quand l'inscription est refusée, rien n'est enregistré."""
    dao = FauxUtilisateurDao()
    service = AuthentificationService(utilisateur_dao=dao, securite=FausseSecurite())

    with pytest.raises(DonneesInvalides):
        service.inscrire("alice", "court")

    assert dao.utilisateurs == []


# Connexion


def test_connecter_renvoie_un_jeton():
    """Avec les bons identifiants, on obtient le jeton de l'utilisateur."""
    service = creer_service_avec_compte()

    assert service.connecter("alice", "Motdepasse1") == "jeton-1"


def test_connecter_enregistre_la_derniere_connexion():
    """La date de dernière connexion est renseignée après une connexion réussie."""
    service = creer_service_avec_compte()
    assert service.utilisateur_dao.trouver_par_nom("alice").derniere_connexion is None

    service.connecter("alice", "Motdepasse1")

    assert service.utilisateur_dao.trouver_par_nom("alice").derniere_connexion is not None


def test_connecter_nom_insensible_a_la_casse_et_aux_espaces():
    """'  ALICE ' se connecte au compte 'alice'."""
    service = creer_service_avec_compte()

    assert service.connecter("  ALICE ", "Motdepasse1") == "jeton-1"


def test_connecter_mot_de_passe_sensible_a_la_casse():
    """Le mot de passe, lui, est sensible à la casse."""
    service = creer_service_avec_compte()

    with pytest.raises(AuthentificationEchouee):
        service.connecter("alice", "motdepasse1")


def test_connecter_mauvais_mot_de_passe():
    """Un mauvais mot de passe lève AuthentificationEchouee."""
    service = creer_service_avec_compte()

    with pytest.raises(AuthentificationEchouee):
        service.connecter("alice", "MauvaisMotdepasse9")


def test_connecter_utilisateur_inconnu_meme_message_que_mauvais_mot_de_passe():
    """Le message ne permet pas de savoir si le nom d'utilisateur existe."""
    service = creer_service_avec_compte()

    with pytest.raises(AuthentificationEchouee) as inconnu:
        service.connecter("personne", "Motdepasse1")
    with pytest.raises(AuthentificationEchouee) as mauvais_mdp:
        service.connecter("alice", "MauvaisMotdepasse9")

    assert str(inconnu.value) == str(mauvais_mdp.value)


def test_connecter_echec_ne_modifie_pas_la_derniere_connexion():
    """Une connexion échouée ne met pas à jour la date de dernière connexion."""
    service = creer_service_avec_compte()

    with pytest.raises(AuthentificationEchouee):
        service.connecter("alice", "MauvaisMotdepasse9")

    assert service.utilisateur_dao.trouver_par_nom("alice").derniere_connexion is None


def test_connecter_compte_desactive():
    """Un compte désactivé avec le bon mot de passe lève AccesRefuse."""
    service = creer_service_avec_compte(actif=False)

    with pytest.raises(AccesRefuse):
        service.connecter("alice", "Motdepasse1")


def test_connecter_compte_desactive_mauvais_mot_de_passe():
    """Avec un mauvais mot de passe, on ne révèle pas que le compte est désactivé."""
    service = creer_service_avec_compte(actif=False)

    with pytest.raises(AuthentificationEchouee):
        service.connecter("alice", "MauvaisMotdepasse9")


@pytest.mark.parametrize(
    ("nom", "mot_de_passe"),
    [
        ("", "Motdepasse1"),
        ("   ", "Motdepasse1"),
        ("alice", ""),
        (None, "Motdepasse1"),
        ("alice", None),
    ],
)
def test_connecter_champs_vides(nom, mot_de_passe):
    """Un nom ou un mot de passe vide ou absent lève DonneesInvalides."""
    service = creer_service_avec_compte()

    with pytest.raises(DonneesInvalides):
        service.connecter(nom, mot_de_passe)


def test_connecter_mot_de_passe_trop_long():
    """Un mot de passe de plus de 128 caractères est refusé comme incorrect."""
    service = creer_service_avec_compte()

    with pytest.raises(AuthentificationEchouee):
        service.connecter("alice", "a" * 129)


# Retrouver l'utilisateur à partir du jeton


def test_utilisateur_depuis_jeton():
    """Un jeton valide donne l'utilisateur correspondant."""
    service = creer_service_avec_compte()
    jeton = service.connecter("alice", "Motdepasse1")

    utilisateur = service.utilisateur_depuis_jeton(jeton)

    assert utilisateur.nom_utilisateur == "alice"


@pytest.mark.parametrize("jeton_absent", [None, ""])
def test_utilisateur_depuis_jeton_absent(jeton_absent):
    """Sans jeton, on lève AuthentificationEchouee."""
    service = creer_service_avec_compte()

    with pytest.raises(AuthentificationEchouee):
        service.utilisateur_depuis_jeton(jeton_absent)


def test_utilisateur_depuis_jeton_invalide():
    """Un jeton invalide ou expiré (la sécurité lève ValueError) donne AuthentificationEchouee."""
    service = creer_service_avec_compte()

    with pytest.raises(AuthentificationEchouee):
        service.utilisateur_depuis_jeton("n-importe-quoi")


def test_utilisateur_depuis_jeton_utilisateur_supprime():
    """Un jeton valide dont l'utilisateur n'existe plus est refusé."""
    service = creer_service_avec_compte()

    with pytest.raises(AuthentificationEchouee):
        service.utilisateur_depuis_jeton("jeton-999")


def test_utilisateur_depuis_jeton_compte_desactive_apres_connexion():
    """Si le compte est désactivé après l'émission du jeton, le jeton ne marche plus."""
    service = creer_service_avec_compte()
    jeton = service.connecter("alice", "Motdepasse1")
    service.utilisateur_dao.trouver_par_nom("alice").actif = False

    with pytest.raises(AccesRefuse):
        service.utilisateur_depuis_jeton(jeton)


def test_utilisateur_depuis_jeton_relit_le_role_en_base():
    """Une promotion en administrateur est prise en compte avec le même jeton."""
    service = creer_service_avec_compte()
    jeton = service.connecter("alice", "Motdepasse1")
    assert service.utilisateur_depuis_jeton(jeton).role is Role.UTILISATEUR

    service.utilisateur_dao.trouver_par_nom("alice").role = Role.ADMIN

    assert service.utilisateur_depuis_jeton(jeton).role is Role.ADMIN


## Contrôle du rôle


def test_exiger_admin_avec_un_administrateur():
    """Un administrateur passe le contrôle et est renvoyé."""
    service = creer_service()
    admin = Utilisateur(id=1, nom_utilisateur="chef", role=Role.ADMIN)

    assert service.exiger_admin(admin) is admin


def test_exiger_admin_avec_un_utilisateur_standard():
    """Un utilisateur standard lève AccesRefuse."""
    service = creer_service()
    standard = Utilisateur(id=2, nom_utilisateur="alice", role=Role.UTILISATEUR)

    with pytest.raises(AccesRefuse):
        service.exiger_admin(standard)


# Parcours complet avec la vraie sécurité


def test_parcours_complet_avec_la_vraie_securite(monkeypatch):
    """Inscription, connexion puis retour de l'utilisateur, avec utils.securite par défaut."""
    monkeypatch.setenv("JWT_SECRET_KEY", "cle-secrete-de-test")
    monkeypatch.setattr(securite, "ITERATIONS", 1000)  # hachage rapide pour le test
    service = AuthentificationService(utilisateur_dao=FauxUtilisateurDao())

    service.inscrire("alice", "Motdepasse1")
    jeton = service.connecter("alice", "Motdepasse1")
    utilisateur = service.utilisateur_depuis_jeton(jeton)

    assert utilisateur.nom_utilisateur == "alice"
    with pytest.raises(AuthentificationEchouee):
        service.connecter("alice", "MauvaisMotdepasse9")
    with pytest.raises(AuthentificationEchouee):
        service.utilisateur_depuis_jeton(jeton + "x")