"""Collecte, parsing et persistance des données ILOSTAT."""

import io
from datetime import datetime

import pandas as pd
from business_object.enums import StatutImport
from business_object.import_donnees import ImportDonnees
from client.ilostat_client import IlostatClient
from dao.import_dao import ImportDao
from dao.observation_dao import ObservationDao
from service.parser_service import ParserService
from utils.journalisation import get_logger

logger = get_logger(__name__)


class CollecteService:
    """Télécharge un indicateur, le parse, l'enregistre et trace l'import."""

    def __init__(self, ilostat_client: IlostatClient | None = None):
        self.import_dao = ImportDao()
        self.observation_dao = ObservationDao()
        self.parser_service = ParserService()
        self.ilostat_client = ilostat_client or IlostatClient()

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

        trace = self.import_dao.creer(
            ImportDonnees(
                indicateur_code=code_indicateur.strip(),
                utilisateur_id=utilisateur_id,
                date_debut=datetime.now(),
                statut=StatutImport.EN_COURS,
                fichier_source=IlostatClient.BASE_URL,
            )
        )

        try:
            logger.info(
                "Collecte ILOSTAT : indicateur=%s, période=%s-%s",
                code_indicateur,
                from_date,
                to_date,
            )
            csv_brut = self.ilostat_client.telecharger_indicateur(
                code_indicateur=code_indicateur.strip(),
                from_date=from_date,
                to_date=to_date,
            )
            data = pd.read_csv(io.StringIO(csv_brut))
            observations = self.parser_service.parser(data, code_indicateur.strip())
            if not observations:
                raise ValueError("Aucune observation exploitable reçue pour cet indicateur.")

            for observation in observations:
                observation.import_id = trace.id

            trace.nombre_lignes = self.observation_dao.inserer_ou_mettre_a_jour_par_lot(
                observations
            )
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
