"""Tests du calcul des taux d'emploi, sans base de données.

Le taux d'emploi = Emploi (OCU_ISCO08_TOTAL) / Population (AGE_AGGREGATE_TOTAL) * 100.
Les indicateurs utilisés sont EMP_TEMP_SEX_OCU_NB et POP_XWAP_SEX_AGE_NB.
"""

from decimal import Decimal

import pytest

from business_object.classification import Classification
from business_object.enums import Sexe
from business_object.indicateur import Indicateur
from business_object.observation import Observation
from business_object.pays import Pays
from service.analyse_service import AnalyseService
from utils.exceptions import DonneesInvalides, RessourceIntrouvable

# ----------------------------------------------------------------------
# Faux DAO et outils de test
# ----------------------------------------------------------------------


class FauxObservationDao:
    """Faux DAO d'observations : il cherche dans une liste en mémoire."""

    def __init__(self, observations):
        self.observations = observations

    def lire_serie(self, code_indicateur, code_pays, sexe=None, code_classification=None):
        resultat = [
            obs
            for obs in self.observations
            if obs.code_indicateur == code_indicateur and obs.code_pays == code_pays
        ]
        if sexe is not None:
            resultat = [obs for obs in resultat if obs.sexe == sexe]
        if code_classification:
            resultat = [obs for obs in resultat if obs.code_classification == code_classification]
        return sorted(resultat, key=lambda obs: obs.periode)

    def lire_par_periode(self, code_indicateur, periode, codes_pays=None):
        resultat = [
            obs
            for obs in self.observations
            if obs.code_indicateur == code_indicateur and obs.periode == periode
        ]
        if codes_pays:
            resultat = [obs for obs in resultat if obs.code_pays in codes_pays]
        return resultat


class FauxIndicateurDao:
    """Faux DAO d'indicateurs."""

    def __init__(self, indicateurs):
        self.indicateurs = {ind.code_indicateur: ind for ind in indicateurs}

    def trouver_par_code(self, code_indicateur):
        return self.indicateurs.get(code_indicateur)


class FauxPaysDao:
    """Faux DAO de pays."""

    def __init__(self, pays):
        self.pays = {p.code_pays: p for p in pays}

    def lister(self):
        return list(self.pays.values())

    def trouver_par_code(self, code_pays):
        return self.pays.get(code_pays)


class FauxClassificationDao:
    """Faux DAO de classifications."""

    def __init__(self, classifications):
        self.classifications = {c.code: c for c in classifications}

    def trouver_par_code(self, code):
        return self.classifications.get(code)


# ----------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------

CODE_EMPLOI = "EMP_TEMP_SEX_OCU_NB"
CODE_POPULATION = "POP_XWAP_SEX_AGE_NB"
CLASSIF_EMPLOI = "OCU_ISCO08_TOTAL"
CLASSIF_POPULATION = "AGE_AGGREGATE_TOTAL"


def creer_observation(
    pays, periode, valeur, sexe="total", classification=None, indicateur=CODE_EMPLOI
):
    """Fabrique une observation de test."""
    return Observation(
        code_indicateur=indicateur,
        code_pays=pays,
        periode=periode,
        valeur=valeur,
        sexe=sexe,
        code_classification=classification,
    )


def creer_service(observations):
    """Fabrique un service branché sur des faux DAO."""
    return AnalyseService(
        observation_dao=FauxObservationDao(observations),
        indicateur_dao=FauxIndicateurDao(
            [
                Indicateur(
                    code_indicateur=CODE_EMPLOI,
                    description="Emploi temporaire par sexe et occupation",
                    unite="milliers",
                ),
                Indicateur(
                    code_indicateur=CODE_POPULATION,
                    description="Population en âge de travailler par sexe et âge",
                    unite="milliers",
                ),
            ]
        ),
        pays_dao=FauxPaysDao(
            [
                Pays(code_pays="FRA", nom_pays="France"),
                Pays(code_pays="DEU", nom_pays="Allemagne"),
            ]
        ),
        classification_dao=FauxClassificationDao(
            [
                Classification(code=CLASSIF_EMPLOI, libelle="Total ISCO 08", type="occupation"),
                Classification(code=CLASSIF_POPULATION, libelle="Total âge", type="age"),
            ]
        ),
    )


def obs_emploi(pays, periode, valeur, sexe="total"):
    """Alias pour créer une observation d'emploi."""
    return creer_observation(
        pays, periode, valeur, sexe=sexe, classification=CLASSIF_EMPLOI, indicateur=CODE_EMPLOI
    )


def obs_population(pays, periode, valeur, sexe="total"):
    """Alias pour créer une observation de population."""
    return creer_observation(
        pays, periode, valeur, sexe=sexe, classification=CLASSIF_POPULATION, indicateur=CODE_POPULATION
    )


# ----------------------------------------------------------------------
# Tests : calcul du taux d'emploi
# ----------------------------------------------------------------------


def test_taux_emploi_calcul_simple():
    """Taux = emploi / population * 100, pour le total."""
    service = creer_service(
        [
            obs_emploi("FRA", "2022", 28_000.0),
            obs_emploi("FRA", "2023", 29_000.0),
            obs_population("FRA", "2022", 32_000.0),
            obs_population("FRA", "2023", 32_500.0),
        ]
    )

    resultat = service.calculer_taux_emploi("FRA")

    taux_2022 = 28_000.0 / 32_000.0 * 100.0  # = 87.5
    taux_2023 = 29_000.0 / 32_500.0 * 100.0  # ≈ 89.23

    assert len(resultat.taux_total) == 2
    assert resultat.taux_total[0].periode == "2022"
    assert resultat.taux_total[0].taux == pytest.approx(taux_2022, rel=1e-6)
    assert resultat.taux_total[1].periode == "2023"
    assert resultat.taux_total[1].taux == pytest.approx(taux_2023, rel=1e-6)


def test_taux_emploi_par_sexe():
    """Les taux sont calculés séparément pour homme et femme."""
    service = creer_service(
        [
            obs_emploi("FRA", "2023", 15_000.0, sexe="homme"),
            obs_emploi("FRA", "2023", 14_000.0, sexe="femme"),
            obs_population("FRA", "2023", 16_000.0, sexe="homme"),
            obs_population("FRA", "2023", 16_500.0, sexe="femme"),
        ]
    )

    resultat = service.calculer_taux_emploi("FRA")

    assert len(resultat.taux_homme) == 1
    assert len(resultat.taux_femme) == 1
    assert resultat.taux_homme[0].taux == pytest.approx(15_000.0 / 16_000.0 * 100.0, rel=1e-6)
    assert resultat.taux_femme[0].taux == pytest.approx(14_000.0 / 16_500.0 * 100.0, rel=1e-6)


def test_taux_emploi_variation():
    """La variation est la différence entre le taux courant et le précédent (en points)."""
    service = creer_service(
        [
            obs_emploi("FRA", "2022", 25_000.0),
            obs_emploi("FRA", "2023", 26_000.0),
            obs_population("FRA", "2022", 30_000.0),
            obs_population("FRA", "2023", 30_000.0),
        ]
    )

    resultat = service.calculer_taux_emploi("FRA")

    # Taux 2022 = 25000/30000*100 = 83.33...
    # Taux 2023 = 26000/30000*100 = 86.67...
    # Variation 2023 = 86.67 - 83.33 = +3.33 points
    assert len(resultat.variation_taux_total) == 1
    assert resultat.variation_taux_total[0].periode == "2023"
    attendu = (26_000.0 / 30_000.0 - 25_000.0 / 30_000.0) * 100.0
    assert resultat.variation_taux_total[0].taux == pytest.approx(attendu, rel=1e-6)


def test_taux_emploi_nb_periodes():
    """Avec nb_periodes=2, on ne garde que les 2 dernières périodes."""
    service = creer_service(
        [
            obs_emploi("FRA", "2021", 24_000.0),
            obs_emploi("FRA", "2022", 25_000.0),
            obs_emploi("FRA", "2023", 26_000.0),
            obs_population("FRA", "2021", 30_000.0),
            obs_population("FRA", "2022", 30_000.0),
            obs_population("FRA", "2023", 30_000.0),
        ]
    )

    resultat = service.calculer_taux_emploi("FRA", nb_periodes=2)

    assert len(resultat.taux_total) == 2
    assert resultat.taux_total[0].periode == "2022"
    assert resultat.taux_total[1].periode == "2023"


def test_taux_emploi_population_zero():
    """Si la population est 0, le taux n'est pas calculé pour cette période."""
    service = creer_service(
        [
            obs_emploi("FRA", "2023", 25_000.0),
            obs_population("FRA", "2023", 0.0),
        ]
    )

    # Le total est vide -> RessourceIntrouvable
    with pytest.raises(RessourceIntrouvable):
        service.calculer_taux_emploi("FRA")


def test_taux_emploi_aucune_donnee():
    """Aucune donnée d'emploi ni de population : RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.calculer_taux_emploi("FRA")


def test_taux_emploi_pays_inconnu():
    """Un pays inexistant lève RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.calculer_taux_emploi("XXX")


def test_taux_emploi_code_pays_vide():
    """Un code pays vide lève DonneesInvalides."""
    service = creer_service([])

    with pytest.raises(DonneesInvalides):
        service.calculer_taux_emploi("")


def test_taux_emploi_nb_periodes_invalide():
    """Un nombre de périodes inférieur à 1 lève DonneesInvalides."""
    service = creer_service([])

    with pytest.raises(DonneesInvalides):
        service.calculer_taux_emploi("FRA", nb_periodes=0)


def test_taux_emploi_seule_emploi_sans_population():
    """De l'emploi mais pas de population : RessourceIntrouvable (pas de taux calculable)."""
    service = creer_service(
        [
            obs_emploi("FRA", "2023", 25_000.0),
        ]
    )

    with pytest.raises(RessourceIntrouvable):
        service.calculer_taux_emploi("FRA")


def test_taux_emploi_decimal_values():
    """PostgreSQL renvoie des Decimal : le service les convertit en float."""
    service = creer_service(
        [
            obs_emploi("FRA", "2023", Decimal("25000.5000")),
            obs_population("FRA", "2023", Decimal("30000.2500")),
        ]
    )

    resultat = service.calculer_taux_emploi("FRA")

    assert len(resultat.taux_total) == 1
    attendu = float(Decimal("25000.5000")) / float(Decimal("30000.2500")) * 100.0
    assert resultat.taux_total[0].taux == pytest.approx(attendu, rel=1e-6)
    assert isinstance(resultat.taux_total[0].taux, float)


def test_taux_emploi_variation_homme_femme():
    """Les variations par sexe sont calculées indépendamment."""
    service = creer_service(
        [
            obs_emploi("FRA", "2022", 12_000.0, sexe="homme"),
            obs_emploi("FRA", "2023", 13_000.0, sexe="homme"),
            obs_emploi("FRA", "2022", 10_000.0, sexe="femme"),
            obs_emploi("FRA", "2023", 11_000.0, sexe="femme"),
            obs_population("FRA", "2022", 15_000.0, sexe="homme"),
            obs_population("FRA", "2023", 15_000.0, sexe="homme"),
            obs_population("FRA", "2022", 15_000.0, sexe="femme"),
            obs_population("FRA", "2023", 15_000.0, sexe="femme"),
        ]
    )

    resultat = service.calculer_taux_emploi("FRA")

    var_homme_attendue = (13_000.0 / 15_000.0 - 12_000.0 / 15_000.0) * 100.0
    var_femme_attendue = (11_000.0 / 15_000.0 - 10_000.0 / 15_000.0) * 100.0

    assert len(resultat.variation_taux_homme) == 1
    assert resultat.variation_taux_homme[0].taux == pytest.approx(var_homme_attendue, rel=1e-6)
    assert len(resultat.variation_taux_femme) == 1
    assert resultat.variation_taux_femme[0].taux == pytest.approx(var_femme_attendue, rel=1e-6)


def test_taux_emploi_seule_population_sans_emploi():
    """De la population mais pas d'emploi : RessourceIntrouvable."""
    service = creer_service(
        [
            obs_population("FRA", "2023", 30_000.0),
        ]
    )

    with pytest.raises(RessourceIntrouvable):
        service.calculer_taux_emploi("FRA")


def test_taux_emploi_une_periode_seule():
    """Avec une seule période, il n'y a pas de variation (liste vide)."""
    service = creer_service(
        [
            obs_emploi("FRA", "2023", 25_000.0),
            obs_population("FRA", "2023", 30_000.0),
        ]
    )

    resultat = service.calculer_taux_emploi("FRA")

    assert len(resultat.taux_total) == 1
    assert len(resultat.variation_taux_total) == 0
    assert len(resultat.variation_taux_homme) == 0
    assert len(resultat.variation_taux_femme) == 0
