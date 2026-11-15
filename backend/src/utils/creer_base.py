"""Crée la base de données PostgreSQL applicative si elle n'existe pas encore.

Lancé par ``make db-create`` (et donc par ``make init``) avant la création du
schéma et des tables. On se connecte à la base de maintenance ``postgres`` pour
pouvoir exécuter ``CREATE DATABASE`` (qui ne peut pas s'exécuter dans une
transaction ni depuis la base que l'on veut créer).
"""

from utils.config import load_environment_variables


def main() -> None:
    """Crée la base cible (POSTGRES_DATABASE) si elle est absente."""
    load_environment_variables()

    import os

    import psycopg2
    from psycopg2 import sql

    cible = os.environ["POSTGRES_DATABASE"]
    params = {
        "host": os.environ["POSTGRES_HOST"],
        "port": os.environ["POSTGRES_PORT"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
    }

    try:
        connexion = psycopg2.connect(dbname="postgres", **params)
    except psycopg2.Error as erreur:
        # Certaines bases managées interdisent la connexion à "postgres" ou la
        # création de bases. Si la base cible existe déjà, l'étape suivante
        # (db-push) fonctionnera malgré tout : on se contente d'avertir.
        print(f"Impossible de se connecter à la base de maintenance 'postgres' : {erreur}")
        print(f"La base '{cible}' doit déjà exister (création automatique ignorée).")
        return

    connexion.autocommit = True  # CREATE DATABASE interdit dans une transaction
    try:
        with connexion.cursor() as curseur:
            curseur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (cible,))
            if curseur.fetchone():
                print(f"Base '{cible}' déjà présente.")
            else:
                curseur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(cible)))
                print(f"Base '{cible}' créée.")
    finally:
        connexion.close()


if __name__ == "__main__":
    main()
