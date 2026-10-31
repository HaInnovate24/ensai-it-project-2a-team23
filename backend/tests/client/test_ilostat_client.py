from unittest.mock import Mock

import pytest

from client.ilostat_client import IlostatClient


CSV_EXEMPLE = "ref_area,time,sex,obs_value\nFRA,2020,SEX_T,12.5\n"


def test_telecharger_indicateur_enregistre_le_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(IlostatClient, "DATA_DIRECTORY", tmp_path)
    requete = Mock(return_value=Mock(text=CSV_EXEMPLE))
    monkeypatch.setattr("client.ilostat_client.requests.get", requete)

    resultat = IlostatClient().telecharger_indicateur("TEST_INDICATOR", 2020, 2021)

    chemin = tmp_path / "TEST_INDICATOR" / "TEST_INDICATOR_2020_2021.csv"
    assert resultat == CSV_EXEMPLE
    assert chemin.read_text(encoding="utf-8") == CSV_EXEMPLE
    requete.assert_called_once_with(
        IlostatClient.BASE_URL,
        params={
            "id": "TEST_INDICATOR",
            "timefrom": 2020,
            "timeto": 2021,
            "type": "code",
            "format": ".csv",
        },
        timeout=IlostatClient.TIMEOUT_SECONDS,
    )
    requete.return_value.raise_for_status.assert_called_once_with()


def test_telecharger_indicateur_reutilise_le_fichier_exact(monkeypatch, tmp_path):
    monkeypatch.setattr(IlostatClient, "DATA_DIRECTORY", tmp_path)
    repertoire = tmp_path / "TEST_INDICATOR"
    repertoire.mkdir()
    (repertoire / "TEST_INDICATOR_2020_2021.csv").write_text(
        CSV_EXEMPLE, encoding="utf-8"
    )
    requete = Mock()
    monkeypatch.setattr("client.ilostat_client.requests.get", requete)

    resultat = IlostatClient().telecharger_indicateur("TEST_INDICATOR", 2020, 2021)

    assert resultat == CSV_EXEMPLE
    requete.assert_not_called()


def test_lister_annees_telechargees_reconnait_les_plages_et_limites_les_annees(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(IlostatClient, "DATA_DIRECTORY", tmp_path)
    repertoire = tmp_path / "TEST_INDICATOR"
    repertoire.mkdir()
    (repertoire / "TEST_INDICATOR_2014_2020.csv").touch()
    (repertoire / "TEST_INDICATOR_2022_2023.csv").touch()
    (repertoire / "AUTRE_INDICATOR_2016_2018.csv").touch()
    (repertoire / "TEST_INDICATOR_invalide.csv").touch()

    annees = IlostatClient().lister_annees_telechargees("TEST_INDICATOR", 2016, 2022)

    assert annees == {2016, 2017, 2018, 2019, 2020, 2022}


def test_telecharger_indicateur_ne_telecharge_que_les_plages_manquantes(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(IlostatClient, "DATA_DIRECTORY", tmp_path)
    repertoire = tmp_path / "TEST_INDICATOR"
    repertoire.mkdir()
    lignes_archivees = ["ref_area,time,sex,obs_value"]
    lignes_archivees.extend(f"FRA,{annee},SEX_T,{annee}.0" for annee in range(2020, 2023))
    (repertoire / "TEST_INDICATOR_2020_2022.csv").write_text(
        "\n".join(lignes_archivees) + "\n", encoding="utf-8"
    )

    def repondre(url, params, timeout):
        annees = range(params["timefrom"], params["timeto"] + 1)
        lignes = ["ref_area,time,sex,obs_value"]
        lignes.extend(f"FRA,{annee},SEX_T,{annee}.0" for annee in annees)
        return Mock(text="\n".join(lignes) + "\n")

    requete = Mock(side_effect=repondre)
    monkeypatch.setattr("client.ilostat_client.requests.get", requete)
    client = IlostatClient()

    resultat = client.telecharger_indicateur("TEST_INDICATOR", 2018, 2023)

    assert requete.call_count == 2
    assert [appel.kwargs["params"]["timefrom"] for appel in requete.call_args_list] == [
        2018,
        2023,
    ]
    assert [appel.kwargs["params"]["timeto"] for appel in requete.call_args_list] == [
        2019,
        2023,
    ]
    assert (repertoire / "TEST_INDICATOR_2018_2019.csv").is_file()
    assert (repertoire / "TEST_INDICATOR_2023_2023.csv").is_file()
    assert not (repertoire / "TEST_INDICATOR_2018_2023.csv").exists()
    assert {f"FRA,{annee},SEX_T,{annee}.0" for annee in range(2018, 2024)} <= set(
        resultat.splitlines()
    )


def test_telecharger_indicateur_ne_refait_aucun_appel_quand_tout_est_archive(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(IlostatClient, "DATA_DIRECTORY", tmp_path)
    repertoire = tmp_path / "TEST_INDICATOR"
    repertoire.mkdir()
    for debut, fin in ((2018, 2019), (2020, 2022), (2023, 2023)):
        lignes = ["ref_area,time,sex,obs_value"]
        lignes.extend(f"FRA,{annee},SEX_T,{annee}.0" for annee in range(debut, fin + 1))
        (repertoire / f"TEST_INDICATOR_{debut}_{fin}.csv").write_text(
            "\n".join(lignes) + "\n", encoding="utf-8"
        )
    requete = Mock()
    monkeypatch.setattr("client.ilostat_client.requests.get", requete)

    resultat = IlostatClient().telecharger_indicateur("TEST_INDICATOR", 2018, 2023)

    requete.assert_not_called()
    assert {f"FRA,{annee},SEX_T,{annee}.0" for annee in range(2018, 2024)} <= set(
        resultat.splitlines()
    )


@pytest.mark.parametrize("code", ["../AUTRE", "", "TEST/INDICATOR"])
def test_code_indicateur_invalide_est_refuse_sans_requete(code, monkeypatch):
    requete = Mock()
    monkeypatch.setattr("client.ilostat_client.requests.get", requete)

    with pytest.raises(ValueError):
        IlostatClient().telecharger_indicateur(code, 2020, 2021)

    requete.assert_not_called()


def test_periode_invalide_est_refuse(monkeypatch, tmp_path):
    monkeypatch.setattr(IlostatClient, "DATA_DIRECTORY", tmp_path)
    requete = Mock()
    monkeypatch.setattr("client.ilostat_client.requests.get", requete)

    with pytest.raises(ValueError):
        IlostatClient().telecharger_indicateur("TEST_INDICATOR", 2021, 2020)

    requete.assert_not_called()
