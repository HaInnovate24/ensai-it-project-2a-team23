"""Tests du module de journalisation (loggers, indentation, décorateur log)."""

import logging

import pytest

from utils import journalisation
from utils.journalisation import LogIndentation, get_logger, log


# --- Fixtures ---


@pytest.fixture(autouse=True)
def reset_indentation():
    """Réinitialise l'indentation avant chaque test."""
    LogIndentation.current_indentation = 0
    yield
    LogIndentation.current_indentation = 0


# --- get_logger ---


def test_get_logger_nom_court():
    """Un nom de module court (<= max_size) est utilisé tel quel."""
    logger = get_logger("dao.pays_dao")

    assert logger.name == "dao.pays_dao"


def test_get_logger_nom_long():
    """Un nom de module long (> max_size) est raccourci avec des initiales."""
    # "backend.src.service.collecte_service" a 36 caractères > 25
    logger = get_logger("backend.src.service.collecte_service")

    # initiales: b.s.s + dernier segment
    assert logger.name == "b.s.s.collecte_service"


def test_get_logger_exactement_max_size():
    """Un nom de longueur exactement max_size n'est pas raccourci."""
    nom = "a" * 25  # longueur exacte de max_size par défaut
    logger = get_logger(nom)

    assert logger.name == nom


def test_get_logger_max_size_personnalise():
    """Un max_size personnalisé modifie le comportement du raccourcissement."""
    # "ab.cd.ef" a 8 caractères, avec max_size=5 il doit être raccourci
    logger = get_logger("ab.cd.ef", max_size=5)

    assert logger.name == "a.c.ef"


# --- LogIndentation ---


def test_indentation_initiale():
    """L'indentation démarre à zéro."""
    assert LogIndentation.get_indentation() == ""


def test_increase_indentation():
    """Chaque appel à increase ajoute indentation_size espaces."""
    LogIndentation.increase_indentation()

    assert LogIndentation.get_indentation() == " " * LogIndentation.indentation_size


def test_multiple_increase_indentation():
    """Plusieurs increases s'additionnent."""
    LogIndentation.increase_indentation()
    LogIndentation.increase_indentation()
    LogIndentation.increase_indentation()

    assert LogIndentation.get_indentation() == " " * LogIndentation.indentation_size * 3


def test_decrease_indentation():
    """Decrease annule un increase."""
    LogIndentation.increase_indentation()
    LogIndentation.decrease_indentation()

    assert LogIndentation.get_indentation() == ""


def test_decrease_sous_zero():
    """Un decrease sans increase précédent ne lève pas d'erreur."""
    LogIndentation.decrease_indentation()

    # current_indentation devient -1, get_indentation retourne une chaîne vide ou négative
    # (on vérifie simplement qu'il n'y a pas d'exception)
    LogIndentation.get_indentation()


# --- Décorateur @log ---


def test_log_renvoie_le_resultat(caplog):
    """Le décorateur @log renvoie le résultat de la fonction décorée."""

    class MaClasse:
        def ma_methode(self, x, y):
            return x + y

    MaClasse.ma_methode = log(MaClasse.ma_methode)

    obj = MaClasse()
    assert obj.ma_methode(3, 4) == 7


def test_log_masque_mots_de_passe_sensibles(caplog):
    """Les paramètres contenant des mots-clés sensibles sont masqués dans le log."""

    class MaClasse:
        def connecter(self, password, host):
            return "ok"

    MaClasse.connecter = log(MaClasse.connecter)

    with caplog.at_level(logging.INFO):
        obj = MaClasse()
        obj.connecter("motdepasse123", "localhost")

    log_entry = caplog.text
    assert "*****" in log_entry
    assert "motdepasse123" not in log_entry


def test_log_masque_kwargs_sensibles(caplog):
    """Les kwargs sensibles sont aussi masqués."""

    class MaClasse:
        def appel(self, token):
            return "ok"

    MaClasse.appel = log(MaClasse.appel)

    with caplog.at_level(logging.INFO):
        obj = MaClasse()
        obj.appel(token="abc123secret")

    log_entry = caplog.text
    assert "*****" in log_entry
    assert "abc123secret" not in log_entry


def test_log_parametres_normaux_visibles(caplog):
    """Les paramètres non sensibles sont visibles dans le log."""

    class MaClasse:
        def chercher(self, code, limite):
            return code

    MaClasse.chercher = log(MaClasse.chercher)

    with caplog.at_level(logging.INFO):
        obj = MaClasse()
        obj.chercher("AGE", 10)

    log_entry = caplog.text
    assert "AGE" in log_entry
    assert "10" in log_entry


def test_log_boucle_resultat_liste(caplog):
    """Un résultat liste est tronqué (max 3 éléments affichés)."""

    class MaClasse:
        def lister(self):
            return ["a", "b", "c", "d", "e"]

    MaClasse.lister = log(MaClasse.lister)

    with caplog.at_level(logging.INFO):
        obj = MaClasse()
        obj.lister()

    log_entry = caplog.text
    assert "(5 elements)" in log_entry


def test_log_tronque_resultat_chaine_longue(caplog):
    """Une chaîne de résultat > 50 caractères est tronquée dans le log."""

    class MaClasse:
        def texte(self):
            return "x" * 100

    MaClasse.texte = log(MaClasse.texte)

    with caplog.at_level(logging.INFO):
        obj = MaClasse()
        obj.texte()

    log_entry = caplog.text
    assert "(100 characters)" in log_entry


def test_log_indentation_incremente(caplog):
    """Le décorateur incrémente puis décrémente l'indentation."""

    class MaClasse:
        def methode(self):
            return 1

    MaClasse.methode = log(MaClasse.methode)

    with caplog.at_level(logging.INFO):
        obj = MaClasse()
        obj.methode()

    # Après le décorateur, l'indentation doit être revenue à 0
    assert LogIndentation.current_indentation == 0


def test_log_fonction_sans_self():
    """Le décorateur fonctionne aussi sur une fonction simple (sans self)."""

    def simple(a, b):
        return a * b

    simple_loguee = log(simple)

    assert simple_loguee(3, 7) == 21