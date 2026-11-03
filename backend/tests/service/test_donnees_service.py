"""Tests unitaires du service d'administration des observations."""

from business_object.observation import Observation
from service.donnees_service import DonneesService


class FauxObservationDao:
    """DAO en mémoire permettant de vérifier les appels du service."""

    def __init__(self):
        self.observations = []
        self.filtres_recus = None
        self.observation_modifiee = None
        self.id_supprime = None
        self.resultat_modification = True
        self.resultat_suppression = True

    def rechercher(self, **filtres):
        self.filtres_recus = filtres
        return self.observations

    def modifier(self, observation):
        self.observation_modifiee = observation
        return self.resultat_modification

    def supprimer(self, observation_id):
        self.id_supprime = observation_id
        return self.resultat_suppression


def test_rechercher_transmet_les_filtres_et_retourne_les_observations():
    dao = FauxObservationDao()
    observation = Observation(id=12, code_pays="FRA", periode="2024")
    dao.observations = [observation]
    service = DonneesService(dao)

    resultat = service.rechercher(code_pays="FRA", periode="2024")

    assert resultat == [observation]
    assert dao.filtres_recus == {"code_pays": "FRA", "periode": "2024"}


def test_corriger_transmet_observation_et_retourne_resultat_du_dao():
    dao = FauxObservationDao()
    observation = Observation(id=12, valeur=3.5, source="correction manuelle")
    service = DonneesService(dao)

    resultat = service.corriger(observation)

    assert resultat is True
    assert dao.observation_modifiee is observation


def test_corriger_sans_identifiant_ne_tente_pas_de_modification():
    dao = FauxObservationDao()
    service = DonneesService(dao)

    resultat = service.corriger(Observation(valeur=3.5))

    assert resultat is False
    assert dao.observation_modifiee is None


def test_corriger_retourne_false_si_le_dao_ne_trouve_pas_l_observation():
    dao = FauxObservationDao()
    dao.resultat_modification = False
    service = DonneesService(dao)

    resultat = service.corriger(Observation(id=404, valeur=3.5))

    assert resultat is False


def test_supprimer_transmet_identifiant_et_retourne_resultat_du_dao():
    dao = FauxObservationDao()
    service = DonneesService(dao)

    resultat = service.supprimer(12)

    assert resultat is True
    assert dao.id_supprime == 12


def test_supprimer_retourne_false_si_le_dao_ne_trouve_pas_l_observation():
    dao = FauxObservationDao()
    dao.resultat_suppression = False
    service = DonneesService(dao)

    resultat = service.supprimer(404)

    assert resultat is False
    assert dao.id_supprime == 404
