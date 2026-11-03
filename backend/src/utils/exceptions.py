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
    """Levée lorsqu'une authentification échoue (identifiants ou jeton invalides)."""


class ConflitRessource(ErreurMetier):
    """Levée lorsqu'une ressource entre en conflit avec une autre (ex. nom déjà pris)."""
