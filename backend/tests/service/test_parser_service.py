import math
import pytest
import pandas as pd

from business_object.enums import Sexe
from service.parser_service import ParserService


@pytest.fixture
def parser():
    return ParserService()


def test_parser_dataframe_vide(parser):
    df = pd.DataFrame()
    assert parser.parser(df, "IND_TEST") == []


def test_parser_colonnes_manquantes_leve_erreur(parser):
    df = pd.DataFrame({"ref_area": ["FRA"]})  # Manque time et obs_value
    with pytest.raises(ValueError, match="Colonnes de code/période/valeur manquantes"):
        parser.parser(df, "IND_TEST")


def test_parser_succes_nominal(parser):
    df = pd.DataFrame({
        "ref_area": [" fra ", "DEU"],
        "sex": ["SEX_M", "SEX_F"],
        "time": [" 2020 ", "2021"],
        "obs_value": ["10.5", 20],
        "classif1": ["AGE_15_24", None]
    })
    
    observations = parser.parser(df, "EMP_AGE")
    
    assert len(observations) == 2
    
    # Première observation (Homme, avec classification)
    assert observations[0].code_indicateur == "EMP_AGE"
    assert observations[0].code_pays == "FRA"
    assert observations[0].periode == "2020"
    assert observations[0].valeur == 10.5
    assert observations[0].sexe == Sexe.HOMME
    assert observations[0].code_classification == "AGE_15_24"
    assert observations[0].source == "ILOSTAT_RPLUMBER"

    # Deuxième observation (Femme, sans classification, valeur numérique directe)
    assert observations[1].code_pays == "DEU"
    assert observations[1].sexe == Sexe.FEMME
    assert observations[1].valeur == 20.0
    assert observations[1].code_classification is None


def test_parser_ignore_lignes_invalides_ou_non_numeriques(parser):
    df = pd.DataFrame({
        "country": ["FRA", "ESP", "ITA", "GBR"],
        "period": ["2020", "2020", "2020", "2020"],
        "value": ["12.5", "not_a_number", float('nan'), float('inf')],
        "sex": ["SEX_T", "SEX_T", "SEX_T", "SEX_T"]
    })
    
    observations = parser.parser(df, "IND")
    # Seule la première ligne ("12.5") est valide
    assert len(observations) == 1
    assert observations[0].valeur == 12.5


def test_parser_ignore_sexe_inconnu(parser):
    df = pd.DataFrame({
        "country": ["FRA", "DEU"],
        "period": ["2020", "2020"],
        "value": [10.0, 10.0],
        "sex": ["SEX_T", "SEX_INCONNU"]
    })
    
    observations = parser.parser(df, "IND")
    # La ligne avec "SEX_INCONNU" doit être ignorée silencieusement
    assert len(observations) == 1
    assert observations[0].code_pays == "FRA"


@pytest.mark.parametrize("input_sex,expected", [
    ("m", Sexe.HOMME),
    ("male", Sexe.HOMME),
    ("homme", Sexe.HOMME),
    ("f", Sexe.FEMME),
    ("female", Sexe.FEMME),
    ("femme", Sexe.FEMME),
    ("t", Sexe.TOTAL),
    ("total", Sexe.TOTAL),
    ("both_sexes", Sexe.TOTAL),
])
def test_parse_sex_variantes(parser, input_sex, expected):
    df = pd.DataFrame({
        "country": ["FRA"],
        "period": ["2020"],
        "value": [1.0],
        "sex": [input_sex]
    })
    observations = parser.parser(df, "IND")
    assert len(observations) == 1
    assert observations[0].sexe == expected


def test_normalize_classification_alias(parser):
    # Test des alias spécifiques liés aux indicateurs d'âge
    df = pd.DataFrame({
        "country": ["FRA", "FRA", "FRA"],
        "period": ["2020", "2020", "2020"],
        "value": [1.0, 1.0, 1.0],
        "classif1": ["AGE_AGGREGATE_YGE15", "AGE_AGGREGATE_YGE25", "AUTRE_CODE"]
    })
    
    # Indicateur contenant _AGE_ pour déclencher la règle de normalisation
    observations = parser.parser(df, "EMP_SEX_AGE_NB")
    
    assert observations[0].code_classification == "AGE_AGGREGATE_TOTAL"
    assert observations[1].code_classification == "AGE_AGGREGATE_Y25-PLUS"
    assert observations[2].code_classification == "AUTRE_CODE"


def test_classification_column_alternatives(parser):
    # Test avec la colonne "age_group" au lieu de classif1
    df = pd.DataFrame({
        "country": ["FRA"],
        "period": ["2020"],
        "value": [1.0],
        "age_group": ["Y15-24"]
    })
    
    observations = parser.parser(df, "IND")
    assert observations[0].code_classification == "Y15-24"