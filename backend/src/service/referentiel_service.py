"""Listes et recherches dans les référentiels : indicateurs, pays, classifications."""

from business_object.classification import Classification
from business_object.enums import TypeClassification
from business_object.indicateur import Indicateur
from business_object.pays import Pays
from dao.classification_dao import ClassificationDao
from dao.indicateur_dao import IndicateurDao
from dao.pays_dao import PaysDao
from utils.exceptions import DonneesInvalides, RessourceIntrouvable


class ReferentielService:
    """Fournit les listes de référence utilisées pour construire les analyses.

    Connaître les indicateurs, les pays et les classifications disponibles
    avant de demander une analyse.
    """

    def __init__(
        self,
        indicateur_dao: IndicateurDao | None = None,
        pays_dao: PaysDao | None = None,
        classification_dao: ClassificationDao | None = None,
    ):
        """Initialise le service.

        Pour les tests on fournira de faux DAO pour ne pas toucher à la base.
        """
        self.indicateur_dao = indicateur_dao if indicateur_dao is not None else IndicateurDao()
        self.pays_dao = pays_dao if pays_dao is not None else PaysDao()
        self.classification_dao = (
            classification_dao if classification_dao is not None else ClassificationDao()
        )

    # Listes

    def lister_indicateurs(self, inclure_inactifs: bool = False) -> list[Indicateur]:
        """Renvoie les indicateurs du référentiel.

        Par défaut, seuls les indicateurs actifs (ceux qui sont collectés) sont
        renvoyés. Avec inclure_inactifs=True, on les renvoie tous (usage admin).
        """
        indicateurs = self.indicateur_dao.lister()
        if inclure_inactifs:
            return indicateurs
        return [indicateur for indicateur in indicateurs if indicateur.actif]

    def lister_pays(self) -> list[Pays]:
        """Renvoie tous les pays du référentiel."""
        return self.pays_dao.lister()

    def lister_classifications(
        self, type_classification: TypeClassification | str | None = None
    ) -> list[Classification]:
        """Renvoie les classifications, éventuellement filtrées par type ("age" ou "occupation").

        Lève DonneesInvalides si le type demandé n'existe pas.
        """
        if type_classification is not None:
            try:
                type_classification = TypeClassification(type_classification)
            except ValueError as erreur:
                raise DonneesInvalides(
                    f"Type de classification inconnu : {type_classification}."
                ) from erreur
        return self.classification_dao.lister(type_classification)

    # Recherches par code

    def trouver_indicateur(self, code_indicateur: str) -> Indicateur:
        """Renvoie l'indicateur correspondant au code.

        Lève DonneesInvalides si le code est vide, RessourceIntrouvable s'il n'existe pas.
        """
        self._verifier_code(code_indicateur, "indicateur")
        indicateur = self.indicateur_dao.trouver_par_code(code_indicateur)
        if indicateur is None:
            raise RessourceIntrouvable(f"Indicateur inconnu : {code_indicateur}.")
        return indicateur

    def trouver_pays(self, code_pays: str) -> Pays:
        """Renvoie le pays correspondant au code.

        Lève DonneesInvalides si le code est vide, RessourceIntrouvable s'il n'existe pas.
        """
        self._verifier_code(code_pays, "pays")
        pays = self.pays_dao.trouver_par_code(code_pays)
        if pays is None:
            raise RessourceIntrouvable(f"Pays inconnu : {code_pays}.")
        return pays

    def trouver_classification(self, code: str) -> Classification:
        """Renvoie la classification correspondant au code.

        Lève DonneesInvalides si le code est vide, RessourceIntrouvable s'il n'existe pas.
        """
        self._verifier_code(code, "classification")
        classification = self.classification_dao.trouver_par_code(code)
        if classification is None:
            raise RessourceIntrouvable(f"Classification inconnue : {code}.")
        return classification

    # Partie outil privé

    def _verifier_code(self, code: str | None, nom: str) -> None:
        """Lève DonneesInvalides si le code est absent ou ne contient que des espaces."""
        if code is None or not code.strip():
            raise DonneesInvalides(f"Le code {nom} est obligatoire.")
