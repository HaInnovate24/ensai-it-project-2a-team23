"""Tests des outils de gestion des périodes."""

import pytest

from utils.periodes import convertir_periode, fenetre_de_periodes, formater_periode

# convertir_periode et formater_periode


@pytest.mark.parametrize(
    ("periode", "attendu"),
    [
        ("2014", ("annee", 2014)),
        ("2014Q1", ("trimestre", 2014 * 4)),
        ("2014Q4", ("trimestre", 2014 * 4 + 3)),
        ("2014M01", ("mois", 2014 * 12)),
        ("2014M12", ("mois", 2014 * 12 + 11)),
        ("2014M7", ("mois", 2014 * 12 + 6)),
        (" 2014Q2 ", ("trimestre", 2014 * 4 + 1)),
    ],
)
def test_convertir_periode_valide(periode, attendu):
    """Les formats année, trimestre et mois sont reconnus."""
    assert convertir_periode(periode) == attendu


@pytest.mark.parametrize(
    "periode_invalide",
    ["", "14", "2014Q5", "2014Q0", "2014M13", "2014M00", "T1-2014", "2014-Q1", "abcd", None, 2014],
)
def test_convertir_periode_invalide(periode_invalide):
    """Un format inconnu (ou une valeur qui n'est pas du texte) donne None."""
    assert convertir_periode(periode_invalide) is None


@pytest.mark.parametrize("periode", ["2014", "2014Q1", "2014Q4", "2014M01", "2014M12"])
def test_formater_est_l_inverse_de_convertir(periode):
    """Convertir puis formater redonne la période d'origine."""
    frequence, numero = convertir_periode(periode)

    assert formater_periode(frequence, numero) == periode


def test_trimestres_consecutifs_a_la_frontiere_d_une_annee():
    """2023Q4 et 2024Q1 sont consécutifs : leurs numéros diffèrent de 1."""
    assert convertir_periode("2024Q1")[1] - convertir_periode("2023Q4")[1] == 1


# fenetre_de_periodes


def test_fenetre_liste_vide():
    """Sans période, il n'y a rien à garder ni à signaler."""
    assert fenetre_de_periodes([], 3) == ([], [])


def test_fenetre_sans_nb_periodes_garde_tout_sans_trou():
    """Sans limite et sans trou, toutes les périodes sont gardées."""
    gardees, manquantes = fenetre_de_periodes(["2024Q1", "2024Q2", "2024Q3"])

    assert gardees == ["2024Q1", "2024Q2", "2024Q3"]
    assert manquantes == []


def test_fenetre_sans_nb_periodes_signale_les_trous():
    """Sans limite, les trous entre la première et la dernière période sont signalés."""
    gardees, manquantes = fenetre_de_periodes(["2023Q1", "2023Q2", "2023Q4", "2024Q1"])

    assert gardees == ["2023Q1", "2023Q2", "2023Q4", "2024Q1"]
    assert manquantes == ["2023Q3"]


def test_fenetre_calendaire_avec_une_periode_manquante():
    """Les 3 derniers trimestres sont 2023Q3, Q4 et 2024Q1 : 2023Q3 est manquant."""
    gardees, manquantes = fenetre_de_periodes(["2023Q1", "2023Q2", "2023Q4", "2024Q1"], 3)

    assert gardees == ["2023Q4", "2024Q1"]
    assert manquantes == ["2023Q3"]


def test_fenetre_plus_grande_que_les_donnees():
    """Quand il y a moins de données que demandé, les périodes avant le début sont manquantes."""
    gardees, manquantes = fenetre_de_periodes(["2024Q1", "2024Q2"], 4)

    assert gardees == ["2024Q1", "2024Q2"]
    assert manquantes == ["2023Q3", "2023Q4"]


def test_fenetre_ordre_chronologique_meme_si_l_entree_est_desordonnee():
    """Les périodes gardées sont renvoyées dans l'ordre chronologique."""
    gardees, _ = fenetre_de_periodes(["2024Q2", "2023Q4", "2024Q1"])

    assert gardees == ["2023Q4", "2024Q1", "2024Q2"]


def test_fenetre_annees():
    """Avec des années, une année absente est signalée."""
    gardees, manquantes = fenetre_de_periodes(["2012", "2014", "2015"])

    assert gardees == ["2012", "2014", "2015"]
    assert manquantes == ["2013"]


def test_fenetre_mois_ordre_numerique_et_non_alphabetique():
    """2024M2 vient avant 2024M10 (l'ordre alphabétique les inverserait)."""
    gardees, manquantes = fenetre_de_periodes(["2024M10", "2024M2"])

    assert gardees == ["2024M2", "2024M10"]
    assert manquantes == [
        "2024M03",
        "2024M04",
        "2024M05",
        "2024M06",
        "2024M07",
        "2024M08",
        "2024M09",
    ]


def test_fenetre_format_inconnu_garde_les_n_dernieres_observations():
    """Format inconnu : on garde les N dernières périodes et on ne signale rien."""
    gardees, manquantes = fenetre_de_periodes(["T1-2024", "T2-2024", "T3-2024"], 2)

    assert gardees == ["T2-2024", "T3-2024"]
    assert manquantes == []


def test_fenetre_frequences_melangees():
    """Années et trimestres mélangés : on ne raisonne pas sur le calendrier."""
    gardees, manquantes = fenetre_de_periodes(["2023", "2024Q1", "2024Q2"], 2)

    assert gardees == ["2024Q1", "2024Q2"]
    assert manquantes == []
