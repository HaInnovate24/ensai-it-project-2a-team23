"""Transformation des données ILOSTAT en observations métier."""

import math
import re
from collections.abc import Mapping

import pandas as pd

from business_object.enums import Sexe
from business_object.observation import Observation


class ParserService:
    """Convertit les colonnes d'un CSV ILOSTAT en objets ``Observation``."""

    # L'ordre est volontaire : les codes doivent toujours primer sur les libellés.
    ALIASES = {
        "country": ("ref_area", "country_code", "geo_code", "country", "geo"),
        "sex": ("sex", "sex_code", "gender"),
        "period": ("time", "time_period", "period"),
        "value": ("obs_value", "observation_value", "value"),
    }
    CLASSIFICATION_COLUMNS = re.compile(r"^classif\d+$")

    def parser(self, data: pd.DataFrame, indicator_id: str) -> list[Observation]:
        """Parse les observations valides et ignore les lignes incomplètes ou non numériques."""
        if data.empty:
            return []

        # Les noms ILOSTAT peuvent être par exemple ``ref_area.label`` ou
        # ``classif1.label``. On conserve leur forme normalisée pour distinguer
        # les colonnes de code des colonnes de libellé.
        columns = {self._normalize_name(column): column for column in data.columns}
        rename: dict[object, str] = {}
        for field, aliases in self.ALIASES.items():
            source = next((columns[name] for name in aliases if name in columns), None)
            if source is not None:
                rename[source] = field

        parsed = data.rename(columns=rename).copy()
        required = ("country", "period", "value")
        missing = [field for field in required if field not in parsed.columns]
        if missing:
            raise ValueError(
                "Colonnes de code/période/valeur manquantes dans le CSV ILOSTAT : "
                + ", ".join(missing)
            )

        # Ne jamais utiliser ref_area.label comme clé étrangère pays : la base
        # attend le code ILOSTAT (FRA, DEU, ...).
        parsed["country"] = parsed["country"].astype("string").str.strip().str.upper()
        parsed["period"] = parsed["period"].astype("string").str.strip()
        parsed["value"] = pd.to_numeric(parsed["value"], errors="coerce")
        parsed = parsed.dropna(subset=["country", "period", "value"])
        parsed = parsed[(parsed["country"] != "") & (parsed["period"] != "")]

        classification_column = self._classification_column(data.columns, columns)
        sex_column = "sex" if "sex" in parsed.columns else None

        observations: list[Observation] = []
        for _, row in parsed.iterrows():
            value = float(row["value"])
            if not math.isfinite(value):
                continue

            sex = self._parse_sex(row[sex_column]) if sex_column else Sexe.TOTAL
            classification = None
            if classification_column is not None:
                raw_classification = row[classification_column]
                if pd.notna(raw_classification):
                    classification = self._normalize_classification(
                        str(raw_classification), indicator_id
                    )

            observations.append(
                Observation(
                    code_indicateur=indicator_id,
                    code_pays=str(row["country"]),
                    periode=str(row["period"]),
                    valeur=value,
                    sexe=sex,
                    code_classification=classification,
                    source="ILOSTAT_RPLUMBER",
                )
            )

        return observations

    @classmethod
    def _classification_column(
        cls, original_columns: pd.Index, normalized_columns: Mapping[str, object]
    ) -> str | None:
        """Retourne une colonne de code de classification, jamais son libellé."""
        for name in normalized_columns:
            if cls.CLASSIFICATION_COLUMNS.fullmatch(name):
                return str(normalized_columns[name])

        # Alias utiles pour les DataFrames déjà transformés ou fournis par un
        # autre client ; les colonnes *_label restent volontairement exclues.
        for name in ("age_group", "occupation", "classif"):
            if name in normalized_columns:
                return str(normalized_columns[name])

        for column in original_columns:
            name = cls._normalize_name(column)
            if name in {"age", "age_group", "occupation"}:
                return str(column)
        return None

    @staticmethod
    def _parse_sex(value: object) -> Sexe:
        """Reconnaît les codes et libellés ILOSTAT sans confondre Female et Male."""
        normalized = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
        if normalized in {"m", "sex_m", "male", "man", "men", "homme", "hommes"}:
            return Sexe.HOMME
        if normalized in {"f", "sex_f", "female", "woman", "women", "femme", "femmes"}:
            return Sexe.FEMME
        if normalized in {
            "t", "sex_t", "total", "both_sexes", "both_sex", "all_sexes", "ensemble"
        }:
            return Sexe.TOTAL
        raise ValueError(f"Valeur de sexe ILOSTAT non reconnue : {value!r}")

    @staticmethod
    def _normalize_classification(value: str, indicator_id: str) -> str:
        """Normalise certains agrégats ILOSTAT vers les clés du référentiel local."""
        code = value.strip().upper()
        if "_AGE_" in indicator_id.upper() or indicator_id.upper().endswith("_AGE_NB"):
            aliases = {
                "AGE_AGGREGATE_YGE15": "AGE_AGGREGATE_TOTAL",
                "AGE_AGGREGATE_YGE25": "AGE_AGGREGATE_Y25-PLUS",
                "AGE_AGGREGATE_Y25-PLUS": "AGE_AGGREGATE_Y25-plus",
            }
            return aliases.get(code, code)
        return code

    @staticmethod
    def _normalize_name(name: object) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")

import sys
sys.path.insert(0, "backend/src")

import pandas as pd
from service.parser_service import ParserService

data = pd.DataFrame([
    {"ref_area": "FRA", "sex": "SEX_T", "time": "2020", "obs_value": "12.5"},
    {"ref_area": "DEU", "sex": "SEX_M", "time": "2020", "obs_value": "invalide"},
])

observations = ParserService().parser(data, "TEST_INDICATOR")

assert len(observations) == 1
assert observations[0].code_pays == "FRA"
assert observations[0].periode == "2020"
assert observations[0].valeur == 12.5

print("Test réussi")