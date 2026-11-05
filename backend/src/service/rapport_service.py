"""FO3 : génération des rapports PDF."""

import os
from fpdf import FPDF
from business_object.rapport import Rapport
from business_object.enums import StatutRapport
from dao.rapport_dao import RapportDao

class RapportService:
    """Assemble séries, résumé statistique, graphiques et conclusion dans un PDF."""

    def __init__(self):
        self.dao = RapportDao()
        self.dossier_stockage = "rapports_generes"
        os.makedirs(self.dossier_stockage, exist_ok=True)

    def generer(self, utilisateur_id: int, **parametres) -> Rapport:
        """Génère un rapport PDF à partir des paramètres d'analyse."""
        # 1. Enregistrement initial
        rapport_initial = Rapport(
            utilisateur_id=utilisateur_id,
            titre=parametres.get("titre", "Analyse"),
            description=parametres.get("description", ""),
            statut=StatutRapport.EN_ATTENTE
        )
        rapport = self.dao.creer(rapport_initial)

        # 2. Génération PDF
        nom_fichier = f"rapport_{rapport.id}.pdf"
        chemin_complet = os.path.join(self.dossier_stockage, nom_fichier)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(0, 10, txt=rapport.titre, new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, txt=f"Indicateur : {parametres.get('code_indicateur', 'Non spécifié')}", new_x="LMARGIN", new_y="NEXT")
        if rapport.description:
            pdf.multi_cell(0, 10, txt=rapport.description)
        
        pdf.output(chemin_complet)

        # 3. Mise à jour de la base de données
        rapport.fichier_path = chemin_complet
        rapport.statut = StatutRapport.PRET
        self.dao.mettre_a_jour(rapport)

        return rapport

    def lister(self, utilisateur_id: int) -> list[Rapport]:
        """Renvoie les rapports d'un utilisateur."""
        return self.dao.lister(utilisateur_id)

    def trouver_par_id(self, rapport_id: int) -> Rapport | None:
        """Renvoie le rapport correspondant à l'ID, ou None s'il n'existe pas."""
        return self.dao.trouver_par_id(rapport_id)

    def telecharger(self, rapport_id: int) -> bytes:
        """Renvoie le contenu binaire du PDF d'un rapport."""
        rapport = self.dao.trouver_par_id(rapport_id)
        if not rapport or not rapport.fichier_path or not os.path.exists(rapport.fichier_path):
            raise FileNotFoundError("PDF introuvable.")
            
        with open(rapport.fichier_path, "rb") as fichier:
            return fichier.read()