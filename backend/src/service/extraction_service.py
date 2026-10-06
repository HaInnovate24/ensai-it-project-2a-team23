from io import StringIO

import pandas as pd
import requests

from utils.log_utils import get_logger

logger = get_logger(__name__)


class ExtractionService:
    """Fetches data d'un indicateur depuis l'API ILOSTAT."""

    BASE_URL = "https://rplumber.ilo.org/data/indicator"

    def get_indicator_data(
        self,
        indicator_id: str,
        from_date: int = 2014,
        to_date: int = 2026,
    ) -> pd.DataFrame:
        if from_date > to_date:
            raise ValueError("from_date must be less than or equal to to_date")

        params: dict[str, str | int] = {
        "id": indicator_id,
        "timefrom": from_date,
        "timeto": to_date,
        "type": "label",
        "format": ".csv",
        }

        logger.info(
            "Fetching ILO data: indicator=%s, period=%s-%s",
            indicator_id,
            from_date,
            to_date,
        )
        response = requests.get(self.BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))


    def get_data_from_ilo_for_one_indicator(
        self,
        indicator_id: str = "EMP_5EMP_SEX_OC2_NB_Q",
        from_date: int = 2014,
        to_date: int = 2026,
    ) -> pd.DataFrame:
        """
        Méthode utilitaire pour traiter un seul indicateur sur une période donnée.

        Args:
            indicator_id (str, optionnel): Identifiant de l'indicateur. Valeur par défaut "EMP_5EMP_SEX_OC2_NB_Q".
            from_date (int, optionnel): Année de début de période. Valeur par défaut 2014.
            to_date (int, optionnel): Année de fin de période. Valeur par défaut 2026.

        Returns:
            pd.DataFrame: Les données extraites pour l'indicateur demandé sous forme de DataFrame.
        """

        logger.info(
            "Traitement de l'indicateur %s (%s-%s)",
            indicator_id,
            from_date,
            to_date,
        )

        return self.get_indicator_data(
            indicator_id=indicator_id,
            from_date=from_date,
            to_date=to_date,
        )
