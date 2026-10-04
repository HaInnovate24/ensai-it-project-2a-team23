"""F2 : transformation des données brutes en observations."""

import re
import pandas as pd
from business_object.observation import Observation
from business_object.enums import Sexe

class ParserService:
    """Transforme le DataFrame ILOSTAT en objets Observation."""

    ALIASES = {
        "country": {"ref_area", "ref_area_label", "country", "country_name", "geo"},
        "sex": {"sex", "sex_label"},
        "period": {"time", "time_period", "period", "time_label"},
        "value": {"obs_value", "observation_value", "value"},
    }

    def parser(self, data: pd.DataFrame, indicator_id: str) -> list[Observation]:
        """Parse le DataFrame en observations, en rejetant les lignes invalides."""
        if data.empty:
            return []

        # 1. Normalisation des noms de colonnes via la logique de Vicram
        columns = {self._normalize_name(col): col for col in data.columns}
        rename = {}
        for field, aliases in self.ALIASES.items():
            source = next((columns[name] for name in aliases if name in columns), None)
            if source is not None:
                rename[source] = field
        
        parsed = data.rename(columns=rename).copy()

        # 2. Extraction des classifications (âge ou occupation)
        for column in data.columns:
            name = self._normalize_name(column)
            if "age" in name and "age_group" not in parsed:
                parsed["age_group"] = data[column]
            elif any(term in name for term in ("occupation", "oc2", "isco")):
                if "occupation" not in parsed:
                    parsed["occupation"] = data[column]

        # 3. Filtrage des valeurs nulles
        if "value" not in parsed:
            raise ValueError("Colonne de valeur introuvable dans les données retournées par l'API.")
        parsed = parsed.dropna(subset=["value"])

        observations = []

        # 4. Instanciation des objets métier pour le DAO
        for _, row in parsed.iterrows():
            # Typage robuste du sexe
            valeur_sexe = str(row.get("sex", "T")).upper()
            if "M" in valeur_sexe or "HOMME" in valeur_sexe:
                sexe_enum = Sexe.HOMME
            elif "F" in valeur_sexe or "FEMME" in valeur_sexe:
                sexe_enum = Sexe.FEMME
            else:
                sexe_enum = Sexe.TOTAL

            # Consolidation de la classification
            code_classif = None
            if pd.notna(row.get("age_group")):
                code_classif = str(row["age_group"])
            elif pd.notna(row.get("occupation")):
                code_classif = str(row["occupation"])

            observations.append(
                Observation(
                    code_indicateur=indicator_id,
                    code_pays=str(row.get("country", "UNKNOWN")),
                    periode=str(row.get("period", "")),
                    valeur=float(row["value"]),
                    sexe=sexe_enum,
                    code_classification=code_classif,
                    source="ILOSTAT_RPLUMBER"
                )
            )

        return observations

    @staticmethod
    def _normalize_name(name: object) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")