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
    """Série temporelle en sortie.

    periodes_manquantes liste les périodes sans donnée dans la fenêtre analysée
    (vide quand il n'y en a pas, ou quand le format des périodes est inconnu).
    """

    libelle: str
    points: list[PointSerie]
    periodes_manquantes: list[str] = []


class Comparaison(BaseModel):
    """Comparaison de plusieurs séries en sortie.

    sans_donnees liste les pays ou indicateurs demandés pour lesquels aucune
    donnée n'a été trouvée (ils n'apparaissent donc pas dans series).
    """

    series: list[Serie]
    sans_donnees: list[str] = []


class ResumeSerie(BaseModel):
    """Résumé statistique d'une série (F3) : bornes, moyenne et variation.

    Les variations valent None quand elles ne sont pas calculables.
    série d'un seul point (absolue et relative) ou valeur de départ égale
    à zéro (relative seulement). La variation relative est en pourcentage.
    Les statistiques portent sur les points disponibles. periodes_manquantes
    indique les périodes de la fenêtre sans donnée.
    """

    libelle: str
    nb_points: int
    periode_debut: str
    periode_fin: str
    valeur_debut: float
    valeur_fin: float
    minimum: float
    maximum: float
    moyenne: float
    variation_absolue: float | None
    variation_relative: float | None
    periodes_manquantes: list[str] = []
