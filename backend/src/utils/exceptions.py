"""Erreurs métier communes à l'application."""


class ErreurMetier(Exception):
    """Classe de base des erreurs métier."""


class RessourceIntrouvable(ErreurMetier):
    """Levée lorsqu'une ressource demandée n'existe pas."""


class DonneesInvalides(ErreurMetier):
    """Levée lorsqu'une donnée fournie ne respecte pas les règles métier."""


class AccesRefuse(ErreurMetier):
    """Levée lorsqu'un utilisateur n'a pas les droits requis."""
