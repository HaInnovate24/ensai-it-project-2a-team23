import os
import pytest

from business_object.rapport import Rapport
from business_object.enums import StatutRapport
from service.rapport_service import RapportService

class FauxRapportDao:
    def __init__(self):
        self.rapports = {}
        self.id_counter = 1

    def creer(self, rapport):
        rapport.id = self.id_counter
        self.rapports[rapport.id] = rapport
        self.id_counter += 1
        return rapport

    def mettre_a_jour(self, rapport):
        self.rapports[rapport.id] = rapport

    def lister(self, utilisateur_id):
        return [r for r in self.rapports.values() if r.utilisateur_id == utilisateur_id]

    def trouver_par_id(self, rapport_id):
        return self.rapports.get(rapport_id)


def creer_service(tmp_path):
    """
    Crée un service avec un faux DAO et un dossier temporaire.
    On utilise __new__ pour contourner le __init__ et ne pas taper la vraie BDD.
    """
    service = RapportService.__new__(RapportService)
    service.dao = FauxRapportDao()
    # Utilisation d'un dossier temporaire fourni par pytest pour éviter de 
    # polluer le vrai projet avec des PDF de test.
    service.dossier_stockage = str(tmp_path)
    os.makedirs(service.dossier_stockage, exist_ok=True)
    return service


def test_generer_rapport(tmp_path):
    service = creer_service(tmp_path)
    
    rapport = service.generer(
        utilisateur_id=1,
        titre="Analyse de test",
        description="Ceci est un test",
        code_indicateur="EMP_TEMP"
    )
    
    assert rapport.id == 1
    assert rapport.titre == "Analyse de test"
    assert rapport.description == "Ceci est un test"
    assert rapport.statut == StatutRapport.PRET
    assert rapport.fichier_path.endswith(f"rapport_{rapport.id}.pdf")
    # Vérifie que le fichier physique a bien été créé
    assert os.path.exists(rapport.fichier_path)


def test_lister(tmp_path):
    service = creer_service(tmp_path)
    service.generer(utilisateur_id=1, titre="Rapport A")
    service.generer(utilisateur_id=1, titre="Rapport B")
    service.generer(utilisateur_id=2, titre="Rapport C")
    
    rapports_u1 = service.lister(1)
    assert len(rapports_u1) == 2
    assert rapports_u1[0].titre == "Rapport A"


def test_trouver_par_id(tmp_path):
    service = creer_service(tmp_path)
    rapport = service.generer(utilisateur_id=1)
    
    trouve = service.trouver_par_id(rapport.id)
    assert trouve is not None
    assert trouve.id == rapport.id
    
    assert service.trouver_par_id(999) is None


def test_telecharger(tmp_path):
    service = creer_service(tmp_path)
    rapport = service.generer(utilisateur_id=1)
    
    contenu = service.telecharger(rapport.id)
    
    assert isinstance(contenu, bytes)
    assert len(contenu) > 0
    # On vérifie la signature magique d'un fichier PDF (qui commence toujours par %PDF-)
    assert contenu.startswith(b"%PDF-")


def test_telecharger_echoue_si_introuvable(tmp_path):
    service = creer_service(tmp_path)
    
    # Cas 1 : Le rapport n'existe pas en base
    with pytest.raises(FileNotFoundError, match="PDF introuvable."):
        service.telecharger(999)
        
    # Cas 2 : Le rapport existe, mais le fichier PDF a été supprimé physiquement du disque
    rapport = service.generer(utilisateur_id=1)
    os.remove(rapport.fichier_path)
    
    with pytest.raises(FileNotFoundError, match="PDF introuvable."):
        service.telecharger(rapport.id)