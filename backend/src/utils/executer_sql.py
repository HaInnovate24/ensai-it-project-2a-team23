"""Exécute un fichier SQL sur la base applicative sans dépendre du client ``psql``.

Permet à ``make db-push`` et ``make db-load`` de fonctionner même si le binaire
``psql`` n'est pas installé (cas fréquent sous Windows) : on se connecte via
``psycopg2`` — déjà utilisé par l'application — et on positionne le ``search_path``
sur le schéma applicatif avant d'exécuter le contenu du fichier.

Usage :
    python backend/src/utils/executer_sql.py <chemin_du_fichier.sql> [--create-schema]

L'option ``--create-schema`` crée au préalable le schéma applicatif
(``POSTGRES_SCHEMA``) s'il n'existe pas (utilisé par ``db-push``).
"""

import sys

from utils.config import load_environment_variables


def main() -> int:
    """Applique le fichier SQL passé en argument dans le schéma applicatif."""
    load_environment_variables()

    import os

    import psycopg2
    from psycopg2 import sql

    if len(sys.argv) < 2:
        print("Usage : executer_sql.py <fichier.sql> [--create-schema]")
        return 2

    chemin = sys.argv[1]
    creer_schema = "--create-schema" in sys.argv[2:]
    schema = os.environ.get("POSTGRES_SCHEMA", "project")

    with open(chemin, encoding="utf-8") as fichier:
        contenu_sql = fichier.read()

    connexion = psycopg2.connect(
        dbname=os.environ["POSTGRES_DATABASE"],
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    try:
        with connexion.cursor() as curseur:
            if creer_schema:
                curseur.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
                )
            # Le search_path persiste pour les instructions suivantes de la même
            # session : les objets du fichier sont donc créés dans le bon schéma.
            curseur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            curseur.execute(contenu_sql)
        connexion.commit()
    except Exception:
        connexion.rollback()
        raise
    finally:
        connexion.close()

    print(f"Fichier {chemin} appliqué dans le schéma '{schema}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
