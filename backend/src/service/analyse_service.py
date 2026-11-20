"""F3, F4, F5 et carte : construction des séries et comparaisons."""

from datetime import datetime

from business_object.enums import Sexe
from business_object.indicateur import Indicateur
from business_object.observation import Observation
from business_object.pays import Pays
from dao.classification_dao import ClassificationDao
from dao.indicateur_dao import IndicateurDao
from dao.observation_dao import ObservationDao
from dao.pays_dao import PaysDao
from model.analyse_model import Comparaison, PointSerie, ResumeSerie, Serie
from utils.exceptions import DonneesInvalides, RessourceIntrouvable
from utils.periodes import convertir_periode, fenetre_de_periodes


class AnalyseService:
    """Construit les séries temporelles et les comparaisons pour les analyses.

    Règles communes à toutes les analyses :
        - Si aucun sexe n'est demandé, on prend "total" (sinon on mélangerait
          hommes, femmes et total sur un même graphique).
        - Si aucune classification n'est demandée, on garde uniquement les
          observations sans classification (code_classification vide). Si les
          données n'existent que par classification, on lève DonneesInvalides.
        - Les observations sans valeur (None) sont ignorées.
        - Une période n'a qu'une valeur : si une même période apparaît plusieurs
          fois, on garde l'observation importée en dernier.
        - Les périodes sans donnée ne sont jamais passées sous silence : elles sont
          listées dans periodes_manquantes (séries) ou sans_donnees (comparaisons).
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

        nb_periodes limite l'analyse aux N dernières périodes du calendrier (ex. 8 pour
        les 8 derniers trimestres), calculées à partir de la dernière période disponible.
        Les périodes de cette fenêtre sans donnée sont renvoyées dans periodes_manquantes.
        None signifie "toutes les périodes" (seuls les trous sont alors signalés).
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
                f"Le pays {pays.nom_pays} existe, mais aucune donnée n'est disponible "
                f"pour l'indicateur {code_indicateur}."
            )

        points, periodes_manquantes = self._points_et_periodes_manquantes(observations, nb_periodes)
        libelle = f"{self._libelle_indicateur(indicateur)} - {pays.nom_pays}"
        return Serie(libelle=libelle, points=points, periodes_manquantes=periodes_manquantes)

    def resumer_evolution(
        self,
        code_indicateur: str,
        code_pays: str,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
        nb_periodes: int | None = None,
    ) -> ResumeSerie:
        """F3 : calcule le résumé de l'évolution (minimum, maximum, moyenne, variation).

        On réutilise evolution() : les mêmes vérifications et les mêmes erreurs
        s'appliquent, puis on calcule les statistiques sur les points disponibles.

        Variation absolue = dernière valeur - première valeur.
        Variation relative = variation absolue / |première valeur| x 100 (en %).
        La moyenne est une moyenne simple des valeurs (non pondérée).
        """
        serie = self.evolution(code_indicateur, code_pays, sexe, code_classification, nb_periodes)

        valeurs = [point.valeur for point in serie.points]
        premier = serie.points[0]
        dernier = serie.points[-1]

        variation_absolue = None
        variation_relative = None
        if len(serie.points) >= 2:
            variation_absolue = dernier.valeur - premier.valeur
            if premier.valeur != 0:
                variation_relative = variation_absolue / abs(premier.valeur) * 100

        return ResumeSerie(
            libelle=serie.libelle,
            nb_points=len(valeurs),
            periode_debut=premier.periode,
            periode_fin=dernier.periode,
            valeur_debut=premier.valeur,
            valeur_fin=dernier.valeur,
            minimum=min(valeurs),
            maximum=max(valeurs),
            moyenne=sum(valeurs) / len(valeurs),
            variation_absolue=variation_absolue,
            variation_relative=variation_relative,
            periodes_manquantes=serie.periodes_manquantes,
        )

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

        Si periode est None, on prend pour chaque pays sa période la plus récente
        (elle peut différer d'un pays à l'autre : elle est indiquée dans chaque point).
        Les pays demandés sans donnée sont listés dans sans_donnees.
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
            observations = list(self._une_par_cle(observations, lambda obs: obs.code_pays).values())
        if not observations:
            raise RessourceIntrouvable(
                f"Aucune donnée pour l'indicateur {code_indicateur} sur les pays demandés."
            )

        pays_avec_donnees = {obs.code_pays for obs in observations}
        sans_donnees = [
            pays_par_code[code].nom_pays for code in codes if code not in pays_avec_donnees
        ]
        series = [
            Serie(
                libelle=pays_par_code[obs.code_pays].nom_pays,
                points=self._vers_points([obs]),
            )
            for obs in observations
        ]
        # Valeur décroissante, puis nom du pays pour départager les égalités.
        series.sort(key=lambda serie: (-serie.points[0].valeur, serie.libelle))
        return Comparaison(series=series, sans_donnees=sans_donnees)

    def comparer_indicateurs(
        self,
        codes_indicateur: list[str],
        code_pays: str,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
        base_100: bool = False,
    ) -> Comparaison:
        """F5 : compare plusieurs indicateurs pour un même pays.

        Chaque indicateur donne une série. L'unité est écrite dans le libellé car
        les indicateurs n'ont pas forcément la même unité. Un indicateur sans
        donnée pour ce pays n'a pas de série : il est listé dans sans_donnees.

        Avec base_100=True, chaque série est ramenée à 100 à la première période
        commune à toutes les séries : on compare alors des évolutions relatives,
        lisibles sur un même graphique malgré des unités différentes.
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
        descriptions = []
        sans_donnees = []
        for indicateur in indicateurs:
            observations = self._lire_serie_filtree(
                indicateur.code_indicateur, code_pays, sexe, code_classification
            )
            if not observations:
                sans_donnees.append(self._libelle_indicateur(indicateur))
                continue
            points, periodes_manquantes = self._points_et_periodes_manquantes(observations, None)
            series.append(
                Serie(
                    libelle=self._libelle_indicateur(indicateur),
                    points=points,
                    periodes_manquantes=periodes_manquantes,
                )
            )
            descriptions.append(indicateur.description or indicateur.code_indicateur)

        if not series:
            raise RessourceIntrouvable(f"Aucune donnée pour le pays {code_pays}.")
        if base_100:
            series = self._ramener_en_base_100(series, descriptions)
        return Comparaison(series=series, sans_donnees=sans_donnees)

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
        observations = list(self._une_par_cle(observations, lambda obs: obs.code_pays).values())
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

    def _sexe_ou_defaut(self, sexe) -> Sexe:
        """Renvoie le Sexe correspondant, ou TOTAL par défaut."""
        if not sexe:
            return Sexe.TOTAL

        if isinstance(sexe, Sexe):
            return sexe

        # Si c'est une chaîne de caractères, on tente de la convertir
        try:
            return Sexe(sexe)
        except ValueError as erreur:
            raise DonneesInvalides(f"Sexe invalide : {sexe}") from erreur

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

    def _filtrer(
        self, observations: list[Observation], sexe: Sexe, code_classification: str | None
    ) -> list[Observation]:
        """Garde les observations du bon sexe, avec une valeur et la bonne classification.

        Lève DonneesInvalides si aucune classification n'est demandée alors que les
        données n'existent que par classification (on ne saurait pas laquelle choisir).
        """
        gardees = [
            obs
            for obs in observations
            if obs.sexe == sexe and self._observation_valide(obs, code_classification)
        ]
        if gardees or code_classification:
            return gardees

        existe_par_classification = any(
            obs.sexe == sexe and obs.valeur is not None and obs.code_classification
            for obs in observations
        )
        if existe_par_classification:
            raise DonneesInvalides("Des données existent mais nécessitent une classification.")
        return []

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
        return self._filtrer(observations, sexe, code_classification)

    def _lire_periode_filtree(
        self,
        code_indicateur: str,
        periode: str,
        codes_pays: list[str] | None,
        sexe: Sexe,
        code_classification: str | None,
    ) -> list[Observation]:
        """Lit les observations d'une période donnée, filtrées par sexe et classification."""
        observations = self.observation_dao.lire_par_periode(code_indicateur, periode, codes_pays)
        return self._filtrer(observations, sexe, code_classification)

    def _derniere_observation_par_pays(
        self,
        code_indicateur: str,
        codes_pays: list[str],
        sexe: Sexe,
        code_classification: str | None,
    ) -> list[Observation]:
        """Renvoie la dernière observation disponible de chaque pays (les pays sans donnée sont absents)."""
        dernieres: list[Observation] = []
        for code_pays in codes_pays:
            observations = self._lire_serie_filtree(
                code_indicateur, code_pays, sexe, code_classification
            )
            par_periode = self._une_par_cle(observations, lambda obs: obs.periode)
            if par_periode:
                # La fenêtre d'une seule période est la plus récente du calendrier.
                plus_recente, _ = fenetre_de_periodes(list(par_periode), 1)
                dernieres.append(par_periode[plus_recente[0]])
        return dernieres

    def _une_par_cle(self, observations: list[Observation], cle) -> dict[str, Observation]:
        """Garde une seule observation par clé (période, pays...) : la plus récemment importée.

        Normalement la base interdit les doublons (contrainte d'unicité). Cette règle protège
        le calcul si une même période apparaissait plusieurs fois (ex. valeur corrigée).
        """
        retenues: dict[str, Observation] = {}
        for obs in observations:
            existante = retenues.get(cle(obs))
            if existante is None or self._date_import(obs) >= self._date_import(existante):
                retenues[cle(obs)] = obs
        return retenues

    def _date_import(self, obs: Observation) -> datetime:
        """Renvoie la date d'import de l'observation (très ancienne si elle est inconnue)."""
        return obs.date_import if obs.date_import is not None else datetime.min

    def _points_et_periodes_manquantes(
        self, observations: list[Observation], nb_periodes: int | None
    ) -> tuple[list[PointSerie], list[str]]:
        """Construit les points d'une série et la liste des périodes manquantes.

        Une seule observation par période est gardée, puis on applique la fenêtre
        de nb_periodes périodes consécutives (voir utils.periodes.fenetre_de_periodes).
        """
        par_periode = self._une_par_cle(observations, lambda obs: obs.periode)
        gardees, manquantes = fenetre_de_periodes(list(par_periode), nb_periodes)
        points = [self._vers_points([par_periode[periode]])[0] for periode in gardees]
        return points, manquantes

    def _ramener_en_base_100(self, series: list[Serie], descriptions: list[str]) -> list[Serie]:
        """Ramène chaque série à 100 à la première période commune à toutes les séries.

        Chaque valeur est divisée par la valeur de sa série à la période de base,
        puis multipliée par 100. Lève DonneesInvalides s'il n'y a aucune période
        commune ou si une valeur de base est nulle ou négative.
        """
        periodes_communes = {point.periode for point in series[0].points}
        for serie in series[1:]:
            periodes_communes &= {point.periode for point in serie.points}
        if not periodes_communes:
            raise DonneesInvalides(
                "Les indicateurs n'ont aucune période en commun : "
                "impossible de les ramener en base 100."
            )
        periode_base = min(periodes_communes, key=self._cle_chronologique)

        resultat = []
        for serie, description in zip(series, descriptions, strict=True):
            valeur_base = next(
                point.valeur for point in serie.points if point.periode == periode_base
            )
            if valeur_base <= 0:
                raise DonneesInvalides(
                    f"Impossible de ramener '{description}' en base 100 : "
                    f"sa valeur à {periode_base} est nulle ou négative."
                )
            points = [
                PointSerie(periode=point.periode, valeur=point.valeur / valeur_base * 100)
                for point in serie.points
            ]
            resultat.append(
                Serie(
                    libelle=f"{description} (base 100 = {periode_base})",
                    points=points,
                    periodes_manquantes=serie.periodes_manquantes,
                )
            )
        return resultat

    def _cle_chronologique(self, periode: str) -> tuple[int, int | str]:
        """Clé de tri chronologique : position dans le calendrier, sinon ordre alphabétique."""
        conversion = convertir_periode(periode)
        if conversion is not None:
            return (0, conversion[1])
        return (1, periode)

    def _vers_points(self, observations: list[Observation]) -> list[PointSerie]:
        """Convertit des observations en points de série (période, valeur en float)."""
        return [
            PointSerie(periode=obs.periode, valeur=float(obs.valeur))
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
