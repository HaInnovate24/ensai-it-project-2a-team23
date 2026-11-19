"""Tests du schéma Pydantic du journal d'activité."""

from datetime import datetime

from business_object.journal_activite import JournalActivite
from model.journal_model import JournalSortie


def test_journal_sortie_depuis_un_objet_metier():
    """Une entrée de journal est convertie avec tous ses champs."""
    date = datetime(2026, 11, 3, 10, 0)
    entree = JournalActivite(
        id=5,
        utilisateur_id=1,
        action="PROMOTION_ADMIN",
        cible="utilisateur:2",
        details="alice : utilisateur -> admin",
        date_heure=date,
    )

    sortie = JournalSortie.model_validate(entree)

    assert sortie.id == 5
    assert sortie.utilisateur_id == 1
    assert sortie.action == "PROMOTION_ADMIN"
    assert sortie.cible == "utilisateur:2"
    assert sortie.details == "alice : utilisateur -> admin"
    assert sortie.date_heure == date


def test_journal_sortie_action_automatique():
    """Une action sans utilisateur (None) est acceptée."""
    entree = JournalActivite(id=1, utilisateur_id=None, action="COLLECTE")

    assert JournalSortie.model_validate(entree).utilisateur_id is None
