"""Tests unitaires de l'objet métier Rapport."""

from datetime import datetime

from business_object.enums import StatutRapport
from business_object.rapport import Rapport


def test_initialisation_par_defaut():
    """Un Rapport sans argument a ses attributs à None, sauf statut (EN_ATTENTE)."""
    rapport = Rapport()

    assert rapport.id is None
    assert rapport.utilisateur_id is None
    assert rapport.titre is None
    assert rapport.description is None
    assert rapport.date_creation is None
    assert rapport.fichier_path is None
    assert rapport.statut == StatutRapport.EN_ATTENTE


def test_initialisation_complete():
    """Un Rapport construit avec tous les attributs les conserve tels quels."""
    date_creation = datetime(2024, 7, 20, 11, 0, 0)
    rapport = Rapport(
        id=3,
        utilisateur_id=1,
        titre="Synthèse EMP 2024",
        description="Taux d'emploi par pays",
        date_creation=date_creation,
        fichier_path="/rapports/synthese_emp.pdf",
        statut=StatutRapport.PRET,
    )

    assert rapport.id == 3
    assert rapport.utilisateur_id == 1
    assert rapport.titre == "Synthèse EMP 2024"
    assert rapport.description == "Taux d'emploi par pays"
    assert rapport.date_creation == date_creation
    assert rapport.fichier_path == "/rapports/synthese_emp.pdf"
    assert rapport.statut == StatutRapport.PRET


def test_statut_par_defaut_en_attente():
    """Le statut par défaut est EN_ATTENTE."""
    rapport = Rapport()

    assert rapport.statut == StatutRapport.EN_ATTENTE


def test_string_pret_converti_en_enum():
    """Un string 'pret' est converti en StatutRapport.PRET."""
    rapport = Rapport(statut="pret")

    assert rapport.statut == StatutRapport.PRET
    assert isinstance(rapport.statut, StatutRapport)


def test_string_echec_converti_en_enum():
    """Un string 'echec' est converti en StatutRapport.ECHEC."""
    rapport = Rapport(statut="echec")

    assert rapport.statut == StatutRapport.ECHEC
    assert isinstance(rapport.statut, StatutRapport)


def test_enum_pass_chez_lui():
    """Un StatutRapport déjà passé n'est pas reconverti."""
    rapport = Rapport(statut=StatutRapport.PRET)

    assert rapport.statut == StatutRapport.PRET
    assert type(rapport.statut) is StatutRapport
