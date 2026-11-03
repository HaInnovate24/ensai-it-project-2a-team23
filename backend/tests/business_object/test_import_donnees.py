"""Tests unitaires de l'objet métier ImportDonnees."""

from datetime import datetime

from business_object.enums import StatutImport
from business_object.import_donnees import ImportDonnees


def test_initialisation_par_defaut():
    """Un ImportDonnees sans argument a ses attributs à None, sauf statut (EN_COURS) et nombre_lignes (0)."""
    imp = ImportDonnees()

    assert imp.id is None
    assert imp.indicateur_code is None
    assert imp.utilisateur_id is None
    assert imp.date_debut is None
    assert imp.date_fin is None
    assert imp.statut == StatutImport.EN_COURS
    assert imp.nombre_lignes == 0
    assert imp.fichier_source is None
    assert imp.message_erreur is None


def test_initialisation_complete():
    """Un ImportDonnees construit avec tous les attributs les conserve tels quels."""
    date_debut = datetime(2024, 6, 1, 9, 0, 0)
    date_fin = datetime(2024, 6, 1, 9, 5, 30)
    imp = ImportDonnees(
        id=1,
        indicateur_code="EMP",
        utilisateur_id=5,
        date_debut=date_debut,
        date_fin=date_fin,
        statut=StatutImport.SUCCES,
        nombre_lignes=150,
        fichier_source="export_emp.csv",
        message_erreur=None,
    )

    assert imp.id == 1
    assert imp.indicateur_code == "EMP"
    assert imp.utilisateur_id == 5
    assert imp.date_debut == date_debut
    assert imp.date_fin == date_fin
    assert imp.statut == StatutImport.SUCCES
    assert imp.nombre_lignes == 150
    assert imp.fichier_source == "export_emp.csv"
    assert imp.message_erreur is None


def test_statut_par_defaut_en_cours():
    """Le statut par défaut est EN_COURS."""
    imp = ImportDonnees()

    assert imp.statut == StatutImport.EN_COURS


def test_string_succes_converti_en_enum():
    """Un string 'succes' est converti en StatutImport.SUCCES."""
    imp = ImportDonnees(statut="succes")

    assert imp.statut == StatutImport.SUCCES
    assert isinstance(imp.statut, StatutImport)


def test_string_echec_converti_en_enum():
    """Un string 'echec' est converti en StatutImport.ECHEC."""
    imp = ImportDonnees(statut="echec")

    assert imp.statut == StatutImport.ECHEC
    assert isinstance(imp.statut, StatutImport)


def test_enum_pass_chez_lui():
    """Un StatutImport déjà passé n'est pas reconverti."""
    imp = ImportDonnees(statut=StatutImport.EN_COURS)

    assert imp.statut == StatutImport.EN_COURS
    assert type(imp.statut) is StatutImport


def test_statut_echec_avec_message_erreur():
    """Un import en échec peut avoir un message d'erreur."""
    imp = ImportDonnees(statut=StatutImport.ECHEC, message_erreur="Connexion refusée")

    assert imp.statut == StatutImport.ECHEC
    assert imp.message_erreur == "Connexion refusée"
