
import sys
sys.path.insert(0, "backend/src")

from business_object.enums import StatutImport
from client.ilostat_client import IlostatClient
from service.collecte_service import CollecteService
from service.parser_service import ParserService


class FauxImportDao:
    def creer(self, trace):
        trace.id = 1
        return trace

    def mettre_a_jour(self, trace):
        pass


class FauxConnexion:
    def rollback(self):
        pass


class FauxObservationDao:
    def __init__(self):
        self.conn = FauxConnexion()
        self.observations = []

    def inserer_ou_mettre_a_jour_par_lot(self, observations):
        self.observations = observations
        return len(observations)


service = CollecteService.__new__(CollecteService)
service.import_dao = FauxImportDao()
service.observation_dao = FauxObservationDao()
service.parser_service = ParserService()
service.ilostat_client = IlostatClient()

trace = service.collecter_indicateur(
    code_indicateur="EMP_TEMP_SEX_OCU_NB",
    from_date=2020,
    to_date=2021,
)

assert trace.statut == StatutImport.SUCCES, trace.message_erreur
assert trace.nombre_lignes > 0
assert all(observation.import_id == trace.id
           for observation in service.observation_dao.observations)

print(f"Test réussi : {trace.nombre_lignes} observations traitées")