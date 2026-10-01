from io import StringIO

import pandas as pd  # type: ignore[import-untyped]
import requests  # type: ignore[import-untyped]

from utils.log_utils import get_logger  # type: ignore[import-not-found]

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

        params = {
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
