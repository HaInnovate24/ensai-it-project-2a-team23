"""Tests des schémas Pydantic des comptes utilisateurs."""

import pytest
from pydantic import ValidationError

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from model.utilisateur_model import (
    ChangementActivation,
    ChangementRole,
    UtilisateurCreation,
    UtilisateurSortie,
)


def test_sortie_ne_contient_jamais_l_empreinte_du_mot_de_passe():
    """Même si l'objet métier contient l'empreinte, la sortie ne la contient pas."""
    utilisateur = Utilisateur(
        id=1, nom_utilisateur="alice", mot_de_passe_hash="pbkdf2$secret", role=Role.ADMIN
    )

    sortie = UtilisateurSortie.model_validate(utilisateur)

    assert "mot_de_passe_hash" not in sortie.model_dump()
    assert "mot_de_passe" not in sortie.model_dump()
    assert "secret" not in sortie.model_dump_json()


def test_sortie_champs_renvoyes():
    """La sortie contient l'identifiant, le nom, le rôle et l'état du compte."""
    utilisateur = Utilisateur(id=3, nom_utilisateur="bob", role=Role.UTILISATEUR, actif=False)

    sortie = UtilisateurSortie.model_validate(utilisateur)

    assert sortie.id == 3
    assert sortie.nom_utilisateur == "bob"
    assert sortie.role is Role.UTILISATEUR
    assert sortie.actif is False
    assert sortie.date_creation is None
    assert sortie.derniere_connexion is None


def test_creation_champs_obligatoires():
    """Le nom et le mot de passe sont obligatoires à l'inscription."""
    with pytest.raises(ValidationError):
        UtilisateurCreation(nom_utilisateur="alice")


def test_creation_refuse_un_role():
    """On ne peut pas choisir son rôle à l'inscription : un champ en trop est refusé."""
    with pytest.raises(ValidationError):
        UtilisateurCreation(nom_utilisateur="alice", mot_de_passe="Motdepasse1", role="admin")


@pytest.mark.parametrize("role_valide", ["admin", "utilisateur"])
def test_changement_role_valide(role_valide):
    """Les deux rôles existants sont acceptés."""
    assert ChangementRole(role=role_valide).role == Role(role_valide)


@pytest.mark.parametrize("role_invalide", ["superadmin", "", None, 1])
def test_changement_role_invalide(role_invalide):
    """Un rôle inconnu est refusé."""
    with pytest.raises(ValidationError):
        ChangementRole(role=role_invalide)


@pytest.mark.parametrize("etat_valide", [True, False])
def test_changement_activation_valide(etat_valide):
    """Un vrai booléen est accepté."""
    assert ChangementActivation(actif=etat_valide).actif is etat_valide


@pytest.mark.parametrize("etat_invalide", ["false", "true", 0, 1, None, "oui"])
def test_changement_activation_invalide(etat_invalide):
    """Une valeur ambiguë (texte, 0, 1, None) est refusée."""
    with pytest.raises(ValidationError):
        ChangementActivation(actif=etat_invalide)
