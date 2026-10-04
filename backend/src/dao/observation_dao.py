"""Accès aux données des observations.

Point de coordination entre la collecte (P2), les analyses (P4) et
l'administration (P5) : les signatures ci-dessous doivent être validées
en commun avant implémentation.
"""

from psycopg2.extras import execute_values
from business_object.enums import Sexe
from business_object.observation import Observation
from dao.db_connection import DBConnection


class ObservationDao:
    """Lecture et écriture des observations en base."""

    def __init__(self):
        self.conn = DBConnection().connection

    def inserer_ou_mettre_a_jour_par_lot(self, observations: list[Observation]) -> int:
        """Insère ou met à jour un lot d'observations ; renvoie le nombre traité.

        S'appuie sur la contrainte d'unicité (indicateur, pays, période,
        sexe, classification) pour éviter les doublons.
        """
        if not observations:
            return 0

        valeurs = [
            (
                obs.code_indicateur,
                obs.code_pays,
                obs.periode,
                obs.valeur,
                obs.sexe.value if hasattr(obs.sexe, 'value') else obs.sexe,
                obs.code_classification,
                obs.import_id,
                obs.source
            )
            for obs in observations
        ]

        requete = """
            INSERT INTO observation 
            (code_indicateur, code_pays, periode, valeur, sexe, code_classification, import_id, source)
            VALUES %s
            ON CONFLICT ON CONSTRAINT uq_observation 
            DO UPDATE SET 
                valeur = EXCLUDED.valeur,
                import_id = EXCLUDED.import_id,
                source = EXCLUDED.source,
                date_import = CURRENT_TIMESTAMP;
        """

        with self.conn.cursor() as cursor:
            # execute_values est ultra optimisé pour les batch inserts
            execute_values(cursor, requete, valeurs)
            self.conn.commit()
            return len(observations)

    def lire_serie(
        self,
        code_indicateur: str,
        code_pays: str,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
    ) -> list[Observation]:
        """Renvoie la série temporelle correspondant aux filtres fournis."""
        requete = "SELECT * FROM observation WHERE code_indicateur = %s AND code_pays = %s"
        parametres = [code_indicateur, code_pays]

        if sexe:
            requete += " AND sexe = %s"
            parametres.append(sexe.value if hasattr(sexe, 'value') else sexe)
        
        if code_classification:
            requete += " AND code_classification = %s"
            parametres.append(code_classification)
            
        requete += " ORDER BY periode ASC;"

        with self.conn.cursor() as cursor:
            cursor.execute(requete, tuple(parametres))
            rows = cursor.fetchall()
            return [Observation(**row) for row in rows]

    def lire_par_periode(
        self,
        code_indicateur: str,
        periode: str,
        codes_pays: list[str] | None = None,
    ) -> list[Observation]:
        """Renvoie les observations d'une période donnée (comparaison, carte)."""
        requete = "SELECT * FROM observation WHERE code_indicateur = %s AND periode = %s"
        parametres = [code_indicateur, periode]

        if codes_pays:
            # L'opérateur = ANY(%s) de PostgreSQL fonctionne très bien avec les listes Python
            requete += " AND code_pays = ANY(%s)"
            parametres.append(codes_pays)

        with self.conn.cursor() as cursor:
            cursor.execute(requete, tuple(parametres))
            rows = cursor.fetchall()
            return [Observation(**row) for row in rows]

    def trouver_par_id(self, id: int) -> Observation | None:
        """Renvoie l'observation correspondant à l'identifiant, ou None."""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM observation WHERE id = %s;", (id,))
            row = cursor.fetchone()
            if row:
                return Observation(**row)
            return None

    def modifier(self, observation: Observation) -> bool:
        """Met à jour une observation existante ; renvoie True si succès."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE observation 
                SET valeur = %s, source = %s 
                WHERE id = %s;
                """,
                (observation.valeur, observation.source, observation.id)
            )
            self.conn.commit()
            return cursor.rowcount > 0

    def supprimer(self, id: int) -> bool:
        """Supprime une observation ; renvoie True si succès."""
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM observation WHERE id = %s;", (id,))
            self.conn.commit()
            return cursor.rowcount > 0