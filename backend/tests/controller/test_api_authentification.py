"""Tests de bout en bout : vraies requêtes HTTP sur les vrais services, avec une fausse base.

On assemble une petite application FastAPI avec les vrais routeurs, le gestionnaire
d'erreurs et les vrais services (AuthentificationService, UtilisateurService,
JournalService) branchés sur des faux DAO. On vérifie ainsi les codes HTTP, les
en-têtes et le contenu des réponses.

Ces tests ont besoin du paquet httpx (utilisé par le client de test FastAPI). S'il
n'est pas installé, ils sont simplement ignorés (au besoin : uv add --project backend --dev httpx)
"""

from datetime import datetime

import pytest

from business_object.enums import Role
from model.analyse_model import Comparaison, PointSerie, ResumeSerie, Serie
from service.authentification_service import AuthentificationService
from service.journal_service import JournalService
from service.utilisateur_service import UtilisateurService

# Faux DAO, fausse sécurité, faux service d'analyse


class FauxUtilisateurDao:
    """Faux DAO d'utilisateurs : comptes gardés dans une liste en mémoire."""

    def __init__(self):
        """Démarre sans aucun compte."""
        self.utilisateurs = []

    def creer(self, utilisateur):
        """Ajoute le compte avec un identifiant et une date de création."""
        utilisateur.id = len(self.utilisateurs) + 1
        utilisateur.date_creation = datetime.now()
        self.utilisateurs.append(utilisateur)
        return utilisateur

    def trouver_par_nom(self, nom_utilisateur):
        """Renvoie le compte portant ce nom, ou None."""
        return next((u for u in self.utilisateurs if u.nom_utilisateur == nom_utilisateur), None)

    def trouver_par_id(self, id):
        """Renvoie le compte portant cet identifiant, ou None."""
        return next((u for u in self.utilisateurs if u.id == id), None)

    def lister(self):
        """Renvoie tous les comptes."""
        return list(self.utilisateurs)

    def modifier(self, utilisateur):
        """Imite la mise à jour en base."""
        return self.trouver_par_id(utilisateur.id) is not None


class FauxJournalDao:
    """Faux DAO du journal : entrées gardées dans une liste en mémoire."""

    def __init__(self):
        """Démarre avec un journal vide."""
        self.entrees = []

    def creer(self, entree):
        """Ajoute l'entrée avec un identifiant et une date."""
        entree.id = len(self.entrees) + 1
        entree.date_heure = datetime.now()
        self.entrees.append(entree)
        return entree

    def lister(self):
        """Renvoie les entrées de la plus récente à la plus ancienne."""
        return list(reversed(self.entrees))


class FausseSecurite:
    """Fausse sécurité : hachage et jetons très simples."""

    def hacher_mot_de_passe(self, mot_de_passe):
        """'Hache' le mot de passe en ajoutant un préfixe."""
        return "hash:" + mot_de_passe

    def verifier_mot_de_passe(self, mot_de_passe, mot_de_passe_hash):
        """Compare le mot de passe avec l'empreinte."""
        return mot_de_passe_hash == "hash:" + mot_de_passe

    def creer_jeton(self, id_utilisateur):
        """Crée un jeton de la forme 'jeton-<id>'."""
        return f"jeton-{id_utilisateur}"

    def lire_jeton(self, jeton):
        """Renvoie l'identifiant d'un jeton 'jeton-<id>', sinon lève ValueError."""
        if not jeton.startswith("jeton-"):
            raise ValueError("Jeton invalide")
        return int(jeton.removeprefix("jeton-"))


class FauxAnalyseService:
    """Faux service d'analyse : il renvoie toujours un résultat fixe."""

    def evolution(self, **arguments):
        """Imite AnalyseService.evolution."""
        return Serie(libelle="Emploi", points=[PointSerie(periode="2024Q1", valeur=1.0)])

    def resumer_evolution(self, **arguments):
        """Imite AnalyseService.resumer_evolution."""
        return ResumeSerie(
            libelle="Emploi",
            nb_points=1,
            periode_debut="2024Q1",
            periode_fin="2024Q1",
            valeur_debut=1.0,
            valeur_fin=1.0,
            minimum=1.0,
            maximum=1.0,
            moyenne=1.0,
            variation_absolue=None,
            variation_relative=None,
        )

    def comparer_pays(self, **arguments):
        """Imite AnalyseService.comparer_pays."""
        return Comparaison(series=[])

    def comparer_indicateurs(self, **arguments):
        """Imite AnalyseService.comparer_indicateurs."""
        return Comparaison(series=[])

    def carte(self, **arguments):
        """Imite AnalyseService.carte."""
        return Comparaison(series=[])


@pytest.fixture
def api():
    """Construit l'application de test et renvoie (client HTTP, DAO des utilisateurs)."""
    pytest.importorskip("httpx")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from controller import admin_comptes_controller, analyse_controller, auth_controller
    from controller.dependances import get_authentification_service
    from controller.erreurs_http import enregistrer_gestionnaires

    dao = FauxUtilisateurDao()
    journal = JournalService(journal_dao=FauxJournalDao())
    authentification = AuthentificationService(utilisateur_dao=dao, securite=FausseSecurite())
    gestion = UtilisateurService(utilisateur_dao=dao, journal_service=journal)

    app = FastAPI()
    enregistrer_gestionnaires(app)
    app.include_router(auth_controller.router, prefix="/auth")
    app.include_router(admin_comptes_controller.router, prefix="/admin")
    app.include_router(analyse_controller.router, prefix="/analyses")
    app.dependency_overrides[get_authentification_service] = lambda: authentification
    app.dependency_overrides[admin_comptes_controller.get_utilisateur_service] = lambda: gestion
    app.dependency_overrides[admin_comptes_controller.get_journal_service] = lambda: journal
    app.dependency_overrides[analyse_controller.get_analyse_service] = FauxAnalyseService
    return TestClient(app), dao


def inscrire_et_connecter(client, nom, mot_de_passe="Motdepasse1"):
    """Inscrit un compte, le connecte et renvoie l'en-tête Authorization à utiliser."""
    client.post("/auth/inscription", json={"nom_utilisateur": nom, "mot_de_passe": mot_de_passe})
    reponse = client.post(
        "/auth/connexion", json={"nom_utilisateur": nom, "mot_de_passe": mot_de_passe}
    )
    return {"Authorization": f"Bearer {reponse.json()['data']}"}


def creer_admin(client, dao, nom="chef"):
    """Crée un compte, le promeut administrateur directement en base, et le connecte."""
    en_tete = inscrire_et_connecter(client, nom)
    dao.trouver_par_nom(nom).role = Role.ADMIN
    return en_tete


# Inscription et connexion


def test_inscription_renvoie_200_sans_mot_de_passe_ni_empreinte(api):
    """Une inscription valide donne 200 et ne renvoie ni mot de passe ni empreinte."""
    client, _ = api

    reponse = client.post(
        "/auth/inscription", json={"nom_utilisateur": "Alice", "mot_de_passe": "Motdepasse1"}
    )

    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "succes"
    corps = reponse.json()["data"]
    assert corps["nom_utilisateur"] == "alice"
    assert corps["role"] == "utilisateur"
    assert corps["actif"] is True
    assert "mot_de_passe_hash" not in corps
    assert "mot_de_passe" not in corps
    assert "hash:" not in reponse.text


def test_inscription_nom_deja_pris_renvoie_409(api):
    """Un nom déjà pris donne 409."""
    client, _ = api
    inscrire_et_connecter(client, "alice")

    reponse = client.post(
        "/auth/inscription", json={"nom_utilisateur": "alice", "mot_de_passe": "Motdepasse1"}
    )

    assert reponse.status_code == 409


def test_inscription_mot_de_passe_trop_faible_renvoie_422(api):
    """Un mot de passe qui ne respecte pas les règles donne 422 avec un message."""
    client, _ = api

    reponse = client.post(
        "/auth/inscription", json={"nom_utilisateur": "alice", "mot_de_passe": "court"}
    )

    assert reponse.status_code == 422
    assert "mot de passe" in reponse.json()["detail"].lower()


def test_inscription_ignore_un_role_envoye(api):
    """Envoyer un champ 'role' à l'inscription ne change rien : le compte reste utilisateur."""
    client, dao = api

    reponse = client.post(
        "/auth/inscription",
        json={"nom_utilisateur": "alice", "mot_de_passe": "Motdepasse1", "role": "admin"},
    )

    assert reponse.status_code == 200
    assert reponse.json()["data"]["role"] == "utilisateur"
    assert dao.trouver_par_nom("alice").role is Role.UTILISATEUR


def test_connexion_renvoie_un_jeton(api):
    """Une connexion réussie donne 200 et un jeton dans le champ data."""
    client, _ = api
    inscrire_et_connecter(client, "alice")

    reponse = client.post(
        "/auth/connexion", json={"nom_utilisateur": "alice", "mot_de_passe": "Motdepasse1"}
    )

    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "succes"
    assert reponse.json()["data"]


def test_connexion_mauvais_mot_de_passe_renvoie_401(api):
    """Un mauvais mot de passe donne 401 avec l'en-tête WWW-Authenticate."""
    client, _ = api
    inscrire_et_connecter(client, "alice")

    reponse = client.post(
        "/auth/connexion", json={"nom_utilisateur": "alice", "mot_de_passe": "Mauvais123"}
    )

    assert reponse.status_code == 401
    assert reponse.headers["www-authenticate"] == "Bearer"


def test_connexion_corps_incomplet_renvoie_422(api):
    """Un corps sans mot de passe est refusé par la validation (422)."""
    client, _ = api

    reponse = client.post("/auth/connexion", json={"nom_utilisateur": "alice"})

    assert reponse.status_code == 422


# Profil et jeton


def test_profil_avec_jeton(api):
    """Avec un jeton valide, /auth/profil renvoie le compte sans empreinte."""
    client, _ = api
    en_tete = inscrire_et_connecter(client, "alice")

    reponse = client.get("/auth/profil", headers=en_tete)

    assert reponse.status_code == 200
    assert reponse.json()["data"]["nom_utilisateur"] == "alice"
    assert "mot_de_passe_hash" not in reponse.json()["data"]
    assert "hash:" not in reponse.text


@pytest.mark.parametrize(
    "en_tete",
    [
        {},
        {"Authorization": "Bearer n-importe-quoi"},
        {"Authorization": "Bearer "},
        {"Authorization": "Basic YWxpY2U6c2VjcmV0"},
    ],
)
def test_profil_sans_jeton_valide_renvoie_401(api, en_tete):
    """Sans en-tête, avec un jeton invalide ou un autre schéma d'authentification : 401."""
    client, _ = api
    inscrire_et_connecter(client, "alice")

    reponse = client.get("/auth/profil", headers=en_tete)

    assert reponse.status_code == 401
    assert reponse.headers["www-authenticate"] == "Bearer"


def test_compte_desactive_renvoie_403_avec_un_jeton_existant(api):
    """Après désactivation par un administrateur, le jeton déjà émis donne 403."""
    client, dao = api
    en_tete_alice = inscrire_et_connecter(client, "alice")
    en_tete_chef = creer_admin(client, dao)

    desactivation = client.patch(
        "/admin/utilisateurs/1/activation", json={"actif": False}, headers=en_tete_chef
    )
    reponse = client.get("/auth/profil", headers=en_tete_alice)

    assert desactivation.status_code == 200
    assert reponse.status_code == 403


# ----------------------------------------------------------------------
# Accès aux analyses : évolution libre, le reste avec connexion
# ----------------------------------------------------------------------


def test_evolution_accessible_sans_connexion(api):
    """L'évolution est en accès libre."""
    client, _ = api

    reponse = client.get("/analyses/evolution", params={"code_indicateur": "E", "code_pays": "FRA"})

    assert reponse.status_code == 200


def test_resume_evolution_accessible_sans_connexion(api):
    """Le résumé de l'évolution (F3) est en accès libre, comme l'évolution."""
    client, _ = api

    reponse = client.get(
        "/analyses/resume-evolution", params={"code_indicateur": "E", "code_pays": "FRA"}
    )

    assert reponse.status_code == 200
    assert reponse.json()["moyenne"] == 1.0
    assert reponse.json()["variation_relative"] is None


def test_comparaison_indicateurs_accepte_base_100(api):
    """Le paramètre base_100 est accepté par la route (avec connexion)."""
    client, _ = api
    en_tete = inscrire_et_connecter(client, "alice")

    reponse = client.get(
        "/analyses/comparaison-indicateurs",
        params={"codes_indicateur": ["E", "T"], "code_pays": "FRA", "base_100": "true"},
        headers=en_tete,
    )

    assert reponse.status_code == 200


@pytest.mark.parametrize(
    ("chemin", "parametres"),
    [
        ("/analyses/comparaison-pays", {"code_indicateur": "E", "codes_pays": ["FRA", "DEU"]}),
        (
            "/analyses/comparaison-indicateurs",
            {"codes_indicateur": ["E", "T"], "code_pays": "FRA"},
        ),
        ("/analyses/carte", {"code_indicateur": "E", "periode": "2024Q1"}),
    ],
)
def test_analyses_reservees_aux_utilisateurs_connectes(api, chemin, parametres):
    """Comparaisons et carte : 401 sans jeton, 200 avec un jeton valide."""
    client, _ = api
    en_tete = inscrire_et_connecter(client, "alice")

    sans_jeton = client.get(chemin, params=parametres)
    avec_jeton = client.get(chemin, params=parametres, headers=en_tete)

    assert sans_jeton.status_code == 401
    assert avec_jeton.status_code == 200


# Administration


@pytest.mark.parametrize(
    ("methode", "chemin", "corps"),
    [
        ("get", "/admin/utilisateurs", None),
        ("patch", "/admin/utilisateurs/1/role", {"role": "admin"}),
        ("patch", "/admin/utilisateurs/1/activation", {"actif": False}),
        ("get", "/admin/journal", None),
    ],
)
def test_administration_refusee_a_un_utilisateur_standard(api, methode, chemin, corps):
    """Un utilisateur standard reçoit 403, sans jeton on reçoit 401."""
    client, _ = api
    en_tete = inscrire_et_connecter(client, "alice")

    avec_standard = getattr(client, methode)(
        chemin, headers=en_tete, **({"json": corps} if corps else {})
    )
    sans_jeton = getattr(client, methode)(chemin, **({"json": corps} if corps else {}))

    assert avec_standard.status_code == 403
    assert sans_jeton.status_code == 401


def test_admin_liste_les_comptes_sans_empreinte(api):
    """Un administrateur liste les comptes, sans aucune empreinte de mot de passe."""
    client, dao = api
    inscrire_et_connecter(client, "alice")
    en_tete = creer_admin(client, dao)

    reponse = client.get("/admin/utilisateurs", headers=en_tete)

    assert reponse.status_code == 200
    assert [u["nom_utilisateur"] for u in reponse.json()] == ["alice", "chef"]
    assert "hash:" not in reponse.text


def test_admin_promeut_puis_retrograde(api):
    """Un administrateur promeut puis rétrograde un compte avec la même route."""
    client, dao = api
    inscrire_et_connecter(client, "alice")
    en_tete = creer_admin(client, dao)

    promotion = client.patch("/admin/utilisateurs/1/role", json={"role": "admin"}, headers=en_tete)
    retrogradation = client.patch(
        "/admin/utilisateurs/1/role", json={"role": "utilisateur"}, headers=en_tete
    )

    assert promotion.status_code == 200
    assert promotion.json()["role"] == "admin"
    assert retrogradation.status_code == 200
    assert retrogradation.json()["role"] == "utilisateur"


def test_admin_changement_de_role_inutile_renvoie_409(api):
    """Promouvoir un compte déjà administrateur donne 409."""
    client, dao = api
    en_tete = creer_admin(client, dao)
    inscrire_et_connecter(client, "dora")
    dao.trouver_par_nom("dora").role = Role.ADMIN

    reponse = client.patch("/admin/utilisateurs/2/role", json={"role": "admin"}, headers=en_tete)

    assert reponse.status_code == 409


def test_admin_compte_inconnu_renvoie_404(api):
    """Agir sur un compte inexistant donne 404."""
    client, dao = api
    en_tete = creer_admin(client, dao)

    reponse = client.patch(
        "/admin/utilisateurs/999/activation", json={"actif": False}, headers=en_tete
    )

    assert reponse.status_code == 404


def test_admin_ne_peut_pas_se_desactiver_lui_meme(api):
    """Un administrateur qui désactive son propre compte reçoit 422."""
    client, dao = api
    en_tete = creer_admin(client, dao)

    reponse = client.patch(
        "/admin/utilisateurs/1/activation", json={"actif": False}, headers=en_tete
    )

    assert reponse.status_code == 422
    assert dao.trouver_par_nom("chef").actif is True


@pytest.mark.parametrize("etat_invalide", ["false", 0, 1, None])
def test_admin_activation_etat_ambigu_renvoie_422(api, etat_invalide):
    """Un état d'activation ambigu (texte, 0, 1, null) est refusé avant d'atteindre le service."""
    client, dao = api
    inscrire_et_connecter(client, "alice")
    en_tete = creer_admin(client, dao)

    reponse = client.patch(
        "/admin/utilisateurs/1/activation", json={"actif": etat_invalide}, headers=en_tete
    )

    assert reponse.status_code == 422
    assert dao.trouver_par_nom("alice").actif is True


def test_admin_consulte_le_journal_apres_une_action(api):
    """Une action d'administration apparaît dans le journal, consultable avec filtres."""
    client, dao = api
    inscrire_et_connecter(client, "alice")
    en_tete = creer_admin(client, dao)
    client.patch("/admin/utilisateurs/1/activation", json={"actif": False}, headers=en_tete)

    reponse = client.get(
        "/admin/journal", params={"action": "DESACTIVATION_COMPTE"}, headers=en_tete
    )

    assert reponse.status_code == 200
    assert len(reponse.json()) == 1
    assert reponse.json()[0]["action"] == "DESACTIVATION_COMPTE"
    assert reponse.json()[0]["cible"] == "utilisateur:1"


def test_admin_journal_limite_invalide_renvoie_422(api):
    """Une limite hors des valeurs autorisées donne 422."""
    client, dao = api
    en_tete = creer_admin(client, dao)

    reponse = client.get("/admin/journal", params={"limite": 0}, headers=en_tete)

    assert reponse.status_code == 422
