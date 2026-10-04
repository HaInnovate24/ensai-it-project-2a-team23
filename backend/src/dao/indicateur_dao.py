"""Accès aux données du référentiel des indicateurs."""

from business_object.indicateur import Indicateur
from dao.db_connection import DBConnection


class IndicateurDao:
    """Lecture et création des indicateurs en base."""

    def __init__(self):
        """Initialise le DAO en récupérant la connexion unique à la base."""
        self.conn = DBConnection().connection

    def lister(self) -> list[Indicateur]:
        """Renvoie tous les indicateurs du référentiel."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT code_indicateur, description, unite, source, actif "
                "FROM indicateur ORDER BY description;"
            )
            rows = cursor.fetchall()
            return [Indicateur(**row) for row in rows]

    def trouver_par_code(self, code_indicateur: str) -> Indicateur | None:
        """Renvoie l'indicateur correspondant au code, ou None."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT code_indicateur, description, unite, source, actif "
                "FROM indicateur WHERE code_indicateur = %s;",
                (code_indicateur,)
            )
            row = cursor.fetchone()
            if row:
                return Indicateur(**row)
            return None

    def creer(self, indicateur: Indicateur) -> Indicateur:
        """Insère un indicateur et renvoie l'objet créé."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO indicateur (code_indicateur, description, unite, source, actif) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING code_indicateur, description, unite, source, actif;
                """,
                (
                    indicateur.code_indicateur,
                    indicateur.description,
                    indicateur.unite,
                    indicateur.source,
                    indicateur.actif
                )
            )
            row = cursor.fetchone()
            self.conn.commit()  # Indispensable pour enregistrer la création
            return Indicateur(**row)