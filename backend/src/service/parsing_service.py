import re

import pandas as pd


class ParsingService:
    """Normalize common fields in an ILOSTAT indicator DataFrame."""

    ALIASES = {
        "country": {"ref_area", "ref_area_label", "country", "country_name", "geo"},
        "sex": {"sex", "sex_label"},
        "period": {"time", "time_period", "period", "time_label"},
        "value": {"obs_value", "observation_value", "value"},
    }

    def parse_indicator_data(self, data: pd.DataFrame, indicator_id: str) -> list[dict]:
        if data.empty:
            return []
        columns = {self._normalize_name(col): col for col in data.columns}
        rename = {}
        for field, aliases in self.ALIASES.items():
            source = next((columns[name] for name in aliases if name in columns), None)
            if source is not None:
                rename[source] = field
        parsed = data.rename(columns=rename).copy()
        parsed["indicator_id"] = indicator_id

        # Classification columns vary by indicator; preserve the raw columns
        # and expose age/occupation when column names make them identifiable.
        for column in data.columns:
            name = self._normalize_name(column)
            if "age" in name and "age_group" not in parsed:
                parsed["age_group"] = data[column]
            elif any(term in name for term in ("occupation", "oc2", "isco")):
                if "occupation" not in parsed:
                    parsed["occupation"] = data[column]

        for field in ("country", "sex", "age_group", "occupation", "period", "value"):
            if field not in parsed:
                parsed[field] = None
        common = ["indicator_id", "country", "sex", "age_group", "occupation", "period", "value"]
        parsed = parsed[common + [col for col in parsed.columns if col not in common]]
        records = parsed.astype(object).where(pd.notna(parsed), None).to_dict(orient="records")
        return [
            {key: value.item() if hasattr(value, "item") else value for key, value in row.items()}
            for row in records
        ]

    @staticmethod
    def _normalize_name(name: object) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
