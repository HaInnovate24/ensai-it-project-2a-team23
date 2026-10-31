"""Client HTTP vers l'API ILOSTAT avec archivage local des CSV."""

import csv
import os
import re
import tempfile
from io import StringIO
from pathlib import Path

import requests


class IlostatClient:
    """Télécharge et archive les périodes d'un indicateur ILOSTAT."""

    BASE_URL = "https://rplumber.ilo.org/data/indicator"
    TIMEOUT_SECONDS = 60
    DATA_DIRECTORY = Path(__file__).resolve().parent / "data"
    CODE_INDICATEUR_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
    FICHIER_PATTERN = re.compile(r"(.+)_(\d{4})_(\d{4})\.csv")

    @classmethod
    def _valider_code_indicateur(cls, code_indicateur: str) -> str:
        """Valide le code pour éviter qu'il ne sorte du dossier de cache."""
        code = code_indicateur.strip() if code_indicateur else ""
        if not cls.CODE_INDICATEUR_PATTERN.fullmatch(code):
            raise ValueError("Le code de l'indicateur est invalide.")
        return code

    def _lister_fichiers_archive(self, code_indicateur: str) -> list[tuple[int, int, Path]]:
        repertoire = self.DATA_DIRECTORY / code_indicateur
        if not repertoire.is_dir():
            return []

        fichiers = []
        for chemin in repertoire.iterdir():
            correspondance = self.FICHIER_PATTERN.fullmatch(chemin.name)
            if (
                correspondance is None
                or correspondance.group(1) != code_indicateur
                or not chemin.is_file()
            ):
                continue
            debut, fin = int(correspondance.group(2)), int(correspondance.group(3))
            fichiers.append((debut, fin, chemin))
        return fichiers

    def lister_annees_telechargees(
        self, code_indicateur: str, from_date: int, to_date: int
    ) -> set[int]:
        """Déduit les années téléchargées des plages présentes dans les noms de fichiers."""
        code = self._valider_code_indicateur(code_indicateur)
        annees: set[int] = set()
        for debut, fin, _ in self._lister_fichiers_archive(code):
            if debut <= fin:
                annees.update(range(max(debut, from_date), min(fin, to_date) + 1))
        return annees

    def telecharger_indicateur(
        self,
        code_indicateur: str,
        from_date: int = 2014,
        to_date: int = 2026,
    ) -> str:
        """Complète l'archive d'une période et renvoie son CSV consolidé.

        Les années déjà couvertes par des fichiers du cache ne sont pas redemandées
        à ILOSTAT. Chaque plage contiguë manquante est téléchargée dans son propre
        fichier `{indicateur}_{début}_{fin}.csv`.
        """
        code = self._valider_code_indicateur(code_indicateur)
        if from_date > to_date:
            raise ValueError(
                "L'année de début (from_date) doit être inférieure ou égale à l'année de fin (to_date)."
            )

        annees_existantes = self.lister_annees_telechargees(code, from_date, to_date)
        annees_manquantes = [
            annee
            for annee in range(from_date, to_date + 1)
            if annee not in annees_existantes
        ]
        for debut, fin in self._regrouper_annees_consecutives(annees_manquantes):
            self._telecharger_plage(code, debut, fin)

        return self._lire_csv_archive(code, from_date, to_date)

    def _telecharger_plage(self, code_indicateur: str, from_date: int, to_date: int) -> Path:
        repertoire = self.DATA_DIRECTORY / code_indicateur
        fichier_csv = repertoire / f"{code_indicateur}_{from_date}_{to_date}.csv"
        if fichier_csv.is_file():
            return fichier_csv

        params: dict[str, str | int] = {
            "id": code_indicateur,
            "timefrom": from_date,
            "timeto": to_date,
            "type": "code",
            "format": ".csv",
        }
        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=self.TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        os.makedirs(os.fspath(repertoire), exist_ok=True)
        descripteur, chemin_temporaire = tempfile.mkstemp(
            dir=os.fspath(repertoire), prefix=f".{fichier_csv.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(descripteur, "w", encoding="utf-8", newline="") as fichier:
                fichier.write(response.text)
            os.replace(chemin_temporaire, fichier_csv)
        except Exception:
            if os.path.exists(chemin_temporaire):
                os.remove(chemin_temporaire)
            raise
        return fichier_csv

    def _lire_csv_archive(self, code_indicateur: str, from_date: int, to_date: int) -> str:
        fichiers = [
            chemin
            for debut, fin, chemin in self._lister_fichiers_archive(code_indicateur)
            if debut <= to_date and fin >= from_date
        ]
        colonnes: list[str] | None = None
        lignes: dict[tuple[str, ...], dict[str, str]] = {}

        for chemin in sorted(fichiers):
            with chemin.open(encoding="utf-8", newline="") as fichier:
                lecteur = csv.DictReader(fichier)
                if lecteur.fieldnames is None:
                    continue
                if colonnes is None:
                    colonnes = lecteur.fieldnames
                if lecteur.fieldnames != colonnes:
                    raise ValueError(f"Les colonnes du fichier {chemin.name} diffèrent du cache.")

                for ligne in lecteur:
                    periode = ligne.get("time", "")
                    annee_match = re.match(r"^(\d{4})", periode)
                    if annee_match is not None:
                        annee = int(annee_match.group(1))
                        if not from_date <= annee <= to_date:
                            continue
                    cle = tuple(ligne.get(colonne, "") or "" for colonne in colonnes)
                    lignes[cle] = ligne

        if colonnes is None:
            return ""

        sortie = StringIO(newline="")
        redacteur = csv.DictWriter(sortie, fieldnames=colonnes, lineterminator="\n")
        redacteur.writeheader()
        redacteur.writerows(lignes.values())
        return sortie.getvalue()

    @staticmethod
    def _regrouper_annees_consecutives(annees: list[int]) -> list[tuple[int, int]]:
        """Réunit les années manquantes en plages contiguës."""
        if not annees:
            return []

        plages = []
        debut = precedent = annees[0]
        for annee in annees[1:]:
            if annee != precedent + 1:
                plages.append((debut, precedent))
                debut = annee
            precedent = annee
        plages.append((debut, precedent))
        return plages
