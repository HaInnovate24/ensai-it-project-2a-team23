"""F1 : collecte des données ILOSTAT."""

import io
import requests
import pandas as pd
from datetime import datetime

from business_object.import_donnees import ImportDonnees
from business_object.enums import StatutImport
from dao.import_dao import ImportDao
from dao.observation_dao import ObservationDao
from service.parser_service import ParserService
from utils.journalisation import get_logger

logger = get_logger(__name__)

class CollecteService:
    """Télécharge un indicateur, le fait parser, l'enregistre et trace l'import."""

    BASE_URL = "https://rplumber.ilo.org/data/indicator"

    def __init__(self):
        self.import_dao = ImportDao()
        self.observation_dao = ObservationDao()
        self.parser_service = ParserService()

    def collecter_indicateur(
        self, 
        code_indicateur: str, 
        from_date: int = 2014,
        to_date: int = 2026,
        utilisateur_id: int | None = None
    ) -> ImportDonnees:
        """Collecte un indicateur sur une période et renvoie la trace d'import."""
        if from_date > to_date:
            raise ValueError("L'année de début (from_date) doit être inférieure ou égale à l'année de fin (to_date)")
        
        trace = self.import_dao.creer(
            ImportDonnees(
                indicateur_code=code_indicateur,
                utilisateur_id=utilisateur_id,
                date_debut=datetime.now(),
                statut=StatutImport.EN_COURS
            )
        )

        try:
            params = {
                "id": code_indicateur,
                "timefrom": from_date,
                "timeto": to_date,
                "type": "label",
                "format": ".csv",
            }

            logger.info(f"Collecte des données ILOSTAT: indicateur={code_indicateur}, période={from_date}-{to_date}")
            response = requests.get(self.BASE_URL, params=params, timeout=60)
            response.raise_for_status()

            # Lecture et parsing
            df_brut = pd.read_csv(io.StringIO(response.text))
            observations = self.parser_service.parser(df_brut, code_indicateur)

            # Association de l'import et insertion en base
            for obs in observations:
                obs.import_id = trace.id
            
            trace.nombre_lignes = self.observation_dao.inserer_ou_mettre_a_jour_par_lot(observations)
            trace.statut = StatutImport.SUCCES

        except Exception as e:
            logger.error(f"Erreur lors de la collecte de {code_indicateur}: {e}")
            trace.statut = StatutImport.ECHEC
            trace.message_erreur = str(e)[:250]
        
        finally:
            trace.date_fin = datetime.now()
            self.import_dao.mettre_a_jour(trace)

        return trace