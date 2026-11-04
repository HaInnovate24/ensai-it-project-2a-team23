"""F3, F4, F5 et carte : construction des séries et comparaisons."""

from business_object.enums import Sexe
from business_object.indicateur import Indicateur
from business_object.observation import Observation
from business_object.pays import Pays
from dao.classification_dao import ClassificationDao
from dao.indicateur_dao import IndicateurDao
from dao.observation_dao import ObservationDao
from dao.pays_dao import PaysDao
from model.analyse_model import Comparaison, PointSerie, Serie
from utils.exceptions import DonneesInvalides, RessourceIntrouvable


class AnalyseService:
    """Construit les séries temporelles et les comparaisons pour les analyses.

    Règles communes à toutes les analyses :
        - Si aucun sexe n'est demandé, on prend "total" (sinon on mélangerait
          hommes, femmes et total sur un même graphique).
        - Si aucune classification n'est demandée, on garde uniquement les
          observations sans classification (code_classification vide).
        - Les observations sans valeur (None) sont ignorées.
    """

    def __init__(
        self,
        observation_dao: ObservationDao | None = None,
        indicateur_dao: IndicateurDao | None = None,
        pays_dao: PaysDao | None = None,
        classification_dao: ClassificationDao | None = None,
    ):
        """Initialisation du service."""
        self.observation_dao = observation_dao if observation_dao is not None else ObservationDao()
        self.indicateur_dao = indicateur_dao if indicateur_dao is not None else IndicateurDao()
        self.pays_dao = pays_dao if pays_dao is not None else PaysDao()
        self.classification_dao = (
            classification_dao if classification_dao is not None else ClassificationDao()
        )

    # Méthodes publiques (appelées par le controller)

    def evolution(
        self,
        code_indicateur: str,
        code_pays: str,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
        nb_periodes: int | None = None,
    ) -> Serie:
        """F3 : renvoie l'évolution temporelle d'un indicateur pour un pays.

        nb_periodes permet de ne garder que les N dernières périodes
        (ex. 8 pour les 8 derniers trimestres). None signifie "toutes".
        """
        if not code_pays:
            raise DonneesInvalides("Le code pays est obligatoire.")
        if nb_periodes is not None and nb_periodes < 1:
            raise DonneesInvalides("Le nombre de périodes doit être supérieur ou égal à 1.")

        sexe = self._sexe_ou_defaut(sexe)
        indicateur = self._trouver_indicateur(code_indicateur)
        pays = self._trouver_pays(code_pays)
        self._verifier_classification(code_classification)

        observations = self._lire_serie_filtree(
            code_indicateur, code_pays, sexe, code_classification
        )
        if not observations:
            raise RessourceIntrouvable(
                f"Aucune donnée pour l'indicateur {code_indicateur} et le pays {code_pays}."
            )

        if nb_periodes is not None:
            observations = observations[-nb_periodes:]

        libelle = f"{self._libelle_indicateur(indicateur)} - {pays.nom_pays}"
        return Serie(libelle=libelle, points=self._vers_points(observations))

    def comparer_pays(
        self,
        code_indicateur: str,
        codes_pays: list[str],
        periode: str | None = None,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
    ) -> Comparaison:
        """Compare un indicateur entre plusieurs pays.

        Chaque pays donne une série d'un seul point. Les séries sont triées de la
        valeur la plus haute à la plus basse. La première est le pays le plus
        haut, la dernière le pays le plus bas.

        Si periode est None, on prend pour chaque pays sa période la plus récente.
        """
        codes = self._sans_doublons(codes_pays)
        if not codes:
            raise DonneesInvalides("Indiquez au moins un pays.")

        sexe = self._sexe_ou_defaut(sexe)
        self._trouver_indicateur(code_indicateur)
        self._verifier_classification(code_classification)
        pays_par_code = {code: self._trouver_pays(code) for code in codes}

        if periode is None:
            observations = self._derniere_observation_par_pays(
                code_indicateur, codes, sexe, code_classification
            )
        else:
            observations = self._lire_periode_filtree(
                code_indicateur, periode, codes, sexe, code_classification
            )
        if not observations:
            raise RessourceIntrouvable(
                f"Aucune donnée pour l'indicateur {code_indicateur} sur les pays demandés."
            )

        series = [
            Serie(
                libelle=pays_par_code[obs.code_pays].nom_pays,
                points=self._vers_points([obs]),
            )
            for obs in observations
        ]
        # Valeur décroissante, puis nom du pays pour départager les égalités.
        series.sort(key=lambda serie: (-serie.points[0].valeur, serie.libelle))
        return Comparaison(series=series)

    def comparer_indicateurs(
        self,
        codes_indicateur: list[str],
        code_pays: str,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
    ) -> Comparaison:
        """F5 : compare plusieurs indicateurs pour un même pays.

        Chaque indicateur donne une série. L'unité est écrite dans le libellé car
        les indicateurs n'ont pas forcément la même unité. Un indicateur sans
        donnée pour ce pays est ignoré.
        """
        codes = self._sans_doublons(codes_indicateur)
        if not codes:
            raise DonneesInvalides("Indiquez au moins un indicateur.")
        if not code_pays:
            raise DonneesInvalides("Le code pays est obligatoire.")

        sexe = self._sexe_ou_defaut(sexe)
        self._trouver_pays(code_pays)
        self._verifier_classification(code_classification)
        indicateurs = [self._trouver_indicateur(code) for code in codes]

        series = []
        for indicateur in indicateurs:
            observations = self._lire_serie_filtree(
                indicateur.code_indicateur, code_pays, sexe, code_classification
            )
            if observations:
                series.append(
                    Serie(
                        libelle=self._libelle_indicateur(indicateur),
                        points=self._vers_points(observations),
                    )
                )

        if not series:
            raise RessourceIntrouvable(f"Aucune donnée pour le pays {code_pays}.")
        return Comparaison(series=series)

    def carte(
        self,
        code_indicateur: str,
        periode: str,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
    ) -> Comparaison:
        """Renvoie la valeur de l'indicateur pour chaque pays, à une période donnée.

        Chaque pays donne une série d'un seul point, triées par nom de pays.
        """
        if not periode:
            raise DonneesInvalides("La période est obligatoire pour la carte.")

        sexe = self._sexe_ou_defaut(sexe)
        self._trouver_indicateur(code_indicateur)
        self._verifier_classification(code_classification)

        observations = self._lire_periode_filtree(
            code_indicateur, periode, None, sexe, code_classification
        )
        if not observations:
            raise RessourceIntrouvable(
                f"Aucune donnée pour l'indicateur {code_indicateur} à la période {periode}."
            )

        noms_pays = {pays.code_pays: pays.nom_pays for pays in self.pays_dao.lister()}
        series = [
            Serie(
                libelle=noms_pays.get(obs.code_pays, obs.code_pays),
                points=self._vers_points([obs]),
            )
            for obs in observations
        ]
        series.sort(key=lambda serie: serie.libelle)
        return Comparaison(series=series)

    # Méthodes privées (helpers appelés par les méthodes publiques)

    def _sexe_ou_defaut(self, sexe: Sexe | None) -> Sexe:
        """Renvoie le sexe demandé, ou Sexe.TOTAL si aucun n'est précisé."""
        return sexe if sexe is not None else Sexe.TOTAL

    def _trouver_indicateur(self, code_indicateur: str) -> Indicateur:
        """Renvoie l'indicateur correspondant au code, ou lève RessourceIntrouvable."""
        if not code_indicateur:
            raise DonneesInvalides("Le code indicateur est obligatoire.")
        indicateur = self.indicateur_dao.trouver_par_code(code_indicateur)
        if indicateur is None:
            raise RessourceIntrouvable(f"Indicateur inconnu : {code_indicateur}.")
        return indicateur

    def _trouver_pays(self, code_pays: str) -> Pays:
        """Renvoie le pays correspondant au code, ou lève RessourceIntrouvable."""
        if not code_pays:
            raise DonneesInvalides("Le code pays est obligatoire.")
        pays = self.pays_dao.trouver_par_code(code_pays)
        if pays is None:
            raise RessourceIntrouvable(f"Pays inconnu : {code_pays}.")
        return pays

    def _verifier_classification(self, code_classification: str | None) -> None:
        """Vérifie que la classification existe (si fournie), sinon lève une erreur."""
        if not code_classification:
            return
        if self.classification_dao.trouver_par_code(code_classification) is None:
            raise RessourceIntrouvable(f"Classification inconnue : {code_classification}.")

    def _observation_valide(self, obs: Observation, code_classification: str | None) -> bool:
        """Vrai si l'observation a une valeur et correspond à la classification demandée.

        Si aucune classification n'est demandée, on ne garde que les observations
        sans classification (sinon on mélangerait les sous-catégories avec l'agrégat).
        """
        if obs.valeur is None:
            return False
        if code_classification:
            return obs.code_classification == code_classification
        return not obs.code_classification

    def _lire_serie_filtree(
        self,
        code_indicateur: str,
        code_pays: str,
        sexe: Sexe,
        code_classification: str | None,
    ) -> list[Observation]:
        """Lit la série temporelle d'un pays, filtrée par sexe et classification."""
        observations = self.observation_dao.lire_serie(
            code_indicateur, code_pays, sexe, code_classification
        )
        return [
            obs for obs in observations if self._observation_valide(obs, code_classification)
        ]

    def _lire_periode_filtree(
        self,
        code_indicateur: str,
        periode: str,
        codes_pays: list[str] | None,
        sexe: Sexe,
        code_classification: str | None,
    ) -> list[Observation]:
        """Lit les observations d'une période donnée, filtrées par sexe et classification."""
        observations = self.observation_dao.lire_par_periode(
            code_indicateur, periode, codes_pays
        )
        return [
            obs
            for obs in observations
            if obs.sexe == sexe and self._observation_valide(obs, code_classification)
        ]

    def _derniere_observation_par_pays(
        self,
        code_indicateur: str,
        codes_pays: list[str],
        sexe: Sexe,
        code_classification: str | None,
    ) -> list[Observation]:
        """Renvoie la dernière observation disponible pour chaque pays demandé."""
        dernieres: list[Observation] = []
        for code_pays in codes_pays:
            # La série est triée par période croissante : la dernière est la plus récente.
            observations = self._lire_serie_filtree(
                code_indicateur, code_pays, sexe, code_classification
            )
            if observations:
                dernieres.append(observations[-1])
        return dernieres

    def _vers_points(self, observations: list[Observation]) -> list[PointSerie]:
        """Convertit des observations en points de série (période, valeur)."""
        return [
            PointSerie(periode=obs.periode, valeur=obs.valeur)
            for obs in observations
            if obs.valeur is not None
        ]

    def _libelle_indicateur(self, indicateur: Indicateur) -> str:
        """Construit le libellé d'un indicateur (description et unité)."""
        description = indicateur.description or indicateur.code_indicateur or ""
        if indicateur.unite:
            return f"{description} ({indicateur.unite})"
        return description

    def _sans_doublons(self, codes: list[str]) -> list[str]:
        """Supprime les doublons d'une liste de codes en conservant l'ordre."""
        if not codes:
            return []
        vus: set[str] = set()
        resultat: list[str] = []
        for code in codes:
            if code and code not in vus:
                vus.add(code)
                resultat.append(code)
        return resultat
