"""Tests des outils de sécurité (hachage des mots de passe et jetons)."""

import pytest

from utils import securite


@pytest.fixture(autouse=True)
def configuration_de_test(monkeypatch):
    """Prépare l'environnement de chaque test : clé secrète et hachage rapide."""
    monkeypatch.setenv("JWT_SECRET_KEY", "cle-secrete-de-test")
    monkeypatch.setattr(securite, "ITERATIONS", 1000)  # plus rapide que la vraie valeur


# Hachage des mots de passe


def test_hacher_ne_renvoie_pas_le_mot_de_passe_en_clair():
    """L'empreinte ne contient pas le mot de passe."""
    empreinte = securite.hacher_mot_de_passe("MotDePasse123")

    assert "MotDePasse123" not in empreinte


def test_hacher_format_et_longueur():
    """L'empreinte a 4 parties séparées par $ et tient dans la colonne (256 caractères)."""
    empreinte = securite.hacher_mot_de_passe("MotDePasse123")

    assert len(empreinte.split("$")) == 4
    assert empreinte.startswith("pbkdf2_sha256$")
    assert len(empreinte) < 256


def test_hacher_deux_fois_donne_deux_empreintes_differentes():
    """Le sel aléatoire fait que le même mot de passe donne des empreintes différentes."""
    assert securite.hacher_mot_de_passe("MotDePasse123") != securite.hacher_mot_de_passe(
        "MotDePasse123"
    )


def test_verifier_bon_mot_de_passe():
    """Le bon mot de passe est reconnu."""
    empreinte = securite.hacher_mot_de_passe("MotDePasse123")

    assert securite.verifier_mot_de_passe("MotDePasse123", empreinte) is True


def test_verifier_mauvais_mot_de_passe():
    """Un mauvais mot de passe est refusé (la casse compte)."""
    empreinte = securite.hacher_mot_de_passe("MotDePasse123")

    assert securite.verifier_mot_de_passe("motdepasse123", empreinte) is False


def test_verifier_mot_de_passe_avec_accents():
    """Les caractères accentués fonctionnent."""
    empreinte = securite.hacher_mot_de_passe("Mdp-éàç-123")

    assert securite.verifier_mot_de_passe("Mdp-éàç-123", empreinte) is True


@pytest.mark.parametrize("empreinte_invalide", [None, "", "abc", "a$b$c", "md5$1$00$00", "x$y$z$w"])
def test_verifier_avec_empreinte_invalide(empreinte_invalide):
    """Une empreinte absente ou mal formée donne False, sans erreur."""
    assert securite.verifier_mot_de_passe("MotDePasse123", empreinte_invalide) is False


def test_verifier_utilise_les_iterations_stockees(monkeypatch):
    """Une ancienne empreinte reste valable même si on change ITERATIONS ensuite."""
    empreinte = securite.hacher_mot_de_passe("MotDePasse123")
    monkeypatch.setattr(securite, "ITERATIONS", 2000)

    assert securite.verifier_mot_de_passe("MotDePasse123", empreinte) is True


# Jetons


def test_jeton_aller_retour():
    """Un jeton créé pour l'utilisateur 42 redonne 42."""
    jeton = securite.creer_jeton(42)

    assert securite.lire_jeton(jeton) == 42


def test_jeton_expire():
    """Un jeton dont la durée est déjà dépassée est refusé."""
    jeton = securite.creer_jeton(42, duree_minutes=-1)

    with pytest.raises(ValueError):
        securite.lire_jeton(jeton)


def test_jeton_modifie():
    """Un jeton dont on a changé un caractère est refusé."""
    jeton = securite.creer_jeton(42)
    jeton_modifie = jeton[:-2] + ("AA" if not jeton.endswith("AA") else "BB")

    with pytest.raises(ValueError):
        securite.lire_jeton(jeton_modifie)


def test_jeton_signe_avec_une_autre_cle(monkeypatch):
    """Un jeton signé avec une autre clé secrète est refusé."""
    jeton = securite.creer_jeton(42)
    monkeypatch.setenv("JWT_SECRET_KEY", "une-autre-cle")

    with pytest.raises(ValueError):
        securite.lire_jeton(jeton)


@pytest.mark.parametrize("jeton_invalide", ["", "n-importe-quoi", "a.b.c", None])
def test_jeton_invalide(jeton_invalide):
    """Un texte qui n'est pas un jeton valide lève ValueError."""
    with pytest.raises(ValueError):
        securite.lire_jeton(jeton_invalide)


def test_duree_lue_dans_l_environnement(monkeypatch):
    """Sans durée donnée, JWT_DUREE_MINUTES est utilisé (ici -1 : jeton déjà expiré)."""
    monkeypatch.setenv("JWT_DUREE_MINUTES", "-1")
    jeton = securite.creer_jeton(42)

    with pytest.raises(ValueError):
        securite.lire_jeton(jeton)


def test_cle_secrete_absente(monkeypatch):
    """Sans clé secrète configurée, on lève une RuntimeError explicite."""
    monkeypatch.delenv("JWT_SECRET_KEY")

    with pytest.raises(RuntimeError):
        securite.creer_jeton(42)
