"""Accès aux données du référentiel des classifications."""

from business_object.classification import Classification
from business_object.enums import TypeClassification
from dao.db_connection import DBConnection


class ClassificationDao:
    """Lecture et création des classifications (âge, occupation) en base."""

    def __init__(self):
        """Initialise le DAO avec la connexion unique."""
        self.conn = DBConnection().connection

    def lister(self, type: TypeClassification | None = None) -> list[Classification]:
        """Renvoie les classifications, éventuellement filtrées par type."""
        with self.conn.cursor() as cursor:
            if type is not None:
                # Si on passe un Enum, on extrait sa valeur (ex: 'age')
                valeur_type = type.value if hasattr(type, 'value') else type
                cursor.execute(
                    "SELECT code, libelle, type FROM classification WHERE type = %s ORDER BY libelle;",
                    (valeur_type,)
                )
            else:
                cursor.execute(
                    "SELECT code, libelle, type FROM classification ORDER BY libelle;"
                )
            
            rows = cursor.fetchall()
            return [Classification(**row) for row in rows]

    def trouver_par_code(self, code: str) -> Classification | None:
        """Renvoie la classification correspondant au code, ou None."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT code, libelle, type FROM classification WHERE code = %s;",
                (code,)
            )
            row = cursor.fetchone()
            if row:
                return Classification(**row)
            return None

    def creer(self, classification: Classification) -> Classification:
        """Insère une classification et renvoie l'objet créé."""
        # On s'assure d'extraire la chaîne de caractères de l'Enum pour la base
        valeur_type = classification.type.value if hasattr(classification.type, 'value') else classification.type

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO classification (code, libelle, type) 
                VALUES (%s, %s, %s) 
                RETURNING code, libelle, type;
                """,
                (classification.code, classification.libelle, valeur_type)
            )
            row = cursor.fetchone()
            self.conn.commit()
            return Classification(**row)