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
    """Faux client renvoyant le CSV consolidé de la période demandée.

    Comme le vrai client, il assume seul la gestion du cache de fichiers : le
    service se contente de lui demander toute la période puis d'upserter le CSV
    reçu. Les tests de découpage/cache par année vivent côté client.
    """

    def __init__(self, avec_doublons=False, csv=None):
        self.avec_doublons = avec_doublons
        self.csv = csv
        self.appels_telechargement = []

    def telecharger_indicateur(self, code_indicateur, from_date, to_date):
        self.appels_telechargement.append((from_date, to_date))
        if self.csv is not None:
            return self.csv
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


def test_collecter_demande_toute_la_periode_et_sauvegarde():
    client = FauxIlostatClient()
    service = creer_service(client)

    trace = service.collecter_indicateur(
        "EMP_TEMP_SEX_OCU_NB", from_date=2016, to_date=2022
    )

    # Le service délègue la gestion du cache au client : il demande toujours la
    # période complète en un seul appel, puis parse et upsert tout le CSV reçu.
    assert client.appels_telechargement == [(2016, 2022)]
    assert trace.statut == StatutImport.SUCCES
    assert trace.nombre_lignes == 7
    assert {obs.periode for obs in service.observation_dao.observations} == {
        str(annee) for annee in range(2016, 2023)
    }
    assert all(obs.import_id == trace.id for obs in service.observation_dao.observations)


def test_collecter_reinsere_le_csv_meme_deja_en_cache():
    # Données présentes dans le CSV renvoyé par le client mais absentes de la
    # base (ex. après une réinitialisation) : le service doit les parser et les
    # upserter, et non les ignorer sous prétexte que rien n'a été téléchargé.
    csv = (
        "ref_area,time,sex,obs_value,classif1\n"
        "FRA,2020,SEX_T,10.0,OCU_ISCO08_1\n"
        "DEU,2020,SEX_T,20.0,OCU_ISCO08_1\n"
    )
    client = FauxIlostatClient(csv=csv)
    service = creer_service(client)

    trace = service.collecter_indicateur("EMP_TEMP_SEX_OCU_NB", 2020, 2020)

    assert trace.statut == StatutImport.SUCCES
    assert service.observation_dao.appels_insertion == 1
    assert trace.nombre_lignes == 2


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


def test_collecter_csv_vide_renvoie_succes_sans_insertion():
    client = FauxIlostatClient(csv="")
    service = creer_service(client)

    trace = service.collecter_indicateur("EMP_TEMP_SEX_OCU_NB", 2020, 2020)

    assert trace.statut == StatutImport.SUCCES
    assert trace.nombre_lignes == 0
    assert service.observation_dao.appels_insertion == 0
