
from service.data_service import get_data_from_ilo_for_one_indicator

if __name__ == "__main__":
    print("Lancement du programme principal...")
    data = get_data_from_ilo_for_one_indicator()
    
    print("Fin du script.")
