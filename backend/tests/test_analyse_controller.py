"""Tests du controller d'analyse, sans base de données ni vrai service.

On appelle directement les fonctions des routes en leur donnant un faux service.
On vérifie deux choses : les paramètres sont bien transmis au service, et les
erreurs métier sont bien transformées en erreurs HTTP.
"""

import pytest
from fastapi import HTTPException

from business_object.enums import Sexe
from controller.analyse_controller import (
    carte,
    comparaison_indicateurs,
    comparaison_pays,
    erreur_http,
    evolution,
)
from model.analyse_model import Comparaison, PointSerie, Serie
from utils.exceptions import AccesRefuse, DonneesInvalides, RessourceIntrouvable


class FauxService:
    """Faux service : il note les appels reçus et renvoie un résultat fixe (ou une erreur)."""

    def __init__(self, erreur=None):
        """Si une erreur est fournie, chaque méthode la lève au lieu de répondre."""
        self.erreur = erreur
        self.appel = None

    def _repondre(self, nom, arguments, resultat):
        """Note l'appel reçu, lève l'erreur prévue ou renvoie le résultat."""
        self.appel = (nom, arguments)
        if self.erreur is not None:
            raise self.erreur
        return resultat

    def evolution(self, **arguments):
        """Imite AnalyseService.evolution."""
        serie = Serie(libelle="Emploi - France", points=[PointSerie(periode="2024Q1", valeur=1.0)])
        return self._repondre("evolution", arguments, serie)

    def comparer_pays(self, **arguments):
        """Imite AnalyseService.comparer_pays."""
        return self._repondre("comparer_pays", arguments, Comparaison(series=[]))

    def comparer_indicateurs(self, **arguments):
        """Imite AnalyseService.comparer_indicateurs."""
        return self._repondre("comparer_indicateurs", arguments, Comparaison(series=[]))

    def carte(self, **arguments):
        """Imite AnalyseService.carte."""
        return self._repondre("carte", arguments, Comparaison(series=[]))


# ----------------------------------------------------------------------
# Traduction des erreurs
# ----------------------------------------------------------------------


def test_erreur_http_ressource_introuvable():
    """RessourceIntrouvable devient une erreur 404 avec le message d'origine."""
    resultat = erreur_http(RessourceIntrouvable("Pays inconnu : XXX."))

    assert resultat.status_code == 404
    assert resultat.detail == "Pays inconnu : XXX."


def test_erreur_http_donnees_invalides():
    """DonneesInvalides devient une erreur 422."""
    assert erreur_http(DonneesInvalides("Paramètre incorrect.")).status_code == 422


def test_erreur_http_autre_erreur_metier():
    """Toute autre erreur métier devient aussi une erreur 422."""
    assert erreur_http(AccesRefuse("Interdit.")).status_code == 422


# ----------------------------------------------------------------------
# Évolution
# ----------------------------------------------------------------------


def test_evolution_transmet_les_parametres_et_renvoie_la_serie():
    """La route appelle le service avec les bons paramètres et renvoie sa réponse."""
    service = FauxService()

    resultat = evolution(
        code_indicateur="EMP",
        code_pays="FRA",
        sexe=Sexe.FEMME,
        code_classification="AGE_15_24",
        nb_periodes=8,
        service=service,
    )

    assert resultat.libelle == "Emploi - France"
    assert service.appel == (
        "evolution",
        {
            "code_indicateur": "EMP",
            "code_pays": "FRA",
            "sexe": Sexe.FEMME,
            "code_classification": "AGE_15_24",
            "nb_periodes": 8,
        },
    )


def test_evolution_introuvable_renvoie_404():
    """Une ressource introuvable donne une erreur HTTP 404."""
    service = FauxService(erreur=RessourceIntrouvable("Indicateur inconnu : X."))

    with pytest.raises(HTTPException) as erreur:
        evolution(code_indicateur="X", code_pays="FRA", service=service)

    assert erreur.value.status_code == 404


def test_evolution_donnees_invalides_renvoie_422():
    """Des données invalides donnent une erreur HTTP 422."""
    service = FauxService(erreur=DonneesInvalides("Nombre de périodes invalide."))

    with pytest.raises(HTTPException) as erreur:
        evolution(code_indicateur="EMP", code_pays="FRA", nb_periodes=0, service=service)

    assert erreur.value.status_code == 422


# ----------------------------------------------------------------------
# Comparaison entre pays
# ----------------------------------------------------------------------


def test_comparaison_pays_transmet_les_parametres():
    """La route transmet la liste de pays et la période au service."""
    service = FauxService()

    resultat = comparaison_pays(
        code_indicateur="EMP",
        codes_pays=["FRA", "DEU"],
        periode="2024Q1",
        service=service,
    )

    assert isinstance(resultat, Comparaison)
    assert service.appel[0] == "comparer_pays"
    assert service.appel[1]["codes_pays"] == ["FRA", "DEU"]
    assert service.appel[1]["periode"] == "2024Q1"


def test_comparaison_pays_introuvable_renvoie_404():
    """Une ressource introuvable donne une erreur HTTP 404."""
    service = FauxService(erreur=RessourceIntrouvable("Pays inconnu : XXX."))

    with pytest.raises(HTTPException) as erreur:
        comparaison_pays(code_indicateur="EMP", codes_pays=["XXX"], service=service)

    assert erreur.value.status_code == 404


def test_comparaison_pays_donnees_invalides_renvoie_422():
    """Des données invalides donnent une erreur HTTP 422."""
    service = FauxService(erreur=DonneesInvalides("Indiquez au moins un pays."))

    with pytest.raises(HTTPException) as erreur:
        comparaison_pays(code_indicateur="EMP", codes_pays=[], service=service)

    assert erreur.value.status_code == 422


# ----------------------------------------------------------------------
# Comparaison entre indicateurs
# ----------------------------------------------------------------------


def test_comparaison_indicateurs_transmet_les_parametres():
    """La route transmet la liste d'indicateurs et le pays au service."""
    service = FauxService()

    resultat = comparaison_indicateurs(
        codes_indicateur=["EMP", "TAUX"], code_pays="FRA", service=service
    )

    assert isinstance(resultat, Comparaison)
    assert service.appel[0] == "comparer_indicateurs"
    assert service.appel[1]["codes_indicateur"] == ["EMP", "TAUX"]
    assert service.appel[1]["code_pays"] == "FRA"


def test_comparaison_indicateurs_introuvable_renvoie_404():
    """Une ressource introuvable donne une erreur HTTP 404."""
    service = FauxService(erreur=RessourceIntrouvable("Indicateur inconnu : X."))

    with pytest.raises(HTTPException) as erreur:
        comparaison_indicateurs(codes_indicateur=["X"], code_pays="FRA", service=service)

    assert erreur.value.status_code == 404


# ----------------------------------------------------------------------
# Carte
# ----------------------------------------------------------------------


def test_carte_transmet_les_parametres():
    """La route transmet l'indicateur et la période au service."""
    service = FauxService()

    resultat = carte(code_indicateur="EMP", periode="2024Q1", service=service)

    assert isinstance(resultat, Comparaison)
    assert service.appel[0] == "carte"
    assert service.appel[1]["code_indicateur"] == "EMP"
    assert service.appel[1]["periode"] == "2024Q1"


def test_carte_aucune_donnee_renvoie_404():
    """Aucune donnée pour la période donne une erreur HTTP 404."""
    service = FauxService(erreur=RessourceIntrouvable("Aucune donnée."))

    with pytest.raises(HTTPException) as erreur:
        carte(code_indicateur="EMP", periode="1900Q1", service=service)

    assert erreur.value.status_code == 404
