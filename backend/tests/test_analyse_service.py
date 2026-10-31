"""Tests du service d'analyse (F3, F4, F5 et carte), sans base de données.

Principe : on donne au service de "faux DAO" qui travaillent sur des listes
en mémoire. On teste ainsi uniquement la logique du service.
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
    pays, periode, valeur, sexe="total", classification=None, indicateur="EMP"
):
    """Fabrique une observation de test (évite de répéter tous les arguments)."""
    return Observation(
        code_indicateur=indicateur,
        code_pays=pays,
        periode=periode,
        valeur=valeur,
        sexe=sexe,
        code_classification=classification,
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


# ----------------------------------------------------------------------
# F3 : évolution
# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------
# F4 : comparaison entre pays
# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------
# F5 : comparaison multi-indicateurs
# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------
# Carte
# ----------------------------------------------------------------------


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
