"""Tests de l'UtilisateurDao avec une connexion mockée (aucune base réelle)."""

from datetime import datetime

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDao


def _ligne(id=1, nom="alice", role="utilisateur", actif=True):
    return {
        "id": id,
        "nom_utilisateur": nom,
        "mot_de_passe_hash": "hash_secret_123",
        "role": role,
        "actif": actif,
        "date_creation": datetime(2026, 11, 4, 10, 0),
        "derniere_connexion": None,
    }


def test_creer_renvoie_utilisateur_avec_id(curseur, connexion):
    """creer() renvoie l'objet inséré (avec id et date_creation) et commit."""
    curseur.fetchone.return_value = _ligne(id=42, nom="bob", role="admin")

    cree = UtilisateurDao().creer(
        Utilisateur(nom_utilisateur="bob", mot_de_passe_hash="h", role=Role.ADMIN, actif=True)
    )

    assert cree.id == 42
    assert cree.nom_utilisateur == "bob"
    assert cree.role == Role.ADMIN
    assert cree.date_creation is not None
    connexion.commit.assert_called()


def test_trouver_par_id_existant(curseur):
    """trouver_par_id() renvoie l'utilisateur correspondant."""
    curseur.fetchone.return_value = _ligne(id=7, nom="alice")

    trouve = UtilisateurDao().trouver_par_id(7)

    assert trouve is not None
    assert trouve.id == 7
    assert trouve.nom_utilisateur == "alice"


def test_trouver_par_id_inexistant_renvoie_none(curseur):
    """trouver_par_id() renvoie None si aucune ligne."""
    curseur.fetchone.return_value = None
    assert UtilisateurDao().trouver_par_id(-1) is None


def test_trouver_par_nom_existant(curseur):
    """trouver_par_nom() renvoie l'utilisateur et passe le nom en paramètre."""
    curseur.fetchone.return_value = _ligne(id=5, nom="alice")

    trouve = UtilisateurDao().trouver_par_nom("alice")

    assert trouve is not None
    assert trouve.id == 5
    _, parametres = curseur.execute.call_args[0]
    assert parametres == ("alice",)


def test_trouver_par_nom_inexistant_renvoie_none(curseur):
    """trouver_par_nom() renvoie None si aucune ligne."""
    curseur.fetchone.return_value = None
    assert UtilisateurDao().trouver_par_nom("inconnu") is None


def test_lister_renvoie_des_utilisateurs(curseur):
    """lister() mappe les lignes en objets Utilisateur."""
    curseur.fetchall.return_value = [_ligne(id=1, nom="alice"), _ligne(id=2, nom="bob")]

    liste = UtilisateurDao().lister()

    assert len(liste) == 2
    assert all(isinstance(u, Utilisateur) for u in liste)


def test_modifier_renvoie_true_si_ligne_affectee(curseur, connexion):
    """modifier() renvoie True quand une ligne est modifiée et commit."""
    curseur.rowcount = 1

    utilisateur = Utilisateur(id=7, nom_utilisateur="alice", role=Role.UTILISATEUR, actif=False)
    utilisateur.derniere_connexion = datetime.now()

    assert UtilisateurDao().modifier(utilisateur) is True
    connexion.commit.assert_called()


def test_modifier_renvoie_false_si_aucune_ligne(curseur):
    """modifier() renvoie False quand l'id n'existe pas (rowcount = 0)."""
    curseur.rowcount = 0
    assert UtilisateurDao().modifier(Utilisateur(id=404, nom_utilisateur="x")) is False
