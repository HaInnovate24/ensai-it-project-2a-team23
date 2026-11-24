"""Tests du ClassificationDao avec une connexion mockée (aucune base réelle)."""

from business_object.classification import Classification
from business_object.enums import TypeClassification
from dao.classification_dao import ClassificationDao


def test_trouver_par_code_existant(curseur):
    """trouver_par_code() renvoie la classification correspondante."""
    curseur.fetchone.return_value = {
        "code": "AGE_AGGREGATE_TOTAL",
        "libelle": "Total",
        "type": "age",
    }

    classif = ClassificationDao().trouver_par_code("AGE_AGGREGATE_TOTAL")

    assert classif is not None
    assert classif.code == "AGE_AGGREGATE_TOTAL"
    valeur_type = classif.type.value if hasattr(classif.type, "value") else classif.type
    assert valeur_type == "age"


def test_trouver_par_code_inexistant(curseur):
    """trouver_par_code() renvoie None si le code n'existe pas."""
    curseur.fetchone.return_value = None
    assert ClassificationDao().trouver_par_code("CODE_INEXISTANT") is None


def test_lister_sans_filtre(curseur):
    """lister() mappe toutes les lignes renvoyées en objets Classification."""
    curseur.fetchall.return_value = [
        {"code": "AGE_AGGREGATE_TOTAL", "libelle": "Total", "type": "age"},
        {"code": "OCU_ISCO08_1", "libelle": "Directeurs", "type": "occupation"},
    ]

    liste = ClassificationDao().lister()

    assert len(liste) == 2
    assert isinstance(liste[0], Classification)


def test_lister_avec_filtre_type(curseur):
    """lister(type=AGE) passe la valeur du type en paramètre SQL."""
    curseur.fetchall.return_value = [
        {"code": "AGE_AGGREGATE_TOTAL", "libelle": "Total", "type": "age"},
    ]

    liste = ClassificationDao().lister(type=TypeClassification.AGE)

    assert len(liste) == 1
    # Le filtre 'age' (valeur de l'Enum) est transmis à la requête.
    _, parametres = curseur.execute.call_args[0]
    assert parametres == ("age",)


def test_creer_renvoie_la_classification_inseree(curseur, connexion):
    """creer() renvoie l'objet inséré et valide la transaction (commit)."""
    curseur.fetchone.return_value = {
        "code": "TEST_CLASS",
        "libelle": "Classification de test",
        "type": "occupation",
    }

    creee = ClassificationDao().creer(
        Classification(code="TEST_CLASS", libelle="Classification de test", type="occupation")
    )

    assert creee.code == "TEST_CLASS"
    assert creee.libelle == "Classification de test"
    connexion.commit.assert_called()
