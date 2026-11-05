"""Tests du module de configuration (variables d'environnement, masquage)."""

import logging
from unittest.mock import patch

import pytest

from utils import config


# --- mask_value ---


@pytest.mark.parametrize(
    "cle,valeur_attendue",
    [
        ("POSTGRES_PASSWORD", "*******"),
        ("JWT_SECRET_KEY", "*******"),
        ("API_TOKEN", "*******"),
        ("SECRET", "*******"),
    ],
)
def test_mask_value_cles_sensibles(cle, valeur_attendue):
    """Les valeurs des clés sensibles sont masquées."""
    assert config.mask_value(cle, "valeur-secrete") == valeur_attendue


@pytest.mark.parametrize(
    "cle,valeur",
    [
        ("POSTGRES_HOST", "localhost"),
        ("POSTGRES_PORT", "5432"),
        ("POSTGRES_DATABASE", "defaultdb"),
        ("APP_NAME", "LaborScope"),
    ],
)
def test_mask_value_cles_non_sensibles(cle, valeur):
    """Les valeurs des clés non sensibles sont renvoyées telles quelles."""
    assert config.mask_value(cle, valeur) == valeur


def test_mask_value_independant_de_la_casse_de_la_cle():
    """Le masquage fonctionne même si la clé contient des minuscules."""
    assert config.mask_value("postgres_password", "abc") == "*******"


def test_mask_value_valeur_vide():
    """Une valeur vide reste vide si la clé n'est pas sensible."""
    assert config.mask_value("HOST", "") == ""


# --- display_values ---


@patch("utils.config.dotenv.dotenv_values")
def test_display_values_masque_les_mots_de_passe(mock_dotenv_values, caplog):
    """display_values masque les valeurs sensibles dans les logs."""
    mock_dotenv_values.return_value = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PASSWORD": "supersecret",
    }

    with caplog.at_level(logging.INFO):
        config.display_values()

    assert "POSTGRES_HOST=localhost" in caplog.text
    assert "POSTGRES_PASSWORD=*******" in caplog.text
    assert "supersecret" not in caplog.text


@patch("utils.config.dotenv.dotenv_values")
def test_display_values_include_prefix(mock_dotenv_values, caplog):
    """include_prefix filtre pour n'afficher que les clés correspondantes."""
    mock_dotenv_values.return_value = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "APP_NAME": "LaborScope",
    }

    with caplog.at_level(logging.INFO):
        config.display_values(include_prefix="POSTGRES_")

    assert "POSTGRES_HOST" in caplog.text
    assert "POSTGRES_PORT" in caplog.text
    assert "APP_NAME" not in caplog.text


@patch("utils.config.dotenv.dotenv_values")
def test_display_values_exclude_prefix(mock_dotenv_values, caplog):
    """exclude_prefix exclut les clés commençant par le préfixe donné."""
    mock_dotenv_values.return_value = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "APP_NAME": "LaborScope",
    }

    with caplog.at_level(logging.INFO):
        config.display_values(exclude_prefix="POSTGRES_")

    assert "POSTGRES_HOST" not in caplog.text
    assert "POSTGRES_PORT" not in caplog.text
    assert "APP_NAME" in caplog.text


@patch("utils.config.dotenv.dotenv_values")
def test_display_values_include_et_exclude(mock_dotenv_values, caplog):
    """include_prefix et exclude_prefix sont combinés."""
    mock_dotenv_values.return_value = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "APP_NAME": "LaborScope",
    }

    with caplog.at_level(logging.INFO):
        config.display_values(include_prefix="POSTGRES_", exclude_prefix="POSTGRES_PORT")

    assert "POSTGRES_HOST" in caplog.text
    assert "POSTGRES_PORT" not in caplog.text
    assert "APP_NAME" not in caplog.text


# --- load_environment_variables ---


@patch("utils.config.dotenv.load_dotenv")
def test_load_environment_variables_succes(mock_load_dotenv, caplog):
    """load_environment_variables loggue un message de succès."""
    mock_load_dotenv.return_value = True

    with caplog.at_level(logging.INFO):
        config.load_environment_variables()

    assert "SUCCES" in caplog.text


@patch("utils.config.dotenv.load_dotenv")
def test_load_environment_variables_echec(mock_load_dotenv, caplog):
    """load_environment_variables loggue un message d'échec."""
    mock_load_dotenv.return_value = False

    with caplog.at_level(logging.INFO):
        config.load_environment_variables()

    assert "FAIL" in caplog.text