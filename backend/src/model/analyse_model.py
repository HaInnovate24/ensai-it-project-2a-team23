"""Schémas Pydantic des analyses (filtres en entrée, résultats en sortie)."""

from pydantic import BaseModel

from business_object.enums import Sexe


class FiltreAnalyse(BaseModel):
    """Filtres d'une analyse en entrée."""

    code_indicateur: str
    code_pays: str | None = None
    codes_pays: list[str] | None = None
    codes_indicateur: list[str] | None = None
    sexe: Sexe | None = None
    code_classification: str | None = None
    periode: str | None = None


class PointSerie(BaseModel):
    """Point d'une série (période, valeur)."""

    periode: str
    valeur: float


class Serie(BaseModel):
    """Série temporelle en sortie."""

    libelle: str
    points: list[PointSerie]


class Comparaison(BaseModel):
    """Comparaison de plusieurs séries en sortie."""

    series: list[Serie]


class PointTauxEmploi(BaseModel):
    """Point d'une série de taux d'emploi (période + taux calculé)."""

    periode: str
    taux: float


class ResultatTauxEmploi(BaseModel):
    """Résultat complet du calcul des taux d'emploi et des variations.

    Chaque série est une liste de points ordonnés par période.
    Les taux sont en pourcentage (%). Les variations sont en points.
    """

    taux_total: list[PointTauxEmploi]
    taux_homme: list[PointTauxEmploi]
    taux_femme: list[PointTauxEmploi]
    variation_annuelle_emploi: list[PointTauxEmploi]
    variation_taux_total: list[PointTauxEmploi]
    variation_taux_homme: list[PointTauxEmploi]
    variation_taux_femme: list[PointTauxEmploi]
