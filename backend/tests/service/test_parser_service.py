"""Tests du ParserService : conversion CSV ILOSTAT -> observations."""

import pandas as pd
import pytest

from business_object.enums import Sexe
from service.parser_service import ParserService


@pytest.fixture
def parser():
    return ParserService()


# ---------------------------------------------------------------------------
# parser : cas nominal et lignes ignorées
# ---------------------------------------------------------------------------


def test_parser_cas_nominal_ignore_les_valeurs_non_numeriques(parser):
    data = pd.DataFrame(
        [
            {"ref_area": "FRA", "sex": "SEX_T", "time": "2020", "obs_value": "12.5"},
            {"ref_area": "DEU", "sex": "SEX_M", "time": "2020", "obs_value": "invalide"},
        ]
    )

    observations = parser.parser(data, "TEST_INDICATOR")

    assert len(observations) == 1
    assert observations[0].code_pays == "FRA"
    assert observations[0].periode == "2020"
    assert observations[0].valeur == 12.5
    assert observations[0].sexe == Sexe.TOTAL


def test_parser_dataframe_vide_renvoie_liste_vide(parser):
    assert parser.parser(pd.DataFrame(), "IND") == []


def test_parser_colonnes_obligatoires_manquantes_leve_value_error(parser):
    data = pd.DataFrame([{"sex": "SEX_T"}])

    with pytest.raises(ValueError, match="manquantes"):
        parser.parser(data, "IND")


def test_parser_ignore_les_valeurs_non_finies(parser):
    data = pd.DataFrame(
        [
            {"ref_area": "FRA", "sex": "SEX_T", "time": "2020", "obs_value": "inf"},
            {"ref_area": "FRA", "sex": "SEX_T", "time": "2021", "obs_value": "10"},
        ]
    )

    observations = parser.parser(data, "IND")

    assert [o.periode for o in observations] == ["2021"]


def test_parser_ignore_les_sexes_non_reconnus(parser):
    data = pd.DataFrame(
        [
            {"ref_area": "FRA", "sex": "ALIEN", "time": "2020", "obs_value": "10"},
            {"ref_area": "FRA", "sex": "SEX_F", "time": "2021", "obs_value": "20"},
        ]
    )

    observations = parser.parser(data, "IND")

    assert len(observations) == 1
    assert observations[0].sexe == Sexe.FEMME


def test_parser_sans_colonne_sexe_utilise_total(parser):
    data = pd.DataFrame([{"ref_area": "FRA", "time": "2020", "obs_value": "10"}])

    observations = parser.parser(data, "IND")

    assert observations[0].sexe == Sexe.TOTAL


# ---------------------------------------------------------------------------
# Détection de la colonne de classification
# ---------------------------------------------------------------------------


def test_parser_detecte_classif_numerotee(parser):
    data = pd.DataFrame(
        [{"ref_area": "FRA", "time": "2020", "obs_value": "10", "classif1": "OCU_X"}]
    )

    observations = parser.parser(data, "IND")

    assert observations[0].code_classification == "OCU_X"


def test_parser_detecte_colonne_occupation(parser):
    data = pd.DataFrame(
        [{"ref_area": "FRA", "time": "2020", "obs_value": "10", "occupation": "OCU_Y"}]
    )

    observations = parser.parser(data, "IND")

    assert observations[0].code_classification == "OCU_Y"


def test_parser_detecte_colonne_age_originale(parser):
    data = pd.DataFrame([{"ref_area": "FRA", "time": "2020", "obs_value": "10", "age": "AGE_Z"}])

    observations = parser.parser(data, "IND")

    assert observations[0].code_classification == "AGE_Z"


def test_parser_classification_absente_reste_none(parser):
    # La colonne de classification existe mais la valeur est manquante (NaN).
    data = pd.DataFrame(
        [{"ref_area": "FRA", "time": "2020", "obs_value": "10", "classif1": None}]
    )

    observations = parser.parser(data, "IND")

    assert observations[0].code_classification is None


# ---------------------------------------------------------------------------
# _parse_sex (reconnaissance des codes et libellés)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "valeur, attendu",
    [
        ("SEX_M", Sexe.HOMME),
        ("male", Sexe.HOMME),
        ("SEX_F", Sexe.FEMME),
        ("femmes", Sexe.FEMME),
        ("SEX_T", Sexe.TOTAL),
        ("both_sexes", Sexe.TOTAL),
    ],
)
def test_parse_sex_reconnait_les_variantes(valeur, attendu):
    assert ParserService._parse_sex(valeur) == attendu


def test_parse_sex_valeur_inconnue_leve_value_error():
    with pytest.raises(ValueError):
        ParserService._parse_sex("inconnu")


# ---------------------------------------------------------------------------
# _normalize_classification (agrégats d'âge)
# ---------------------------------------------------------------------------


def test_normalize_classification_age_applique_les_alias():
    code = ParserService._normalize_classification("AGE_AGGREGATE_YGE15", "EMP_AGE_NB")

    assert code == "AGE_AGGREGATE_TOTAL"


def test_normalize_classification_hors_age_renvoie_le_code_majuscule():
    code = ParserService._normalize_classification("ocu_isco08_1", "EMP_OCU_NB")

    assert code == "OCU_ISCO08_1"


def test_parser_applique_la_normalisation_age_sur_les_observations(parser):
    data = pd.DataFrame(
        [
            {
                "ref_area": "FRA",
                "time": "2020",
                "obs_value": "10",
                "classif1": "AGE_AGGREGATE_YGE15",
            }
        ]
    )

    observations = parser.parser(data, "EMP_AGE_NB")

    assert observations[0].code_classification == "AGE_AGGREGATE_TOTAL"
