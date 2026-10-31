""" from business_object.pays import Pays
from service import referentiel_service


def test_lister_pays():
    pays_attendus = [
        Pays(code_pays="FR", nom_pays="France"),
        Pays(code_pays="DE", nom_pays="Allemagne"),
    ]

    class FauxPaysDao:
        def lister(self):
            return pays_attendus

    # On remplace le vrai DAO par un faux DAO pour isoler le test.
    referentiel_service.PaysDao = FauxPaysDao

    service = referentiel_service.ReferentielService()

    resultat = service.lister_pays()

    assert resultat == pays_attendus
 """
