"""Tests unitaires de l'objet métier JournalActivite."""

from datetime import datetime

from business_object.journal_activite import JournalActivite


def test_initialisation_par_defaut_tout_none():
    """Un JournalActivite sans argument a tous ses attributs à None."""
    journal = JournalActivite()

    assert journal.id is None
    assert journal.utilisateur_id is None
    assert journal.action is None
    assert journal.cible is None
    assert journal.details is None
    assert journal.date_heure is None


def test_initialisation_complete():
    """Un JournalActivite construit avec tous les attributs les conserve tels quels."""
    date_heure = datetime(2024, 3, 10, 14, 22, 5)
    journal = JournalActivite(
        id=10,
        utilisateur_id=2,
        action="import",
        cible="EMP",
        details="Import manuel de 150 lignes",
        date_heure=date_heure,
    )

    assert journal.id == 10
    assert journal.utilisateur_id == 2
    assert journal.action == "import"
    assert journal.cible == "EMP"
    assert journal.details == "Import manuel de 150 lignes"
    assert journal.date_heure == date_heure
