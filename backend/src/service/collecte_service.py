"""Collecte, parsing et persistance des données ILOSTAT."""

import io
from datetime import datetime

import pandas as pd
from business_object.enums import StatutImport
from business_object.import_donnees import ImportDonnees
from client.ilostat_client import IlostatClient
from dao.import_dao import ImportDao
from dao.observation_dao import ObservationDao
from service.parser_service import ParserService
from utils.journalisation import get_logger

logger = get_logger(__name__)


class CollecteService:
    """Télécharge un indicateur, le parse, l'enregistre et trace l'import."""

    def __init__(self, ilostat_client: IlostatClient | None = None):
        self.import_dao = ImportDao()
        self.observation_dao = ObservationDao()
        self.parser_service = ParserService()
        self.ilostat_client = ilostat_client or IlostatClient()

    def collecter_indicateur(
        self,
        code_indicateur: str,
        from_date: int = 2014,
        to_date: int = 2026,
        utilisateur_id: int | None = None,
    ) -> ImportDonnees:
        """Collecte un indicateur sur une période et renvoie la trace d'import."""
        if not code_indicateur or not code_indicateur.strip():
            raise ValueError("Le code de l'indicateur est obligatoire.")
        if from_date > to_date:
            raise ValueError(
                "L'année de début (from_date) doit être inférieure ou égale à l'année de fin (to_date)."
            )

        trace = self.import_dao.creer(
            ImportDonnees(
                indicateur_code=code_indicateur.strip(),
                utilisateur_id=utilisateur_id,
                date_debut=datetime.now(),
                statut=StatutImport.EN_COURS,
                fichier_source=IlostatClient.BASE_URL,
            )
        )

        try:
            logger.info(
                "Collecte ILOSTAT : indicateur=%s, période=%s-%s",
                code_indicateur,
                from_date,
                to_date,
            )

            annees_existantes = self.observation_dao.lister_annees_existantes(
                code_indicateur.strip(), from_date, to_date
            )
            annees_a_charger = [
                annee
                for annee in range(from_date, to_date + 1)
                if annee not in annees_existantes
            ]
            intervalles_a_charger = self._regrouper_annees_consecutives(annees_a_charger)

            nombre_annees_ignorees = to_date - from_date + 1 - len(annees_a_charger)
            if nombre_annees_ignorees:
                logger.info(
                    "%s année(s) déjà stockée(s) pour %s ; téléchargement ignoré",
                    nombre_annees_ignorees,
                    code_indicateur,
                )

            observations = []
            for debut, fin in intervalles_a_charger:
                csv_brut = self.ilostat_client.telecharger_indicateur(
                    code_indicateur=code_indicateur.strip(),
                    from_date=debut,
                    to_date=fin,
                )
                data = pd.read_csv(io.StringIO(csv_brut))
                observations.extend(
                    self.parser_service.parser(data, code_indicateur.strip())
                )

            if intervalles_a_charger and not observations:
                raise ValueError("Aucune observation exploitable reçue pour cet indicateur.")

            # La contrainte uq_observation est aussi appliquée par le DAO en base,
            # mais PostgreSQL ne peut pas traiter deux fois la même clé dans un
            # seul INSERT ... ON CONFLICT. On garde donc la dernière valeur reçue
            # pour chaque combinaison unique avant l'upsert.
            observations_uniques = {}
            for observation in observations:
                observation.import_id = trace.id
                sexe = (
                    observation.sexe.value
                    if hasattr(observation.sexe, "value")
                    else observation.sexe
                )
                cle = (
                    observation.code_indicateur,
                    observation.code_pays,
                    observation.periode,
                    sexe,
                    observation.code_classification,
                )
                observations_uniques[cle] = observation

            nombre_doublons = len(observations) - len(observations_uniques)
            if nombre_doublons:
                logger.info(
                    "%s doublon(s) écarté(s) pour l'indicateur %s",
                    nombre_doublons,
                    code_indicateur,
                )
            observations = list(observations_uniques.values())
            trace.nombre_lignes = (
                self.observation_dao.inserer_ou_mettre_a_jour_par_lot(observations)
                if observations
                else 0
            )
            trace.statut = StatutImport.SUCCES
            trace.message_erreur = None
        except Exception as exc:
            logger.exception("Échec de la collecte de l'indicateur %s", code_indicateur)
            # Une erreur pendant l'upsert laisse PostgreSQL dans une transaction
            # avortée. Le rollback permet au DAO d'import de sauvegarder l'échec.
            self.observation_dao.conn.rollback()
            trace.statut = StatutImport.ECHEC
            trace.message_erreur = str(exc)[:250]
        finally:
            trace.date_fin = datetime.now()
            self.import_dao.mettre_a_jour(trace)

        return trace

    @staticmethod
    def _regrouper_annees_consecutives(annees: list[int]) -> list[tuple[int, int]]:
        """Réunit les années manquantes en plages contiguës pour limiter les appels API."""
        if not annees:
            return []

        plages = []
        debut = precedent = annees[0]
        for annee in annees[1:]:
            if annee != precedent + 1:
                plages.append((debut, precedent))
                debut = annee
            precedent = annee
        plages.append((debut, precedent))
        return plages
