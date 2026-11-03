"""Erreurs métier communes à l'application."""


class ErreurMetier(Exception):
    """Classe de base des erreurs métier."""


class RessourceIntrouvable(ErreurMetier):
    """Levée lorsqu'une ressource demandée n'existe pas."""


class DonneesInvalides(ErreurMetier):
    """Levée lorsqu'une donnée fournie ne respecte pas les règles métier."""


class AccesRefuse(ErreurMetier):
    """Levée lorsqu'un utilisateur n'a pas les droits requis."""


class AuthentificationEchouee(ErreurMetier):
    """Lévée lorsque l'identité de l'utilisateur n'est pas établie

    Exemple : mauvais identifiants, jeton absent, invalide ou expiré.
    """


class ConflitRessource(ErreurMetier):
    """Levée lorsqu'une ressource existe déjà (ex. nom d'utilisateur déjà pris)."""
