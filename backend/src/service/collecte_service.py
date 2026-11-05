"""Collecte, parsing et persistance des données ILOSTAT."""

import io
from datetime import datetime

import pandas as pd

from business_object.enums import StatutImport
from business_object.import_donnees import ImportDonnees
from client.ilostat_client import IlostatClient
from dao.classification_dao import ClassificationDao
from dao.import_dao import ImportDao
from dao.indicateur_dao import IndicateurDao
from dao.observation_dao import ObservationDao
from dao.pays_dao import PaysDao
from service.parser_service import ParserService
from utils.journalisation import get_logger

logger = get_logger(__name__)


class CollecteService:
    """Télécharge un indicateur, le parse, l'enregistre et trace l'import."""

    def __init__(
        self, 
        ilostat_client: IlostatClient | None = None,
        import_dao: ImportDao | None = None,
        observation_dao: ObservationDao | None = None,
        pays_dao: PaysDao | None = None,
        classification_dao: ClassificationDao | None = None,
        indicateur_dao: IndicateurDao | None = None,
        parser_service: ParserService | None = None
    ):
        self.ilostat_client = ilostat_client or IlostatClient()
        self.import_dao = import_dao or ImportDao()
        self.observation_dao = observation_dao or ObservationDao()
        self.pays_dao = pays_dao or PaysDao()
        self.classification_dao = classification_dao or ClassificationDao()
        self.indicateur_dao = indicateur_dao or IndicateurDao()
        self.parser_service = parser_service or ParserService()

    def collecter_indicateur(
        self,
        code_indicateur: str,
        from_date: int = 2014,
        to_date: int = 2026,
        utilisateur_id: int | None = None,
    ) -> ImportDonnees:
        """Collecte un indicateur sur une période et renvoie la trace d'import."""
        if not code_indicateur or not code_indicateur.strip():
            raise ValueError("Le code de l'indicateur est obligatoire.")
        if from_date > to_date:
            raise ValueError(
                "L'année de début (from_date) doit être inférieure ou égale à l'année de fin (to_date)."
            )

        trace = None

        try:
            logger.info(
                "Collecte ILOSTAT : indicateur=%s, période=%s-%s",
                code_indicateur,
                from_date,
                to_date,
            )

            trace = self.import_dao.creer(
                ImportDonnees(
                    indicateur_code=code_indicateur.strip(),
                    utilisateur_id=utilisateur_id,
                    date_debut=datetime.now(),
                    statut=StatutImport.EN_COURS,
                    fichier_source=IlostatClient.BASE_URL,
                )
            )

            # Le client ne télécharge que les années absentes du cache de
            # fichiers, puis renvoie le CSV consolidé de toute la période
            # demandée. On parse et on upsert donc systématiquement l'ensemble
            # de la période : les données présentes dans les fichiers CSV mais
            # absentes de la base (par exemple après une réinitialisation) sont
            # ainsi réinsérées, l'upsert restant idempotent pour celles déjà
            # présentes en base.
            csv_brut = self.ilostat_client.telecharger_indicateur(
                code_indicateur=code_indicateur.strip(),
                from_date=from_date,
                to_date=to_date,
            )
            observations = []
            if csv_brut.strip():
                data = pd.read_csv(io.StringIO(csv_brut))
                observations = self.parser_service.parser(data, code_indicateur.strip())
                if not observations:
                    raise ValueError("Aucune observation exploitable reçue pour cet indicateur.")
                # ILOSTAT renvoie des pays et classifications absents de nos
                # référentiels (contraintes de clés étrangères sur observation).
                # On écarte ces lignes pour que l'import n'échoue pas globalement.
                observations = self._filtrer_referentiels_connus(observations)

            # La contrainte uq_observation est aussi appliquée par le DAO en base,
            # mais PostgreSQL ne peut pas traiter deux fois la même clé dans un
            # seul INSERT ... ON CONFLICT. On garde donc la dernière valeur reçue
            # pour chaque combinaison unique avant l'upsert.
            observations_uniques = {}
            for observation in observations:
                observation.import_id = trace.id
                sexe = (
                    observation.sexe.value
                    if hasattr(observation.sexe, "value")
                    else observation.sexe
                )
                cle = (
                    observation.code_indicateur,
                    observation.code_pays,
                    observation.periode,
                    sexe,
                    observation.code_classification,
                )
                observations_uniques[cle] = observation

            nombre_doublons = len(observations) - len(observations_uniques)
            if nombre_doublons:
                logger.info(
                    "%s doublon(s) écarté(s) pour l'indicateur %s",
                    nombre_doublons,
                    code_indicateur,
                )
            observations = list(observations_uniques.values())
            if observations:
                trace.nombre_lignes = self.observation_dao.inserer_ou_mettre_a_jour_par_lot(
                    observations
                )
            else:
                trace.nombre_lignes = 0
            trace.statut = StatutImport.SUCCES
            trace.message_erreur = None
        except Exception as exc:
            logger.exception("Échec de la collecte de l'indicateur %s", code_indicateur)
            # Une erreur pendant l'upsert laisse PostgreSQL dans une transaction
            # avortée. Le rollback permet au DAO d'import de sauvegarder l'échec.
            self.observation_dao.conn.rollback()
            trace.statut = StatutImport.ECHEC
            trace.message_erreur = str(exc)[:250]
        finally:
            trace.date_fin = datetime.now()
            self.import_dao.mettre_a_jour(trace)

        return trace

    def _filtrer_referentiels_connus(self, observations: list) -> list:
        """Écarte les observations dont le pays ou la classification est inconnu.

        Les colonnes ``code_pays`` et ``code_classification`` d'``observation``
        sont des clés étrangères : une valeur absente des référentiels ferait
        échouer tout le lot. On conserve donc uniquement les lignes compatibles
        (classification vide autorisée).
        """
        codes_pays = {pays.code_pays for pays in self.pays_dao.lister()}
        codes_classif = {c.code for c in self.classification_dao.lister()}

        retenues = []
        ignorees = 0
        for obs in observations:
            if obs.code_pays not in codes_pays:
                ignorees += 1
                continue
            if obs.code_classification and obs.code_classification not in codes_classif:
                ignorees += 1
                continue
            retenues.append(obs)

        if ignorees:
            logger.info(
                "%s observation(s) ignorée(s) : pays ou classification hors référentiel.",
                ignorees,
            )
        return retenues

    def lister_imports(self) -> list[ImportDonnees]:
        """
        Lister toutes les historiques d'imports
        """
        return self.import_dao.lister()


if __name__ == "__main__":
    collecte_service = CollecteService()
    trace = collecte_service.collecter_indicateur("SR_LMP_SEX_AGE_NB")
    print(trace)
    print(trace.nombre_lignes)
    print(trace.statut)
    print(trace.message_erreur)
    print(trace.date_debut)
    print(trace.date_fin)
    print(trace.fichier_source)
    print(trace.indicateur_code)
    print(trace.utilisateur_id)