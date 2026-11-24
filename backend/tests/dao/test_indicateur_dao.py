"""Tests de l'IndicateurDao avec une connexion mockée (aucune base réelle)."""

from business_object.indicateur import Indicateur
from dao.indicateur_dao import IndicateurDao


def _ligne(code="EMP_TEMP_SEX_OCU_NB", actif=True):
    return {
        "code_indicateur": code,
        "description": "Emploi par sexe et profession",
        "unite": "Milliers",
        "source": "ILOSTAT",
        "actif": actif,
    }


def test_lister_renvoie_des_indicateurs(curseur):
    """lister() mappe les lignes de la base en objets Indicateur."""
    curseur.fetchall.return_value = [_ligne("EMP_TEMP_SEX_OCU_NB"), _ligne("POP_XWAP_SEX_AGE_NB")]

    liste = IndicateurDao().lister()

    assert len(liste) == 2
    assert all(isinstance(i, Indicateur) for i in liste)
    assert liste[0].code_indicateur == "EMP_TEMP_SEX_OCU_NB"


def test_lister_sans_resultat(curseur):
    """lister() renvoie une liste vide si la base ne renvoie rien."""
    curseur.fetchall.return_value = []
    assert IndicateurDao().lister() == []


def test_trouver_par_code_existant(curseur):
    """trouver_par_code() renvoie l'indicateur correspondant."""
    curseur.fetchone.return_value = _ligne("EMP_TEMP_SEX_OCU_NB")

    indicateur = IndicateurDao().trouver_par_code("EMP_TEMP_SEX_OCU_NB")

    assert indicateur is not None
    assert indicateur.code_indicateur == "EMP_TEMP_SEX_OCU_NB"
    assert indicateur.source == "ILOSTAT"
    assert indicateur.actif is True


def test_trouver_par_code_inexistant(curseur):
    """trouver_par_code() renvoie None si l'indicateur n'existe pas."""
    curseur.fetchone.return_value = None
    assert IndicateurDao().trouver_par_code("CODE_BIDON") is None


def test_creer_renvoie_l_indicateur_insere(curseur, connexion):
    """creer() renvoie l'objet inséré et valide la transaction (commit)."""
    curseur.fetchone.return_value = _ligne("TEST_IND", actif=False)

    cree = IndicateurDao().creer(
        Indicateur(
            code_indicateur="TEST_IND",
            description="Indicateur de test",
            unite="Pourcentage",
            source="TEST",
            actif=False,
        )
    )

    assert cree.code_indicateur == "TEST_IND"
    assert cree.actif is False
    connexion.commit.assert_called()
