"""Client HTTP vers l'API ILOSTAT."""

import requests


class IlostatClient:
    """Télécharge le CSV brut d'un indicateur ILOSTAT."""

    BASE_URL = "https://rplumber.ilo.org/data/indicator"
    TIMEOUT_SECONDS = 60

    def telecharger_indicateur(
        self,
        code_indicateur: str,
        from_date: int = 2014,
        to_date: int = 2026,
    ) -> str:
        """Renvoie le CSV brut de l'indicateur pour la période demandée.

        Les codes ILOSTAT sont demandés plutôt que les libellés afin de
        conserver les clés attendues par les référentiels de l'application.
        Les erreurs HTTP sont propagées à l'appelant.
        """
        if not code_indicateur or not code_indicateur.strip():
            raise ValueError("Le code de l'indicateur est obligatoire.")
        if from_date > to_date:
            raise ValueError(
                "L'année de début (from_date) doit être inférieure ou égale à l'année de fin (to_date)."
            )

        params: dict[str, str | int] = {
            "id": code_indicateur.strip(),
            "timefrom": from_date,
            "timeto": to_date,
            "type": "code",
            "format": ".csv",
        }
        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=self.TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.text
