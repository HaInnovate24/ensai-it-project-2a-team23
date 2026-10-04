"""Accès aux données des imports."""

from business_object.import_donnees import ImportDonnees
from dao.db_connection import DBConnection


class ImportDao:
    """Enregistrement et consultation des imports de données."""

    def __init__(self):
        """Initialise le DAO avec la connexion unique à la base."""
        self.conn = DBConnection().connection

    def creer(self, import_donnees: ImportDonnees) -> ImportDonnees:
        """Enregistre un import et renvoie l'objet créé."""
        valeur_statut = import_donnees.statut.value if hasattr(import_donnees.statut, 'value') else import_donnees.statut

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO import_donnees 
                (indicateur_code, utilisateur_id, date_debut, date_fin, statut, nombre_lignes, fichier_source, message_erreur) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, indicateur_code, utilisateur_id, date_debut, date_fin, statut, nombre_lignes, fichier_source, message_erreur;
                """,
                (
                    import_donnees.indicateur_code,
                    import_donnees.utilisateur_id,
                    import_donnees.date_debut,
                    import_donnees.date_fin,
                    valeur_statut,
                    import_donnees.nombre_lignes,
                    import_donnees.fichier_source,
                    import_donnees.message_erreur
                )
            )
            row = cursor.fetchone()
            self.conn.commit()
            return ImportDonnees(**row)

    def mettre_a_jour(self, import_donnees: ImportDonnees) -> bool:
        """Met à jour le statut et les compteurs d'un import."""
        valeur_statut = import_donnees.statut.value if hasattr(import_donnees.statut, 'value') else import_donnees.statut

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE import_donnees 
                SET date_fin = %s, 
                    statut = %s, 
                    nombre_lignes = %s, 
                    message_erreur = %s
                WHERE id = %s;
                """,
                (
                    import_donnees.date_fin,
                    valeur_statut,
                    import_donnees.nombre_lignes,
                    import_donnees.message_erreur,
                    import_donnees.id
                )
            )
            self.conn.commit()
            return cursor.rowcount > 0

    def lister(self) -> list[ImportDonnees]:
        """Renvoie l'historique des imports."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, indicateur_code, utilisateur_id, date_debut, date_fin, statut, nombre_lignes, fichier_source, message_erreur 
                FROM import_donnees 
                ORDER BY date_debut DESC;
                """
            )
            rows = cursor.fetchall()
            return [ImportDonnees(**row) for row in rows]