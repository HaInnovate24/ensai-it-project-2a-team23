"""Accès aux données du journal d'activité."""

from business_object.journal_activite import JournalActivite
from dao.db_connection import DBConnection


class JournalDao:
    """Écriture et lecture des entrées du journal."""

    def __init__(self):
        """Initialise le DAO avec la connexion unique à la base."""
        self.conn = DBConnection().connection

    def creer(self, entree: JournalActivite) -> JournalActivite:
        """Enregistre une entrée de journal et renvoie l'objet créé."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO journal_activite (utilisateur_id, action, cible, details) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id, utilisateur_id, action, cible, details, date_heure;
                """,
                (entree.utilisateur_id, entree.action, entree.cible, entree.details)
            )
            row = cursor.fetchone()
            self.conn.commit()
            return JournalActivite(**row)

    def lister(self) -> list[JournalActivite]:
        """Renvoie les entrées du journal, de la plus récente à la plus ancienne."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, utilisateur_id, action, cible, details, date_heure 
                FROM journal_activite 
                ORDER BY date_heure DESC;
                """
            )
            rows = cursor.fetchall()
            return [JournalActivite(**row) for row in rows]