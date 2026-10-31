
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