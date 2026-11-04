"""Génération des graphiques insérés dans les rapports PDF."""

import io

import matplotlib

matplotlib.use("Agg")  # backend non-interactive, indispensable hors écran

import matplotlib.pyplot as plt

from model.analyse_model import Serie


class Graphiques:
    """Trace les courbes et barres destinées aux rapports."""

    def courbe(self, serie: Serie) -> bytes:
        """Trace une courbe à partir d'une série et renvoie l'image."""
        periodes = [point.periode for point in serie.points]
        valeurs = [point.valeur for point in serie.points]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(periodes, valeurs, marker="o", linewidth=1.5)
        ax.set_title(serie.libelle)
        ax.set_xlabel("Période")
        ax.set_ylabel("Valeur")
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()

        tampon = io.BytesIO() #Fichier en mémoire RAM, comme si on écrit une image sur un fichier
        fig.savefig(tampon, format="png", dpi=150) #On écrit l'image généré dans le tampon
        plt.close(fig)

        return tampon.getvalue() #On récupère les bytes bruts de l'image

    def barres(self, donnees: list[Serie]) -> bytes:
        """Trace un diagramme en barres et renvoie l'image.

        Chaque série représente un groupe (ex. un pays). Les points de chaque
        série sont positionnés côte à côte pour permettre la comparaison.
        """
        if not donnees:
            raise ValueError("Aucune série fournie pour le diagramme en barres.")

        fig, ax = plt.subplots(figsize=(8, 4))

        largeur_barre = 0.8 / max(len(donnees), 1)

        for i, serie in enumerate(donnees):
            periodes = [point.periode for point in serie.points]
            valeurs = [point.valeur for point in serie.points]
            positions = [j + i * largeur_barre for j in range(len(periodes))]
            ax.bar(
                positions,
                valeurs,
                width=largeur_barre,
                label=serie.libelle,
            ) #On calcule les positions de chaque série correspondant à une barre

        if donnees[0].points:
            ax.set_xticks(
                [j + (len(donnees) - 1) * largeur_barre / 2 for j in range(len(donnees[0].points))]
            ) #permet de placer la marque sous la barre de chaque pays
            ax.set_xticklabels([p.periode for p in donnees[0].points], rotation=45) #affichage des libellés à 45°
        ax.set_ylabel("Valeur")
        ax.legend()
        fig.tight_layout()

        tampon = io.BytesIO()
        fig.savefig(tampon, format="png", dpi=150)
        plt.close(fig)

        return tampon.getvalue()
