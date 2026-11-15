"""Tests du ReferentielService, isolés de la base via de faux DAO."""

import pytest

from business_object.classification import Classification
from business_object.enums import TypeClassification
from business_object.indicateur import Indicateur
from business_object.pays import Pays
from service.referentiel_service import ReferentielService
from utils.exceptions import DonneesInvalides, RessourceIntrouvable


class FauxIndicateurDao:
    def __init__(self, indicateurs=None, par_code=None):
        self._indicateurs = indicateurs or []
        self._par_code = par_code or {}

    def lister(self):
        return self._indicateurs

    def trouver_par_code(self, code):
        return self._par_code.get(code)


class FauxPaysDao:
    def __init__(self, pays=None, par_code=None):
        self._pays = pays or []
        self._par_code = par_code or {}

    def lister(self):
        return self._pays

    def trouver_par_code(self, code):
        return self._par_code.get(code)


class FauxClassificationDao:
    def __init__(self, classifications=None, par_code=None):
        self._classifications = classifications or []
        self._par_code = par_code or {}
        self.dernier_type = "non_appele"

    def lister(self, type_classification=None):
        self.dernier_type = type_classification
        return self._classifications

    def trouver_par_code(self, code):
        return self._par_code.get(code)


# ---------------------------------------------------------------------------
# lister_indicateurs
# ---------------------------------------------------------------------------


def test_lister_indicateurs_exclut_les_inactifs_par_defaut():
    actif = Indicateur(code_indicateur="A", actif=True)
    inactif = Indicateur(code_indicateur="B", actif=False)
    service = ReferentielService(indicateur_dao=FauxIndicateurDao([actif, inactif]))

    resultat = service.lister_indicateurs()

    assert resultat == [actif]


def test_lister_indicateurs_inclut_les_inactifs_si_demande():
    actif = Indicateur(code_indicateur="A", actif=True)
    inactif = Indicateur(code_indicateur="B", actif=False)
    service = ReferentielService(indicateur_dao=FauxIndicateurDao([actif, inactif]))

    resultat = service.lister_indicateurs(inclure_inactifs=True)

    assert resultat == [actif, inactif]


# ---------------------------------------------------------------------------
# lister_pays
# ---------------------------------------------------------------------------


def test_lister_pays_renvoie_tout():
    pays = [Pays(code_pays="FRA", nom_pays="France")]
    service = ReferentielService(pays_dao=FauxPaysDao(pays))

    assert service.lister_pays() == pays


# ---------------------------------------------------------------------------
# lister_classifications
# ---------------------------------------------------------------------------


def test_lister_classifications_sans_filtre():
    classifs = [Classification(code="X", libelle="X", type=TypeClassification.AGE)]
    faux = FauxClassificationDao(classifs)
    service = ReferentielService(classification_dao=faux)

    resultat = service.lister_classifications()

    assert resultat == classifs
    assert faux.dernier_type is None


def test_lister_classifications_filtre_converti_en_enum():
    faux = FauxClassificationDao([])
    service = ReferentielService(classification_dao=faux)

    service.lister_classifications("age")

    assert faux.dernier_type == TypeClassification.AGE


def test_lister_classifications_type_inconnu_leve_donnees_invalides():
    service = ReferentielService(classification_dao=FauxClassificationDao([]))

    with pytest.raises(DonneesInvalides):
        service.lister_classifications("inexistant")


# ---------------------------------------------------------------------------
# trouver_indicateur / trouver_pays / trouver_classification
# ---------------------------------------------------------------------------


def test_trouver_indicateur_succes():
    ind = Indicateur(code_indicateur="EMP")
    service = ReferentielService(indicateur_dao=FauxIndicateurDao(par_code={"EMP": ind}))

    assert service.trouver_indicateur("EMP") is ind


def test_trouver_indicateur_inconnu_leve_ressource_introuvable():
    service = ReferentielService(indicateur_dao=FauxIndicateurDao(par_code={}))

    with pytest.raises(RessourceIntrouvable):
        service.trouver_indicateur("ZZZ")


@pytest.mark.parametrize("code_vide", [None, "", "   "])
def test_trouver_indicateur_code_vide_leve_donnees_invalides(code_vide):
    service = ReferentielService(indicateur_dao=FauxIndicateurDao())

    with pytest.raises(DonneesInvalides):
        service.trouver_indicateur(code_vide)


def test_trouver_pays_succes():
    pays = Pays(code_pays="FRA", nom_pays="France")
    service = ReferentielService(pays_dao=FauxPaysDao(par_code={"FRA": pays}))

    assert service.trouver_pays("FRA") is pays


def test_trouver_pays_inconnu_leve_ressource_introuvable():
    service = ReferentielService(pays_dao=FauxPaysDao(par_code={}))

    with pytest.raises(RessourceIntrouvable):
        service.trouver_pays("XXX")


def test_trouver_classification_succes():
    classif = Classification(code="C1", libelle="Jeunes", type=TypeClassification.AGE)
    service = ReferentielService(classification_dao=FauxClassificationDao(par_code={"C1": classif}))

    assert service.trouver_classification("C1") is classif


def test_trouver_classification_inconnue_leve_ressource_introuvable():
    service = ReferentielService(classification_dao=FauxClassificationDao(par_code={}))

    with pytest.raises(RessourceIntrouvable):
        service.trouver_classification("C9")
