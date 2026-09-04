from io import StringIO

import pandas as pd
import requests

from utils.log_utils import get_logger

logger = get_logger(__name__)

logger.info("Début de la fonction get_data_from_ilo_for_one_indicator")
def get_data_from_ilo_for_one_indicator(indicator_id= "EMP_5EMP_SEX_OC2_NB_Q",
                                        from_date: int = 2014,
                                        to_date: int = 2026) -> pd.DataFrame | None:
    """
    Récupère les données de l'API ILO pour un indicateur donné sur une période spécifiée.
    Args:
        indicator_id: identifiant de l'indicateur à récupérer.
        from_date: année de début de la période.
        to_date: année de fin de la période.
    Returns:
        pd.DataFrame | None: DataFrame contenant les données, ou None en cas d'erreur.
    """
       
    logger.info(f"Début de la fonction get_data_from_ilo_for_one_indicator pour l'indicateur {indicator_id} de {from_date} à {to_date}")
    try:
        logger.info(f"Téléchargement des données depuis {from_date} jusqu'à {to_date}...")
        r = requests.get(f"https://rplumber.ilo.org/data/indicator?id={indicator_id}&timefrom={from_date}&timeto={to_date}&type=label&format=.csv")
        r.raise_for_status()
        logger.info("Requête réussie, lecture du CSV...")
        df = pd.read_csv(StringIO(r.text))
        logger.info("Affichage des premières lignes du DataFrame :")
        logger.info("Données récupérées avec succès.")
        return df
    except Exception as e:
        logger.error("Une erreur est survenue lors de la récupération des données:")
        logger.error(e)
        return None
