"""Outils pour travailler avec les périodes : années, trimestres et mois.

Formats reconnus : "2014" (année), "2014Q3" (trimestre), "2014M07" (mois).
Les périodes sont comparées par leur position dans le calendrier (et non par ordre
alphabétique), ce qui permet de détecter les périodes manquantes.
"""

import re

MOTIF_PERIODE = re.compile(r"(\d{4})(?:Q([1-4])|M(\d{1,2}))?")


def convertir_periode(periode: str) -> tuple[str, int] | None:
    """Convertit une période en (fréquence, numéro dans le calendrier).

    La fréquence vaut "annee", "trimestre" ou "mois". Le numéro permet de savoir
    combien de périodes séparent deux dates (ex. 2014Q4 -> 8059, 2015Q1 -> 8060).
    Renvoie None si le format n'est pas reconnu.
    """
    if not isinstance(periode, str):
        return None
    correspondance = MOTIF_PERIODE.fullmatch(periode.strip())
    if correspondance is None:
        return None

    annee = int(correspondance.group(1))
    trimestre, mois = correspondance.group(2), correspondance.group(3)
    if trimestre is not None:
        return ("trimestre", annee * 4 + int(trimestre) - 1)
    if mois is not None:
        if not 1 <= int(mois) <= 12:
            return None
        return ("mois", annee * 12 + int(mois) - 1)
    return ("annee", annee)


def formater_periode(frequence: str, numero: int) -> str:
    """Opération inverse de convertir_periode. reconstruit le texte de la période."""
    if frequence == "trimestre":
        return f"{numero // 4}Q{numero % 4 + 1}"
    if frequence == "mois":
        return f"{numero // 12}M{numero % 12 + 1:02d}"
    return str(numero)


def fenetre_de_periodes(
    periodes: list[str], nb_periodes: int | None = None
) -> tuple[list[str], list[str]]:
    """Choisit les périodes à garder et repère celles qui manquent.

    Avec nb_periodes, la fenêtre est formée des N périodes consécutives du calendrier
    qui finissent à la dernière période disponible. Les périodes de la fenêtre qui n'ont
    pas de donnée sont renvoyées comme manquantes. Sans nb_periodes, on garde tout et on
    signale les trous entre la première et la dernière période.

    Si les périodes ont un format inconnu ou mélangent plusieurs fréquences, on ne peut
    pas raisonner sur le calendrier, on garde les N dernières périodes (ordre
    alphabétique) et on ne signale aucune période manquante.

    Renvoie (périodes gardées dans l'ordre chronologique, périodes manquantes).
    """
    if not periodes:
        return [], []

    convertis = [convertir_periode(periode) for periode in periodes]
    frequences = {conversion[0] for conversion in convertis if conversion is not None}
    if None in convertis or len(frequences) != 1:
        triees = sorted(periodes)
        return (triees if nb_periodes is None else triees[-nb_periodes:]), []

    frequence = frequences.pop()
    texte_par_numero = {
        conversion[1]: periode for conversion, periode in zip(convertis, periodes, strict=True)
    }
    dernier = max(texte_par_numero)
    premier = min(texte_par_numero) if nb_periodes is None else dernier - nb_periodes + 1

    gardees = [texte_par_numero[numero] for numero in sorted(texte_par_numero) if numero >= premier]
    manquantes = [
        formater_periode(frequence, numero)
        for numero in range(premier, dernier + 1)
        if numero not in texte_par_numero
    ]
    return gardees, manquantes
