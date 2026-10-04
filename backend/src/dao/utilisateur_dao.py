"""Accès aux données des comptes utilisateurs."""

from business_object.utilisateur import Utilisateur
from dao.db_connection import DBConnection


class UtilisateurDao:
    """Création, recherche et modification des comptes."""

    def __init__(self):
        """Initialise le DAO avec la connexion unique à la base."""
        self.conn = DBConnection().connection

    def creer(self, utilisateur: Utilisateur) -> Utilisateur:
        """Insère un compte et renvoie l'objet créé."""
        valeur_role = utilisateur.role.value if hasattr(utilisateur.role, 'value') else utilisateur.role

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO utilisateur (nom_utilisateur, mot_de_passe_hash, role, actif) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id, nom_utilisateur, mot_de_passe_hash, role, actif, date_creation, derniere_connexion;
                """,
                (
                    utilisateur.nom_utilisateur,
                    utilisateur.mot_de_passe_hash,
                    valeur_role,
                    utilisateur.actif
                )
            )
            row = cursor.fetchone()
            self.conn.commit()
            return Utilisateur(**row)

    def trouver_par_id(self, id: int) -> Utilisateur | None:
        """Renvoie le compte correspondant à l'identifiant, ou None."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nom_utilisateur, mot_de_passe_hash, role, actif, date_creation, derniere_connexion 
                FROM utilisateur WHERE id = %s;
                """,
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return Utilisateur(**row)
            return None

    def trouver_par_nom(self, nom_utilisateur: str) -> Utilisateur | None:
        """Renvoie le compte correspondant au nom d'utilisateur, ou None."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nom_utilisateur, mot_de_passe_hash, role, actif, date_creation, derniere_connexion 
                FROM utilisateur WHERE nom_utilisateur = %s;
                """,
                (nom_utilisateur,)
            )
            row = cursor.fetchone()
            if row:
                return Utilisateur(**row)
            return None

    def lister(self) -> list[Utilisateur]:
        """Renvoie tous les comptes."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nom_utilisateur, mot_de_passe_hash, role, actif, date_creation, derniere_connexion 
                FROM utilisateur ORDER BY id;
                """
            )
            rows = cursor.fetchall()
            return [Utilisateur(**row) for row in rows]

    def modifier(self, utilisateur: Utilisateur) -> bool:
        """Met à jour un compte (rôle, activation, dernière connexion) et renvoie True si succès."""
        valeur_role = utilisateur.role.value if hasattr(utilisateur.role, 'value') else utilisateur.role

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE utilisateur 
                SET role = %s, actif = %s, derniere_connexion = %s, mot_de_passe_hash = %s
                WHERE id = %s;
                """,
                (
                    valeur_role,
                    utilisateur.actif,
                    utilisateur.derniere_connexion,
                    utilisateur.mot_de_passe_hash,
                    utilisateur.id
                )
            )
            self.conn.commit()
            # rowcount indique le nombre de lignes modifiées (1 si ok, 0 si l'ID n'existe pas)
            return cursor.rowcount > 0