from business_object.enums import StatutImport
from service.collecte_service import CollecteService
from service.parser_service import ParserService


class FauxImportDao:
    def __init__(self):
        self.trace_mise_a_jour = None

    def creer(self, trace):
        trace.id = 42
        return trace

    def mettre_a_jour(self, trace):
        self.trace_mise_a_jour = trace


class FauxConnexion:
    def rollback(self):
        pass


class FauxObservationDao:
    def __init__(self):
        self.conn = FauxConnexion()
        self.observations = []
        self.appels_insertion = 0

    def inserer_ou_mettre_a_jour_par_lot(self, observations):
        self.appels_insertion += 1
        self.observations = observations
        return len(observations)


class FauxIlostatClient:
    def __init__(self, annees_telechargees=(), avec_doublons=False):
        self.annees_telechargees = set(annees_telechargees)
        self.avec_doublons = avec_doublons
        self.appels_telechargement = []

    def lister_annees_telechargees(self, code_indicateur, from_date, to_date):
        return {
            annee
            for annee in self.annees_telechargees
            if from_date <= annee <= to_date
        }

    def telecharger_indicateur(self, code_indicateur, from_date, to_date):
        self.appels_telechargement.append((from_date, to_date))
        lignes = ["ref_area,time,sex,obs_value,classif1"]
        for annee in range(from_date, to_date + 1):
            lignes.append(f"FRA,{annee},SEX_M,12.5,OCU_ISCO08_1")
            if self.avec_doublons:
                lignes.append(f"FRA,{annee},SEX_M,15.0,OCU_ISCO08_1")
        return "\n".join(lignes) + "\n"


def creer_service(client):
    service = CollecteService.__new__(CollecteService)
    service.import_dao = FauxImportDao()
    service.observation_dao = FauxObservationDao()
    service.parser_service = ParserService()
    service.ilostat_client = client
    return service


def test_collecter_telecharge_et_sauvegarde_les_annees_absentes():
    client = FauxIlostatClient(annees_telechargees=range(2014, 2021))
    service = creer_service(client)

    trace = service.collecter_indicateur(
        "EMP_TEMP_SEX_OCU_NB", from_date=2016, to_date=2022
    )

    assert trace.statut == StatutImport.SUCCES
    assert client.appels_telechargement == [(2021, 2022)]
    assert trace.nombre_lignes == 2
    assert all(obs.periode in {"2021", "2022"} for obs in service.observation_dao.observations)
    assert all(obs.import_id == trace.id for obs in service.observation_dao.observations)


def test_collecter_ne_telecharge_pas_une_periode_deja_en_archive():
    client = FauxIlostatClient(annees_telechargees=range(2014, 2021))
    service = creer_service(client)

    trace = service.collecter_indicateur(
        "EMP_TEMP_SEX_OCU_NB", from_date=2016, to_date=2020
    )

    assert trace.statut == StatutImport.SUCCES
    assert trace.nombre_lignes == 0
    assert client.appels_telechargement == []
    assert service.observation_dao.appels_insertion == 0


def test_collecter_regroupe_seulement_les_plages_manquantes():
    client = FauxIlostatClient(annees_telechargees={2014, 2016, 2018})
    service = creer_service(client)

    trace = service.collecter_indicateur(
        "EMP_TEMP_SEX_OCU_NB", from_date=2014, to_date=2019
    )

    assert trace.statut == StatutImport.SUCCES
    assert client.appels_telechargement == [(2015, 2015), (2017, 2017), (2019, 2019)]


def test_collecter_dedoublonne_le_lot_avant_sauvegarde():
    client = FauxIlostatClient(avec_doublons=True)
    service = creer_service(client)

    trace = service.collecter_indicateur(
        "EMP_TEMP_SEX_OCU_NB", from_date=2020, to_date=2020
    )

    observations = service.observation_dao.observations
    assert trace.statut == StatutImport.SUCCES
    assert trace.nombre_lignes == 1
    assert len(observations) == 1
    assert observations[0].valeur == 15.0
