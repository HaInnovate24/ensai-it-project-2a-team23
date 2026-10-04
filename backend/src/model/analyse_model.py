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
