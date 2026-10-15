
import sys
sys.path.insert(0, "backend/src")

from client.ilostat_client import IlostatClient

client = IlostatClient()
print(f"URL appelée : {client.BASE_URL}")

csv = client.telecharger_indicateur(
    code_indicateur="EMP_TEMP_SEX_OCU_NB",
    from_date=2020,
    to_date=2021,
)

assert csv.strip(), "La réponse CSV est vide"
print(csv[:500])