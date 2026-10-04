"""Accès aux données du référentiel des pays."""

from business_object.pays import Pays
from dao.db_connection import DBConnection


class PaysDao:
    """Lecture et création des pays en base."""

    def __init__(self):
        """Initialise le DAO en récupérant la connexion unique à la base."""
        self.conn = DBConnection().connection

    def lister(self) -> list[Pays]:
        """Renvoie tous les pays du référentiel."""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT code_pays, nom_pays FROM pays ORDER BY nom_pays;")
            rows = cursor.fetchall()
            # L'unpacking **row fonctionne car les clés du dictionnaire (code_pays, nom_pays) 
            # correspondent exactement aux paramètres de Pays.__init__
            return [Pays(**row) for row in rows]

    def trouver_par_code(self, code_pays: str) -> Pays | None:
        """Renvoie le pays correspondant au code, ou None."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT code_pays, nom_pays FROM pays WHERE code_pays = %s;", 
                (code_pays,)
            )
            row = cursor.fetchone()
            if row:
                return Pays(**row)
            return None

    def creer(self, pays: Pays) -> Pays:
        """Insère un pays et renvoie l'objet créé."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pays (code_pays, nom_pays) 
                VALUES (%s, %s) 
                RETURNING code_pays, nom_pays;
                """,
                (pays.code_pays, pays.nom_pays)
            )
            row = cursor.fetchone()
            self.conn.commit()  # Indispensable pour sauvegarder l'insertion en base
            return Pays(**row)