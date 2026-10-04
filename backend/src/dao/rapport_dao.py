"""Accès aux données des rapports."""

from business_object.rapport import Rapport
from dao.db_connection import DBConnection


class RapportDao:
    """Enregistrement et consultation des rapports PDF."""

    def __init__(self):
        """Initialise le DAO avec la connexion unique à la base."""
        self.conn = DBConnection().connection

    def creer(self, rapport: Rapport) -> Rapport:
        """Enregistre un rapport et renvoie l'objet créé."""
        valeur_statut = rapport.statut.value if hasattr(rapport.statut, 'value') else rapport.statut

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rapport (utilisateur_id, titre, description, fichier_path, statut) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id, utilisateur_id, titre, description, date_creation, fichier_path, statut;
                """,
                (
                    rapport.utilisateur_id, 
                    rapport.titre, 
                    rapport.description, 
                    rapport.fichier_path, 
                    valeur_statut
                )
            )
            row = cursor.fetchone()
            self.conn.commit()
            return Rapport(**row)

    def mettre_a_jour(self, rapport: Rapport) -> bool:
        """Met à jour le statut et le chemin de fichier d'un rapport."""
        valeur_statut = rapport.statut.value if hasattr(rapport.statut, 'value') else rapport.statut

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE rapport 
                SET statut = %s, fichier_path = %s 
                WHERE id = %s;
                """,
                (valeur_statut, rapport.fichier_path, rapport.id)
            )
            self.conn.commit()
            return cursor.rowcount > 0

    def trouver_par_id(self, id: int) -> Rapport | None:
        """Renvoie le rapport correspondant à l'identifiant, ou None."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, utilisateur_id, titre, description, date_creation, fichier_path, statut 
                FROM rapport WHERE id = %s;
                """,
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return Rapport(**row)
            return None

    def lister(self, utilisateur_id: int | None = None) -> list[Rapport]:
        """Renvoie les rapports, éventuellement filtrés par utilisateur."""
        with self.conn.cursor() as cursor:
            if utilisateur_id is not None:
                cursor.execute(
                    """
                    SELECT id, utilisateur_id, titre, description, date_creation, fichier_path, statut 
                    FROM rapport 
                    WHERE utilisateur_id = %s 
                    ORDER BY date_creation DESC;
                    """,
                    (utilisateur_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, utilisateur_id, titre, description, date_creation, fichier_path, statut 
                    FROM rapport 
                    ORDER BY date_creation DESC;
                    """
                )
            rows = cursor.fetchall()
            return [Rapport(**row) for row in rows]