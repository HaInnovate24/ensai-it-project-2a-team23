"""Crée (ou réinitialise) un compte administrateur par défaut : admin / admin1234@.

Lancé par ``make admin`` (et par ``make go``). Le script est idempotent : si le
compte ``admin`` existe déjà, son mot de passe est réinitialisé et le rôle
administrateur est garanti. On ne passe pas par ``promouvoir_admin`` (qui exige
déjà un administrateur connecté) : on force le rôle directement via le DAO.
"""

from utils.config import load_environment_variables

NOM_ADMIN = "admin"
MOT_DE_PASSE_ADMIN = "admin1234@"


def main() -> int:
    """Garantit l'existence d'un administrateur admin / admin1234@."""
    load_environment_variables()

    from business_object.enums import Role
    from dao.utilisateur_dao import UtilisateurDao
    from service.authentification_service import AuthentificationService
    from utils import securite

    dao = UtilisateurDao()
    auth = AuthentificationService(utilisateur_dao=dao, securite=securite)

    existant = dao.trouver_par_nom(NOM_ADMIN)
    if existant is None:
        utilisateur = auth.inscrire(NOM_ADMIN, MOT_DE_PASSE_ADMIN)
        print(f"Compte administrateur créé : {NOM_ADMIN}")
    else:
        utilisateur = existant
        utilisateur.mot_de_passe_hash = securite.hacher_mot_de_passe(MOT_DE_PASSE_ADMIN)
        print(f"Compte '{NOM_ADMIN}' déjà présent : mot de passe réinitialisé.")

    # Force le rôle administrateur et réactive le compte si besoin.
    utilisateur.role = Role.ADMIN
    utilisateur.actif = True
    dao.modifier(utilisateur)

    print(f"Administrateur prêt -> identifiant : {NOM_ADMIN} / mot de passe : {MOT_DE_PASSE_ADMIN}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
