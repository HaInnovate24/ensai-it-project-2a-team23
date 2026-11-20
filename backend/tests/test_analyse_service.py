"""Tests du service d'analyse (F3, F4, F5 et carte), sans base de données.

Le principe est tel qu'on donne au service de "faux DAO" qui travaillent sur des listes
en mémoire. On teste ainsi uniquement la logique du service.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from business_object.classification import Classification
from business_object.enums import Sexe
from business_object.indicateur import Indicateur
from business_object.observation import Observation
from business_object.pays import Pays
from service.analyse_service import AnalyseService
from utils.exceptions import DonneesInvalides, RessourceIntrouvable

# Faux DAO et outils de test


class FauxObservationDao:
    """Faux DAO d'observations : il cherche dans une liste en mémoire."""

    def __init__(self, observations):
        """Garde la liste d'observations fournie."""
        self.observations = observations

    def lire_serie(self, code_indicateur, code_pays, sexe=None, code_classification=None):
        """Imite ObservationDao.lire_serie : filtre puis trie par période."""
        resultat = [
            obs
            for obs in self.observations
            if obs.code_indicateur == code_indicateur and obs.code_pays == code_pays
        ]
        if sexe:
            resultat = [obs for obs in resultat if obs.sexe == sexe]
        if code_classification:
            resultat = [obs for obs in resultat if obs.code_classification == code_classification]
        return sorted(resultat, key=lambda obs: obs.periode)

    def lire_par_periode(self, code_indicateur, periode, codes_pays=None):
        """Imite ObservationDao.lire_par_periode : filtre par indicateur, période, pays."""
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
        """Range les indicateurs dans un dictionnaire (clé = code)."""
        self.indicateurs = {ind.code_indicateur: ind for ind in indicateurs}

    def trouver_par_code(self, code_indicateur):
        """Renvoie l'indicateur ou None."""
        return self.indicateurs.get(code_indicateur)


class FauxPaysDao:
    """Faux DAO de pays."""

    def __init__(self, pays):
        """Range les pays dans un dictionnaire (clé = code)."""
        self.pays = {p.code_pays: p for p in pays}

    def lister(self):
        """Renvoie tous les pays."""
        return list(self.pays.values())

    def trouver_par_code(self, code_pays):
        """Renvoie le pays ou None."""
        return self.pays.get(code_pays)


class FauxClassificationDao:
    """Faux DAO de classifications."""

    def __init__(self, classifications):
        """Range les classifications dans un dictionnaire (clé = code)."""
        self.classifications = {c.code: c for c in classifications}

    def trouver_par_code(self, code):
        """Renvoie la classification ou None."""
        return self.classifications.get(code)


def creer_observation(
    pays,
    periode,
    valeur,
    sexe="total",
    classification=None,
    indicateur="EMP",
    date_import=None,
):
    """Fabrique une observation de test (évite de répéter tous les arguments)."""
    return Observation(
        code_indicateur=indicateur,
        code_pays=pays,
        periode=periode,
        valeur=valeur,
        sexe=sexe,
        code_classification=classification,
        date_import=date_import,
    )


def creer_service(observations):
    """Fabrique un service branché sur de faux DAO contenant nos données de test."""
    return AnalyseService(
        observation_dao=FauxObservationDao(observations),
        indicateur_dao=FauxIndicateurDao(
            [
                Indicateur(code_indicateur="EMP", description="Emploi", unite="milliers"),
                Indicateur(code_indicateur="TAUX", description="Taux d'activité", unite="%"),
                Indicateur(code_indicateur="SANS_UNITE", description="Sans unité"),
            ]
        ),
        pays_dao=FauxPaysDao(
            [
                Pays(code_pays="FRA", nom_pays="France"),
                Pays(code_pays="DEU", nom_pays="Allemagne"),
                Pays(code_pays="ESP", nom_pays="Espagne"),
            ]
        ),
        classification_dao=FauxClassificationDao(
            [Classification(code="AGE_15_24", libelle="15-24 ans", type="age")]
        ),
    )


def periodes(serie):
    """Renvoie la liste des périodes d'une série."""
    return [point.periode for point in serie.points]


def valeurs(serie):
    """Renvoie la liste des valeurs d'une série."""
    return [point.valeur for point in serie.points]


def libelles(comparaison):
    """Renvoie la liste des libellés d'une comparaison."""
    return [serie.libelle for serie in comparaison.series]


# F3 : évolution


def test_evolution_trie_par_periode_et_construit_le_libelle():
    """Les points sont triés par période et le libellé contient indicateur, unité et pays."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q2", 11.0),
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("FRA", "2024Q3", 12.0),
        ]
    )

    serie = service.evolution("EMP", "FRA")

    assert serie.libelle == "Emploi (milliers) - France"
    assert periodes(serie) == ["2024Q1", "2024Q2", "2024Q3"]
    assert valeurs(serie) == [10.0, 11.0, 12.0]


def test_evolution_libelle_sans_unite():
    """Un indicateur sans unité n'affiche pas de parenthèses."""
    service = creer_service([creer_observation("FRA", "2024Q1", 1.0, indicateur="SANS_UNITE")])

    serie = service.evolution("SANS_UNITE", "FRA")

    assert serie.libelle == "Sans unité - France"


def test_evolution_garde_les_n_dernieres_periodes():
    """Avec nb_periodes=2, on garde les 2 périodes les plus récentes."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("FRA", "2024Q2", 11.0),
            creer_observation("FRA", "2024Q3", 12.0),
        ]
    )

    serie = service.evolution("EMP", "FRA", nb_periodes=2)

    assert periodes(serie) == ["2024Q2", "2024Q3"]


def test_evolution_nb_periodes_superieur_aux_donnees():
    """Si on demande plus de périodes que disponible, on renvoie tout sans erreur."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 10.0), creer_observation("FRA", "2024Q2", 11.0)]
    )

    serie = service.evolution("EMP", "FRA", nb_periodes=8)

    assert periodes(serie) == ["2024Q1", "2024Q2"]


@pytest.mark.parametrize("mauvaise_valeur", [0, -3])
def test_evolution_nb_periodes_invalide(mauvaise_valeur):
    """Un nombre de périodes inférieur à 1 est refusé."""
    service = creer_service([creer_observation("FRA", "2024Q1", 10.0)])

    with pytest.raises(DonneesInvalides):
        service.evolution("EMP", "FRA", nb_periodes=mauvaise_valeur)


def test_evolution_indicateur_inconnu():
    """Un indicateur inexistant lève RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.evolution("INCONNU", "FRA")


def test_evolution_pays_inconnu():
    """Un pays inexistant lève RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.evolution("EMP", "XXX")


def test_evolution_pays_vide():
    """Un code pays vide lève DonneesInvalides."""
    service = creer_service([])

    with pytest.raises(DonneesInvalides):
        service.evolution("EMP", "")


def test_evolution_classification_inconnue():
    """Une classification inexistante lève RessourceIntrouvable."""
    service = creer_service([creer_observation("FRA", "2024Q1", 10.0)])

    with pytest.raises(RessourceIntrouvable):
        service.evolution("EMP", "FRA", code_classification="INCONNUE")


def test_evolution_serie_vide():
    """Un indicateur et un pays valides mais sans aucune donnée lèvent RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.evolution("EMP", "FRA")


def test_evolution_sexe_par_defaut_est_total():
    """Sans sexe demandé, seules les observations 'total' sont utilisées."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0, sexe="total"),
            creer_observation("FRA", "2024Q1", 5.0, sexe="homme"),
            creer_observation("FRA", "2024Q1", 5.0, sexe="femme"),
        ]
    )

    serie = service.evolution("EMP", "FRA")

    assert valeurs(serie) == [10.0]


def test_evolution_sexe_demande():
    """Avec sexe=FEMME, on récupère les valeurs des femmes."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0, sexe="total"),
            creer_observation("FRA", "2024Q1", 4.0, sexe="femme"),
        ]
    )

    serie = service.evolution("EMP", "FRA", sexe=Sexe.FEMME)

    assert valeurs(serie) == [4.0]


def test_evolution_sexe_texte_inconnu():
    """Un sexe qui n'existe pas lève DonneesInvalides."""
    service = creer_service([creer_observation("FRA", "2024Q1", 10.0)])

    with pytest.raises(DonneesInvalides):
        service.evolution("EMP", "FRA", sexe="inconnu")


def test_evolution_ignore_les_valeurs_absentes():
    """Une observation sans valeur (None) n'apparaît pas dans la série."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("FRA", "2024Q2", None),
            creer_observation("FRA", "2024Q3", 12.0),
        ]
    )

    serie = service.evolution("EMP", "FRA")

    assert periodes(serie) == ["2024Q1", "2024Q3"]


def test_evolution_valeurs_decimal_converties_en_float():
    """PostgreSQL renvoie des Decimal : le service les convertit en float."""
    service = creer_service([creer_observation("FRA", "2024Q1", Decimal("10.5000"))])

    serie = service.evolution("EMP", "FRA")

    assert serie.points[0].valeur == 10.5
    assert isinstance(serie.points[0].valeur, float)


def test_evolution_sans_classification_ignore_les_lignes_classifiees():
    """Sans classification demandée, on garde seulement les lignes sans classification."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("FRA", "2024Q1", 3.0, classification="AGE_15_24"),
        ]
    )

    serie = service.evolution("EMP", "FRA")

    assert valeurs(serie) == [10.0]


def test_evolution_avec_classification():
    """Avec une classification demandée, on garde uniquement ses lignes."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("FRA", "2024Q1", 3.0, classification="AGE_15_24"),
        ]
    )

    serie = service.evolution("EMP", "FRA", code_classification="AGE_15_24")

    assert valeurs(serie) == [3.0]


def test_evolution_donnees_uniquement_classifiees_sans_choix():
    """Si les données existent seulement par classification et qu'aucune n'est choisie : erreur."""
    service = creer_service([creer_observation("FRA", "2024Q1", 3.0, classification="AGE_15_24")])

    with pytest.raises(DonneesInvalides):
        service.evolution("EMP", "FRA")


# F3 : résumé de l'évolution (statistiques et variation)


def test_resumer_evolution_calcule_les_statistiques():
    """Minimum, maximum, moyenne et variation sont calculés sur la série."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("FRA", "2024Q2", 12.0),
            creer_observation("FRA", "2024Q3", 8.0),
            creer_observation("FRA", "2024Q4", 15.0),
        ]
    )

    resume = service.resumer_evolution("EMP", "FRA")

    assert resume.libelle == "Emploi (milliers) - France"
    assert resume.nb_points == 4
    assert resume.periode_debut == "2024Q1"
    assert resume.periode_fin == "2024Q4"
    assert resume.valeur_debut == 10.0
    assert resume.valeur_fin == 15.0
    assert resume.minimum == 8.0
    assert resume.maximum == 15.0
    assert resume.moyenne == pytest.approx(11.25)
    assert resume.variation_absolue == pytest.approx(5.0)
    assert resume.variation_relative == pytest.approx(50.0)


def test_resumer_evolution_variation_negative():
    """Une baisse donne des variations négatives."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 10.0), creer_observation("FRA", "2024Q2", 8.0)]
    )

    resume = service.resumer_evolution("EMP", "FRA")

    assert resume.variation_absolue == pytest.approx(-2.0)
    assert resume.variation_relative == pytest.approx(-20.0)


def test_resumer_evolution_valeur_de_depart_nulle():
    """Si la première valeur est 0, la variation relative n'est pas calculable (None)."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 0.0), creer_observation("FRA", "2024Q2", 5.0)]
    )

    resume = service.resumer_evolution("EMP", "FRA")

    assert resume.variation_absolue == pytest.approx(5.0)
    assert resume.variation_relative is None


def test_resumer_evolution_un_seul_point():
    """Avec un seul point, il n'y a pas de variation à calculer (None)."""
    service = creer_service([creer_observation("FRA", "2024Q1", 10.0)])

    resume = service.resumer_evolution("EMP", "FRA")

    assert resume.nb_points == 1
    assert resume.moyenne == 10.0
    assert resume.variation_absolue is None
    assert resume.variation_relative is None


def test_resumer_evolution_respecte_nb_periodes():
    """Le résumé ne porte que sur les N dernières périodes demandées."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 100.0),
            creer_observation("FRA", "2024Q2", 10.0),
            creer_observation("FRA", "2024Q3", 20.0),
        ]
    )

    resume = service.resumer_evolution("EMP", "FRA", nb_periodes=2)

    assert resume.periode_debut == "2024Q2"
    assert resume.maximum == 20.0
    assert resume.variation_relative == pytest.approx(100.0)


def test_resumer_evolution_erreurs_de_evolution_propagees():
    """Les erreurs de evolution() (indicateur inconnu, série vide) sont reprises telles quelles."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.resumer_evolution("INCONNU", "FRA")
    with pytest.raises(RessourceIntrouvable):
        service.resumer_evolution("EMP", "FRA")


# F4 : comparaison entre pays


def test_comparer_pays_trie_du_plus_haut_au_plus_bas():
    """Les pays sont triés par valeur décroissante : le plus haut en premier."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("DEU", "2024Q1", 12.0),
            creer_observation("ESP", "2024Q1", 8.0),
        ]
    )

    resultat = service.comparer_pays("EMP", ["FRA", "DEU", "ESP"], periode="2024Q1")

    assert libelles(resultat) == ["Allemagne", "France", "Espagne"]
    assert resultat.series[0].points[0].valeur == 12.0
    assert resultat.series[-1].points[0].valeur == 8.0


def test_comparer_pays_sans_periode_prend_la_derniere_de_chaque_pays():
    """Sans période, chaque pays est pris à sa dernière période disponible."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("FRA", "2024Q2", 11.0),
            creer_observation("DEU", "2024Q1", 12.0),
        ]
    )

    resultat = service.comparer_pays("EMP", ["FRA", "DEU"])

    periode_par_pays = {serie.libelle: serie.points[0].periode for serie in resultat.series}
    assert periode_par_pays == {"France": "2024Q2", "Allemagne": "2024Q1"}


def test_comparer_pays_ignore_un_pays_sans_donnee_a_cette_periode():
    """Un pays sans donnée pour la période demandée n'apparaît pas dans le résultat."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 10.0), creer_observation("DEU", "2024Q2", 12.0)]
    )

    resultat = service.comparer_pays("EMP", ["FRA", "DEU"], periode="2024Q1")

    assert libelles(resultat) == ["France"]


def test_comparer_pays_egalite_departagee_par_nom():
    """Deux pays à égalité sont classés par ordre alphabétique."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 10.0), creer_observation("DEU", "2024Q1", 10.0)]
    )

    resultat = service.comparer_pays("EMP", ["FRA", "DEU"], periode="2024Q1")

    assert libelles(resultat) == ["Allemagne", "France"]


def test_comparer_pays_retire_les_doublons():
    """Un pays donné deux fois n'apparaît qu'une fois."""
    service = creer_service([creer_observation("FRA", "2024Q1", 10.0)])

    resultat = service.comparer_pays("EMP", ["FRA", "FRA"], periode="2024Q1")

    assert libelles(resultat) == ["France"]


def test_comparer_pays_liste_vide():
    """Une liste de pays vide lève DonneesInvalides."""
    service = creer_service([])

    with pytest.raises(DonneesInvalides):
        service.comparer_pays("EMP", [])


def test_comparer_pays_pays_inconnu():
    """Un pays inexistant dans la liste lève RessourceIntrouvable."""
    service = creer_service([creer_observation("FRA", "2024Q1", 10.0)])

    with pytest.raises(RessourceIntrouvable):
        service.comparer_pays("EMP", ["FRA", "XXX"], periode="2024Q1")


def test_comparer_pays_indicateur_inconnu():
    """Un indicateur inexistant lève RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.comparer_pays("INCONNU", ["FRA"])


def test_comparer_pays_aucune_donnee():
    """Si aucun pays n'a de donnée, on lève RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.comparer_pays("EMP", ["FRA", "DEU"], periode="2024Q1")


def test_comparer_pays_sexe_par_defaut_est_total():
    """La comparaison utilise le sexe 'total' par défaut."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0, sexe="total"),
            creer_observation("FRA", "2024Q1", 99.0, sexe="homme"),
        ]
    )

    resultat = service.comparer_pays("EMP", ["FRA"], periode="2024Q1")

    assert resultat.series[0].points[0].valeur == 10.0


def test_comparer_pays_avec_classification():
    """Avec une classification demandée, seules ses lignes sont comparées."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("FRA", "2024Q1", 3.0, classification="AGE_15_24"),
        ]
    )

    resultat = service.comparer_pays(
        "EMP", ["FRA"], periode="2024Q1", code_classification="AGE_15_24"
    )

    assert resultat.series[0].points[0].valeur == 3.0


# F5 : comparaison multi-indicateurs


def test_comparer_indicateurs_une_serie_par_indicateur():
    """Chaque indicateur donne une série dont le libellé contient l'unité."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 100.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q2", 101.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q1", 60.0, indicateur="TAUX"),
        ]
    )

    resultat = service.comparer_indicateurs(["EMP", "TAUX"], "FRA")

    assert libelles(resultat) == ["Emploi (milliers)", "Taux d'activité (%)"]
    assert valeurs(resultat.series[0]) == [100.0, 101.0]
    assert valeurs(resultat.series[1]) == [60.0]


def test_comparer_indicateurs_liste_vide():
    """Une liste d'indicateurs vide lève DonneesInvalides."""
    service = creer_service([])

    with pytest.raises(DonneesInvalides):
        service.comparer_indicateurs([], "FRA")


def test_comparer_indicateurs_pays_vide():
    """Un code pays vide lève DonneesInvalides."""
    service = creer_service([])

    with pytest.raises(DonneesInvalides):
        service.comparer_indicateurs(["EMP"], "")


def test_comparer_indicateurs_indicateur_inconnu():
    """Un indicateur inexistant lève RessourceIntrouvable."""
    service = creer_service([creer_observation("FRA", "2024Q1", 100.0)])

    with pytest.raises(RessourceIntrouvable):
        service.comparer_indicateurs(["EMP", "INCONNU"], "FRA")


def test_comparer_indicateurs_pays_inconnu():
    """Un pays inexistant lève RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.comparer_indicateurs(["EMP"], "XXX")


def test_comparer_indicateurs_ignore_un_indicateur_sans_donnee():
    """Un indicateur sans donnée pour ce pays est ignoré, les autres sont gardés."""
    service = creer_service([creer_observation("FRA", "2024Q1", 100.0, indicateur="EMP")])

    resultat = service.comparer_indicateurs(["EMP", "TAUX"], "FRA")

    assert libelles(resultat) == ["Emploi (milliers)"]


def test_comparer_indicateurs_aucune_donnee():
    """Si aucun indicateur n'a de donnée, on lève RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.comparer_indicateurs(["EMP", "TAUX"], "FRA")


def test_comparer_indicateurs_retire_les_doublons():
    """Un indicateur donné deux fois n'apparaît qu'une fois."""
    service = creer_service([creer_observation("FRA", "2024Q1", 100.0)])

    resultat = service.comparer_indicateurs(["EMP", "EMP"], "FRA")

    assert len(resultat.series) == 1


def test_comparer_indicateurs_base_100():
    """Avec base_100, chaque série vaut 100 à la période de base."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 100.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q2", 110.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q1", 50.0, indicateur="TAUX"),
            creer_observation("FRA", "2024Q2", 55.0, indicateur="TAUX"),
        ]
    )

    resultat = service.comparer_indicateurs(["EMP", "TAUX"], "FRA", base_100=True)

    assert libelles(resultat) == [
        "Emploi (base 100 = 2024Q1)",
        "Taux d'activité (base 100 = 2024Q1)",
    ]
    assert valeurs(resultat.series[0]) == pytest.approx([100.0, 110.0])
    assert valeurs(resultat.series[1]) == pytest.approx([100.0, 110.0])


def test_comparer_indicateurs_base_100_periode_commune():
    """La base est la première période commune, même si une série commence plus tôt."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 80.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q2", 100.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q3", 110.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q2", 50.0, indicateur="TAUX"),
            creer_observation("FRA", "2024Q3", 60.0, indicateur="TAUX"),
        ]
    )

    resultat = service.comparer_indicateurs(["EMP", "TAUX"], "FRA", base_100=True)

    assert resultat.series[0].libelle == "Emploi (base 100 = 2024Q2)"
    assert valeurs(resultat.series[0]) == pytest.approx([80.0, 100.0, 110.0])
    assert valeurs(resultat.series[1]) == pytest.approx([100.0, 120.0])


def test_comparer_indicateurs_base_100_un_seul_indicateur():
    """La base 100 fonctionne aussi avec un seul indicateur."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 20.0), creer_observation("FRA", "2024Q2", 30.0)]
    )

    resultat = service.comparer_indicateurs(["EMP"], "FRA", base_100=True)

    assert valeurs(resultat.series[0]) == pytest.approx([100.0, 150.0])


def test_comparer_indicateurs_base_100_sans_periode_commune():
    """Sans période commune entre les séries, la base 100 est impossible."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 100.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q2", 50.0, indicateur="TAUX"),
        ]
    )

    with pytest.raises(DonneesInvalides):
        service.comparer_indicateurs(["EMP", "TAUX"], "FRA", base_100=True)


@pytest.mark.parametrize("valeur_base", [0.0, -5.0])
def test_comparer_indicateurs_base_100_valeur_de_base_invalide(valeur_base):
    """Une valeur de base nulle ou négative empêche la base 100 (division impossible)."""
    service = creer_service([creer_observation("FRA", "2024Q1", valeur_base)])

    with pytest.raises(DonneesInvalides):
        service.comparer_indicateurs(["EMP"], "FRA", base_100=True)


def test_comparer_indicateurs_sans_base_100_garde_les_valeurs_brutes():
    """Par défaut (base_100 absent), les valeurs ne sont pas modifiées."""
    service = creer_service([creer_observation("FRA", "2024Q1", 20.0)])

    resultat = service.comparer_indicateurs(["EMP"], "FRA")

    assert valeurs(resultat.series[0]) == [20.0]


# Carte


def test_carte_une_serie_par_pays_triee_par_nom():
    """La carte renvoie un point par pays, triés par nom de pays."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0),
            creer_observation("ESP", "2024Q1", 8.0),
            creer_observation("DEU", "2024Q1", 12.0),
            creer_observation("FRA", "2024Q2", 99.0),
        ]
    )

    resultat = service.carte("EMP", "2024Q1")

    assert libelles(resultat) == ["Allemagne", "Espagne", "France"]
    assert [serie.points[0].valeur for serie in resultat.series] == [12.0, 8.0, 10.0]


def test_carte_periode_vide():
    """Une période vide lève DonneesInvalides."""
    service = creer_service([])

    with pytest.raises(DonneesInvalides):
        service.carte("EMP", "")


def test_carte_indicateur_inconnu():
    """Un indicateur inexistant lève RessourceIntrouvable."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable):
        service.carte("INCONNU", "2024Q1")


def test_carte_aucune_donnee():
    """Aucune donnée pour cette période : RessourceIntrouvable."""
    service = creer_service([creer_observation("FRA", "2024Q2", 10.0)])

    with pytest.raises(RessourceIntrouvable):
        service.carte("EMP", "2024Q1")


def test_carte_sexe_par_defaut_est_total():
    """La carte utilise le sexe 'total' par défaut."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0, sexe="total"),
            creer_observation("FRA", "2024Q1", 99.0, sexe="femme"),
        ]
    )

    resultat = service.carte("EMP", "2024Q1")

    assert [serie.points[0].valeur for serie in resultat.series] == [10.0]


# Périodes manquantes : fenêtre calendaire et signalement


def donnees_avec_trou():
    """France : 2023Q3 est absent (les autres trimestres de 2023Q1 à 2024Q1 existent)."""
    return [
        creer_observation("FRA", "2023Q1", 100.0),
        creer_observation("FRA", "2023Q2", 102.0),
        creer_observation("FRA", "2023Q4", 106.0),
        creer_observation("FRA", "2024Q1", 110.0),
    ]


def test_evolution_fenetre_calendaire_avec_periode_manquante():
    """Les 3 derniers trimestres sont 2023Q3, Q4 et 2024Q1 : seuls 2 existent, 2023Q3 manque."""
    service = creer_service(donnees_avec_trou())

    serie = service.evolution("EMP", "FRA", nb_periodes=3)

    assert periodes(serie) == ["2023Q4", "2024Q1"]
    assert serie.periodes_manquantes == ["2023Q3"]


def test_evolution_sans_limite_signale_les_trous():
    """Sans nb_periodes, toutes les données sont renvoyées et le trou est signalé."""
    service = creer_service(donnees_avec_trou())

    serie = service.evolution("EMP", "FRA")

    assert periodes(serie) == ["2023Q1", "2023Q2", "2023Q4", "2024Q1"]
    assert serie.periodes_manquantes == ["2023Q3"]


def test_evolution_serie_complete_sans_periode_manquante():
    """Une série sans trou n'a aucune période manquante."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 1.0), creer_observation("FRA", "2024Q2", 2.0)]
    )

    assert service.evolution("EMP", "FRA").periodes_manquantes == []


def test_evolution_moins_de_donnees_que_demande_liste_les_periodes_absentes():
    """Avec 2 trimestres disponibles pour 4 demandés, les 2 plus anciens sont manquants."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 1.0), creer_observation("FRA", "2024Q2", 2.0)]
    )

    serie = service.evolution("EMP", "FRA", nb_periodes=4)

    assert periodes(serie) == ["2024Q1", "2024Q2"]
    assert serie.periodes_manquantes == ["2023Q3", "2023Q4"]


def test_evolution_annees_avec_une_annee_manquante():
    """Avec des données annuelles, une année absente est signalée."""
    service = creer_service(
        [
            creer_observation("FRA", "2012", 1.0),
            creer_observation("FRA", "2014", 2.0),
            creer_observation("FRA", "2015", 3.0),
        ]
    )

    serie = service.evolution("EMP", "FRA")

    assert periodes(serie) == ["2012", "2014", "2015"]
    assert serie.periodes_manquantes == ["2013"]


def test_evolution_mois_tries_dans_l_ordre_du_calendrier():
    """2024M2 vient avant 2024M10 (l'ordre alphabétique les inverserait)."""
    service = creer_service(
        [creer_observation("FRA", "2024M10", 10.0), creer_observation("FRA", "2024M2", 2.0)]
    )

    assert periodes(service.evolution("EMP", "FRA")) == ["2024M2", "2024M10"]


def test_evolution_format_de_periode_inconnu_garde_les_n_dernieres_observations():
    """Format inconnu : on garde les N dernières observations, sans période manquante."""
    service = creer_service(
        [
            creer_observation("FRA", "T1-2024", 1.0),
            creer_observation("FRA", "T2-2024", 2.0),
            creer_observation("FRA", "T3-2024", 3.0),
        ]
    )

    serie = service.evolution("EMP", "FRA", nb_periodes=2)

    assert periodes(serie) == ["T2-2024", "T3-2024"]
    assert serie.periodes_manquantes == []


def test_resumer_evolution_utilise_la_fenetre_calendaire():
    """La variation porte sur les 3 derniers trimestres réels : 106 -> 110, soit +3,77 %."""
    service = creer_service(donnees_avec_trou())

    resume = service.resumer_evolution("EMP", "FRA", nb_periodes=3)

    assert resume.periode_debut == "2023Q4"
    assert resume.variation_relative == pytest.approx(4 / 106 * 100)
    assert resume.periodes_manquantes == ["2023Q3"]


# Cas où il n'y a pas de donnée : messages et erreurs explicites


def test_evolution_pays_connu_sans_donnee_message_explicite():
    """Le message dit que le pays existe mais qu'il n'a pas de donnée pour l'indicateur."""
    service = creer_service([])

    with pytest.raises(RessourceIntrouvable) as erreur:
        service.evolution("EMP", "FRA")

    assert "France" in str(erreur.value)
    assert "EMP" in str(erreur.value)
    assert "existe" in str(erreur.value)


def test_evolution_toutes_les_valeurs_absentes():
    """Des observations sans valeur ne comptent pas : RessourceIntrouvable, pas d'erreur de classification."""
    service = creer_service([creer_observation("FRA", "2024Q1", None)])

    with pytest.raises(RessourceIntrouvable):
        service.evolution("EMP", "FRA")


def test_evolution_classification_demandee_sans_donnee():
    """Régression : une classification existante sans donnée donne 404 (et non une erreur interne)."""
    service = creer_service([creer_observation("FRA", "2024Q1", 10.0)])

    with pytest.raises(RessourceIntrouvable):
        service.evolution("EMP", "FRA", code_classification="AGE_15_24")


def test_comparer_pays_donnees_uniquement_classifiees_sans_choix():
    """F4 : des données qui n'existent que par classification exigent de la préciser."""
    service = creer_service([creer_observation("FRA", "2024Q1", 3.0, classification="AGE_15_24")])

    with pytest.raises(DonneesInvalides):
        service.comparer_pays("EMP", ["FRA"], periode="2024Q1")


def test_comparer_indicateurs_donnees_uniquement_classifiees_sans_choix():
    """F5 : même règle pour la comparaison d'indicateurs."""
    service = creer_service([creer_observation("FRA", "2024Q1", 3.0, classification="AGE_15_24")])

    with pytest.raises(DonneesInvalides):
        service.comparer_indicateurs(["EMP"], "FRA")


def test_carte_donnees_uniquement_classifiees_sans_choix():
    """Carte : même règle."""
    service = creer_service([creer_observation("FRA", "2024Q1", 3.0, classification="AGE_15_24")])

    with pytest.raises(DonneesInvalides):
        service.carte("EMP", "2024Q1")


# Comparaisons : pays ou indicateurs demandés sans donnée


def test_comparer_pays_liste_les_pays_sans_donnee_a_la_periode():
    """Un pays sans donnée à la période demandée est omis ET listé dans sans_donnees."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 10.0), creer_observation("DEU", "2024Q2", 12.0)]
    )

    resultat = service.comparer_pays("EMP", ["FRA", "DEU", "ESP"], periode="2024Q1")

    assert libelles(resultat) == ["France"]
    assert resultat.sans_donnees == ["Allemagne", "Espagne"]


def test_comparer_pays_sans_periode_liste_les_pays_sans_aucune_donnee():
    """Sans période, un pays sans aucune donnée est listé dans sans_donnees."""
    service = creer_service([creer_observation("FRA", "2024Q1", 10.0)])

    resultat = service.comparer_pays("EMP", ["FRA", "ESP"])

    assert libelles(resultat) == ["France"]
    assert resultat.sans_donnees == ["Espagne"]


def test_comparer_pays_sans_donnees_vide_quand_tous_les_pays_ont_une_valeur():
    """Quand tous les pays ont une donnée, sans_donnees est vide."""
    service = creer_service(
        [creer_observation("FRA", "2024Q1", 10.0), creer_observation("DEU", "2024Q1", 12.0)]
    )

    assert service.comparer_pays("EMP", ["FRA", "DEU"], periode="2024Q1").sans_donnees == []


def test_comparer_pays_derniere_periode_dans_l_ordre_du_calendrier():
    """La dernière période est choisie dans le calendrier : 2024M10 est après 2024M2."""
    service = creer_service(
        [creer_observation("FRA", "2024M2", 5.0), creer_observation("FRA", "2024M10", 7.0)]
    )

    resultat = service.comparer_pays("EMP", ["FRA"])

    assert resultat.series[0].points[0].periode == "2024M10"
    assert resultat.series[0].points[0].valeur == 7.0


def test_comparer_indicateurs_liste_les_indicateurs_sans_donnee():
    """Un indicateur sans donnée pour le pays est omis ET listé dans sans_donnees."""
    service = creer_service([creer_observation("FRA", "2024Q1", 100.0, indicateur="EMP")])

    resultat = service.comparer_indicateurs(["EMP", "TAUX"], "FRA")

    assert libelles(resultat) == ["Emploi (milliers)"]
    assert resultat.sans_donnees == ["Taux d'activité (%)"]


def test_comparer_indicateurs_signale_les_periodes_manquantes_de_chaque_serie():
    """Chaque série indique ses propres périodes manquantes."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 1.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q3", 3.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q1", 1.0, indicateur="TAUX"),
            creer_observation("FRA", "2024Q2", 2.0, indicateur="TAUX"),
        ]
    )

    resultat = service.comparer_indicateurs(["EMP", "TAUX"], "FRA")

    assert resultat.series[0].periodes_manquantes == ["2024Q2"]
    assert resultat.series[1].periodes_manquantes == []


def test_comparer_indicateurs_base_100_conserve_les_periodes_manquantes():
    """La mise en base 100 garde l'information sur les périodes manquantes."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 100.0, indicateur="EMP"),
            creer_observation("FRA", "2024Q3", 120.0, indicateur="EMP"),
        ]
    )

    resultat = service.comparer_indicateurs(["EMP"], "FRA", base_100=True)

    assert resultat.series[0].periodes_manquantes == ["2024Q2"]
    assert valeurs(resultat.series[0]) == pytest.approx([100.0, 120.0])


def test_comparer_indicateurs_base_100_choisit_la_premiere_periode_commune_du_calendrier():
    """La base est la première période commune dans le calendrier, pas dans l'ordre alphabétique."""
    service = creer_service(
        [
            creer_observation("FRA", "2024M10", 200.0, indicateur="EMP"),
            creer_observation("FRA", "2024M2", 100.0, indicateur="EMP"),
            creer_observation("FRA", "2024M10", 50.0, indicateur="TAUX"),
            creer_observation("FRA", "2024M2", 40.0, indicateur="TAUX"),
        ]
    )

    resultat = service.comparer_indicateurs(["EMP", "TAUX"], "FRA", base_100=True)

    assert resultat.series[0].libelle == "Emploi (base 100 = 2024M2)"


# Doublons : une nouvelle observation pour une période déjà présente


def test_evolution_doublon_sur_une_periode_garde_l_import_le_plus_recent():
    """Si une période apparaît deux fois, la valeur importée en dernier est retenue."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0, date_import=datetime(2024, 1, 1)),
            creer_observation("FRA", "2024Q1", 12.0, date_import=datetime(2024, 6, 1)),
            creer_observation("FRA", "2024Q2", 20.0, date_import=datetime(2024, 6, 1)),
        ]
    )

    serie = service.evolution("EMP", "FRA")

    assert periodes(serie) == ["2024Q1", "2024Q2"]
    assert valeurs(serie) == [12.0, 20.0]


def test_evolution_doublon_garde_la_valeur_recente_meme_si_elle_est_listee_en_premier():
    """L'ordre dans la liste ne compte pas : c'est la date d'import qui décide."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 12.0, date_import=datetime(2024, 6, 1)),
            creer_observation("FRA", "2024Q1", 10.0, date_import=datetime(2024, 1, 1)),
        ]
    )

    assert valeurs(service.evolution("EMP", "FRA")) == [12.0]


def test_carte_doublon_pour_un_pays_garde_l_import_le_plus_recent():
    """Sur la carte, un pays n'a qu'une valeur : la plus récemment importée."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0, date_import=datetime(2024, 1, 1)),
            creer_observation("FRA", "2024Q1", 12.0, date_import=datetime(2024, 6, 1)),
        ]
    )

    resultat = service.carte("EMP", "2024Q1")

    assert [serie.points[0].valeur for serie in resultat.series] == [12.0]


def test_comparer_pays_doublon_pour_un_pays_garde_l_import_le_plus_recent():
    """En comparaison de pays, un pays n'apparaît qu'une fois avec sa valeur la plus récente."""
    service = creer_service(
        [
            creer_observation("FRA", "2024Q1", 10.0, date_import=datetime(2024, 1, 1)),
            creer_observation("FRA", "2024Q1", 12.0, date_import=datetime(2024, 6, 1)),
        ]
    )

    resultat = service.comparer_pays("EMP", ["FRA"], periode="2024Q1")

    assert len(resultat.series) == 1
    assert resultat.series[0].points[0].valeur == 12.0
