tester la collecte seulement

uv run --project backend python -c "import sys; sys.path.insert(0, 'backend/src'); from client.ilostat_client import IlostatClient; csv = IlostatClient().telecharger_indicateur('POP_XWAP_SEX_AGE_NB', 2014, 2016); print(csv[:1000]); print('--- taille:', len(csv), 'caractères ---')"  