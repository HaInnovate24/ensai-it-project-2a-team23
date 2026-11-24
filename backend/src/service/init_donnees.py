"""Collecte initiale des données : importe tous les indicateurs actifs du référentiel.

Lancé par ``make db-import`` (et donc par ``make init``). On lit les indicateurs
actifs chargés par ``pop_referentiels.sql`` (actuellement EMP_TEMP_SEX_OCU_NB et
POP_XWAP_SEX_AGE_NB) et on collecte chacun depuis ILOSTAT. Ajouter un indicateur
au référentiel suffit donc pour qu'il soit collecté ici, sans toucher au code.
"""

from utils.config import load_environment_variables


def main() -> int:
    """Collecte chaque indicateur actif ; renvoie le nombre d'imports en échec."""
    load_environment_variables()

    from client.ilostat_client import IlostatClient
    from dao.indicateur_dao import IndicateurDao
    from service.collecte_service import CollecteService

    # Import reproductible et hors ligne : on lit les CSV déjà présents dans
    # backend/src/client/data/ (jamais d'appel réseau à ILOSTAT), puis on parse
    # et on enregistre les observations en base comme d'habitude.
    service = CollecteService(ilostat_client=IlostatClient(offline=True))
    indicateurs = [indicateur for indicateur in IndicateurDao().lister() if indicateur.actif]

    if not indicateurs:
        print("Aucun indicateur actif dans le référentiel : lancez d'abord 'make db-load'.")
        return 1

    echecs = 0
    print(f"Collecte de {len(indicateurs)} indicateur(s) actif(s)...")
    for indicateur in indicateurs:
        print(f"  - {indicateur.code_indicateur} ...", flush=True)
        trace = service.collecter_indicateur(indicateur.code_indicateur)
        statut = trace.statut.value if hasattr(trace.statut, "value") else trace.statut
        print(f"      statut={statut}, lignes={trace.nombre_lignes}")
        if trace.message_erreur:
            echecs += 1
            print(f"      erreur : {trace.message_erreur}")

    print(f"Collecte terminée ({echecs} échec(s) sur {len(indicateurs)}).")
    return echecs


if __name__ == "__main__":
    import sys

    sys.exit(1 if main() else 0)
