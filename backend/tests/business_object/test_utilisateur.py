"""Tests unitaires de l'objet métier Utilisateur."""

from datetime import datetime

from business_object.enums import Role
from business_object.utilisateur import Utilisateur


def test_initialisation_par_defaut():
    """Un Utilisateur sans argument a ses attributs à None, sauf role (UTILISATEUR) et actif (True)."""
    user = Utilisateur()

    assert user.id is None
    assert user.nom_utilisateur is None
    assert user.mot_de_passe_hash is None
    assert user.role == Role.UTILISATEUR
    assert user.actif is True
    assert user.date_creation is None
    assert user.derniere_connexion is None


def test_initialisation_complete():
    """Un Utilisateur construit avec tous les attributs les conserve tels quels."""
    date_creation = datetime(2024, 1, 1, 8, 0, 0)
    derniere_connexion = datetime(2024, 11, 20, 15, 30, 0)
    user = Utilisateur(
        id=1,
        nom_utilisateur="alice",
        mot_de_passe_hash="abc123hash",
        role=Role.ADMIN,
        actif=True,
        date_creation=date_creation,
        derniere_connexion=derniere_connexion,
    )

    assert user.id == 1
    assert user.nom_utilisateur == "alice"
    assert user.mot_de_passe_hash == "abc123hash"
    assert user.role == Role.ADMIN
    assert user.actif is True
    assert user.date_creation == date_creation
    assert user.derniere_connexion == derniere_connexion


def test_role_par_defaut_utilisateur():
    """Le rôle par défaut est UTILISATEUR."""
    user = Utilisateur()

    assert user.role == Role.UTILISATEUR


def test_string_admin_converti_en_enum():
    """Un string 'admin' est converti en Role.ADMIN."""
    user = Utilisateur(role="admin")

    assert user.role == Role.ADMIN
    assert isinstance(user.role, Role)


def test_string_utilisateur_converti_en_enum():
    """Un string 'utilisateur' est converti en Role.UTILISATEUR."""
    user = Utilisateur(role="utilisateur")

    assert user.role == Role.UTILISATEUR
    assert isinstance(user.role, Role)


def test_enum_pass_chez_lui():
    """Un Role déjà passé n'est pas reconverti."""
    user = Utilisateur(role=Role.ADMIN)

    assert user.role == Role.ADMIN
    assert type(user.role) is Role


def test_actif_par_defaut_vrai():
    """Un utilisateur est actif par défaut."""
    user = Utilisateur(nom_utilisateur="bob")

    assert user.actif is True


def test_actif_explicite_faux():
    """Un utilisateur peut être désactivé explicitement."""
    user = Utilisateur(nom_utilisateur="bob", actif=False)

    assert user.actif is False
