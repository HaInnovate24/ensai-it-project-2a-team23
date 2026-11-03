"""Outils de sécurité : hachage des mots de passe et jetons de connexion (JWT).

Variables d'environnement qu'on doit définir dans le fichier .env :
    JWT_SECRET_KEY : clé secrète servant à signer les jetons (longue et aléatoire).
    JWT_DUREE_MINUTES : durée de validité d'un jeton en minutes (facultatif, 60 par défaut).
"""

import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta

import jwt

# Nombre de tours de calcul du hachage : plus il est grand, plus un pirate est ralenti.
ITERATIONS = 600_000
ALGORITHME_HACHAGE = "pbkdf2_sha256"
ALGORITHME_JETON = "HS256"
DUREE_JETON_PAR_DEFAUT = 60


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Transforme un mot de passe en empreinte qu'on peut stocker en base.

    Un "sel" aléatoire est ajouté de telle sorte que deux mêmes mots de passe donnent deux empreintes
    différentes. Format renvoyé : algorithme$iterations$sel$empreinte (en hexadécimal).
    """
    sel = secrets.token_bytes(16)
    empreinte = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode("utf-8"), sel, ITERATIONS)
    return f"{ALGORITHME_HACHAGE}${ITERATIONS}${sel.hex()}${empreinte.hex()}"


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    """Indique si le mot de passe correspond à l'empreinte stockée.

    Renvoie False (sans erreur) si l'empreinte est absente ou mal formée.
    """
    try:
        algorithme, iterations, sel_hex, empreinte_hex = mot_de_passe_hash.split("$")
        if algorithme != ALGORITHME_HACHAGE:
            return False
        empreinte_calculee = hashlib.pbkdf2_hmac(
            "sha256", mot_de_passe.encode("utf-8"), bytes.fromhex(sel_hex), int(iterations)
        )
        # compare_digest évite de révéler la réponse par le temps de calcul.
        return hmac.compare_digest(empreinte_calculee, bytes.fromhex(empreinte_hex))
    except (AttributeError, ValueError):
        return False


def creer_jeton(id_utilisateur: int, duree_minutes: int | None = None) -> str:
    """Crée un jeton signé contenant l'identifiant de l'utilisateur et une date d'expiration."""
    if duree_minutes is None:
        duree_minutes = int(os.getenv("JWT_DUREE_MINUTES", str(DUREE_JETON_PAR_DEFAUT)))
    maintenant = datetime.now(UTC)
    contenu = {
        "sub": str(id_utilisateur),
        "iat": maintenant,
        "exp": maintenant + timedelta(minutes=duree_minutes),
    }
    return jwt.encode(contenu, _cle_secrete(), algorithm=ALGORITHME_JETON)


def lire_jeton(jeton: str) -> int:
    """Renvoie l'identifiant de l'utilisateur contenu dans le jeton.

    Lève ValueError si le jeton est invalide, modifié ou expiré.
    """
    try:
        contenu = jwt.decode(jeton, _cle_secrete(), algorithms=[ALGORITHME_JETON])
        return int(contenu["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as erreur:
        raise ValueError("Jeton invalide ou expiré.") from erreur


def _cle_secrete() -> str:
    """Lit la clé secrète dans l'environnement ; lève RuntimeError si elle est absente."""
    cle = os.getenv("JWT_SECRET_KEY")
    if not cle:
        raise RuntimeError("La variable d'environnement JWT_SECRET_KEY n'est pas définie (.env).")
    return cle






""" import hashlib

from fastapi import Header, HTTPException


def hash_password(password: str, salt: str = "") -> str: """
"""Hashes a password using the SHA-256 algorithm.
    Args:
        password (str): The plain text password to be hashed.
        salt (str, optional): A string added to the password before hashing
            to protect against rainbow table attacks.
    Returns:
        str: The resulting hexadecimal hash string.
    """
    """ password_bytes = password.encode("utf-8") + salt.encode("utf-8")
    hash_object = hashlib.sha256(password_bytes)
    return hash_object.hexdigest()


def verify_token(x_auth_token=Header(None)): """
    """Verifies the authenticity of a player via the provided auth token.

    This function checks if a token is present in the request headers and
    validates it against the database.
    Args:
        x_auth_token (str, optional): The token extracted from the
            'X-Auth-Token' HTTP header. Defaults to None.
    Returns:
        Player object associated with the valid token.
    Raises:
        HTTPException: 401 error if the token is missing.
        HTTPException: 401 error if the token is not found in the database.
    """
    """ if not x_auth_token:
        raise HTTPException(status_code=401, detail="Missing token.")
 """
    # player = PlayerDao().find_by_token(x_auth_token)
    # if not player:
    #     raise HTTPException(status_code=401, detail="Invalid token.")

    # return player
