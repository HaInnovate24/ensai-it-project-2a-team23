"""Tests de la génération de graphiques pour les rapports PDF."""

import pytest

from model.analyse_model import PointSerie, Serie
from utils.graphiques import Graphiques

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def graphiques() -> Graphiques:
    """Retourne une instance de Graphiques."""
    return Graphiques()


@pytest.fixture
def serie_simple() -> Serie:
    """Une série avec 3 points."""
    return Serie(
        libelle="Taux de chômage - France",
        points=[
            PointSerie(periode="2022", valeur=7.4),
            PointSerie(periode="2023", valeur=7.1),
            PointSerie(periode="2024", valeur=6.8),
        ],
    )


@pytest.fixture
def series_comparaison() -> list[Serie]:
    """Deux séries de même longueur pour un comparatif."""
    return [
        Serie(
            libelle="France",
            points=[PointSerie(periode="2024", valeur=6.8)],
        ),
        Serie(
            libelle="Allemagne",
            points=[PointSerie(periode="2024", valeur=4.2)],
        ),
    ]


# courbe()


def test_courbe_renvoie_des_bytes(graphiques, serie_simple):
    """La méthode courbe renvoie un objet bytes."""
    resultat = graphiques.courbe(serie_simple)
    assert isinstance(resultat, bytes)


def test_courbe_renvoie_un_png_valide(graphiques, serie_simple):
    """Les bytes renvoyés commencent par la signature PNG."""
    resultat = graphiques.courbe(serie_simple)
    assert resultat.startswith(PNG_SIGNATURE)


def test_courbe_png_non_vide(graphiques, serie_simple):
    """L'image générée a une taille raisonnable (> 1 Ko)."""
    resultat = graphiques.courbe(serie_simple)
    assert len(resultat) > 1024


def test_courbe_point_seul(graphiques):
    """Une série avec un seul point produit quand même une image."""
    serie = Serie(
        libelle="Valeur unique",
        points=[PointSerie(periode="2024", valeur=5.0)],
    )
    resultat = graphiques.courbe(serie)
    assert isinstance(resultat, bytes)
    assert resultat.startswith(PNG_SIGNATURE)


# barres()


def test_barres_renvoie_des_bytes(graphiques, series_comparaison):
    """La méthode barres renvoie un objet bytes."""
    resultat = graphiques.barres(series_comparaison)
    assert isinstance(resultat, bytes)


def test_barres_renvoie_un_png_valide(graphiques, series_comparaison):
    """Les bytes renvoyés commencent par la signature PNG."""
    resultat = graphiques.barres(series_comparaison)
    assert resultat.startswith(PNG_SIGNATURE)


def test_barres_png_non_vide(graphiques, series_comparaison):
    """L'image générée a une taille raisonnable (> 1 Ko)."""
    resultat = graphiques.barres(series_comparaison)
    assert len(resultat) > 1024


def test_barres_liste_vide(graphiques):
    """Une liste vide de séries lève une ValueError."""
    with pytest.raises(ValueError, match="Aucune série"):
        graphiques.barres([])


def test_barres_serie_unique(graphiques):
    """Une seule série fonctionne (pas de division par zéro)."""
    serie = Serie(
        libelle="France",
        points=[PointSerie(periode="2024", valeur=6.8)],
    )
    resultat = graphiques.barres([serie])
    assert isinstance(resultat, bytes)
    assert resultat.startswith(PNG_SIGNATURE)


def test_barres_deux_periodes(graphiques):
    """Des séries avec plusieurs périodes produisent des barres groupées."""
    series = [
        Serie(
            libelle="France",
            points=[
                PointSerie(periode="2023", valeur=7.1),
                PointSerie(periode="2024", valeur=6.8),
            ],
        ),
        Serie(
            libelle="Belgique",
            points=[
                PointSerie(periode="2023", valeur=8.0),
                PointSerie(periode="2024", valeur=7.5),
            ],
        ),
    ]
    resultat = graphiques.barres(series)
    assert isinstance(resultat, bytes)
    assert resultat.startswith(PNG_SIGNATURE)