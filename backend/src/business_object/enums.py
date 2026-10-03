"""Énumérations partagées par les objets métier (rôles, sexe, statuts)."""

from enum import Enum


class Role(str, Enum):
    """Rôle d'un utilisateur : accès standard ou administration."""

    UTILISATEUR = "utilisateur"
    ADMIN = "admin"


class Sexe(str, Enum):
    """Sexe associé à une observation (colonne de la table observation)."""

    HOMME = "homme"
    FEMME = "femme"
    TOTAL = "total"


class TypeClassification(str, Enum):
    """Type d'une classification : tranche d'âge ou catégorie d'occupation."""

    AGE = "age"
    OCCUPATION = "occupation"


class StatutImport(str, Enum):
    """Statut d'un import de données ILOSTAT."""

    EN_COURS = "en_cours"
    SUCCES = "succes"
    ECHEC = "echec"


class StatutRapport(str, Enum):
    """Statut de génération d'un rapport PDF."""

    EN_ATTENTE = "en_attente"
    PRET = "pret"
    ECHEC = "echec"
