# Bilan du projet LaborScope — par fonctionnalité

> Inspection du 2026-10-31 (branche `salim/architecture`).
> Pour chaque fonctionnalité : **chaîne technique** (contrôleur → service → DAO → frontend),
> **état**, **plan de vérification** (cases à cocher) et **reste à faire**.
> Commandes à lancer **depuis la racine**. Pré-requis vérifs HTTP : `make init` puis `make run-back`.

## Tableau récapitulatif

| Fonctionnalité | API (back) | Service | DAO | Frontend | État |
|----------------|-----------|---------|-----|----------|------|
| **F1/F2 — Collecte & parsing** | ✅ | ✅ | ✅ | n/a | **Terminé** |
| **Référentiels** (pays/indic./classif.) | 🟡 | 🟡 | ✅ | ❌ maquette | Partiel |
| **F3 — Analyse temporelle** | ✅ | 🟡 helpers manquants | ✅ | ❌ maquette | Partiel |
| **F4 — Comparaison pays** | ✅ | 🟡 helpers manquants | ✅ | ❌ maquette | Partiel |
| **F5 — Comparaison indicateurs** | ✅ | 🟡 helpers manquants | ✅ | ❌ maquette | Partiel |
| **FO2 — Cartographie** | ✅ | 🟡 helpers manquants | ✅ | ❌ absente | Partiel |
| **Authentification** | ❌ | ❌ | ✅ | ❌ factice | À faire |
| **F6 — Administration** | ❌ (sauf import) | ❌ | ✅ | ❌ maquette | À faire |
| **FO3 — Rapport PDF** | ❌ | ❌ | ✅ | ❌ absent | À faire |
| **Collecte périodique** | n/a | ❌ planificateur | n/a | n/a | À faire |

✅ fait · 🟡 partiel · ❌ stub `...` ou maquette.

---

## F1/F2 — Collecte & parsing ILOSTAT ✅ **TERMINÉ**

**Chaîne** : `POST /admin/imports/{indicateur}` → `collecte_service` → `ilostat_client` + `parser_service` → `observation_dao` → table `observation`.

**Fait** : téléchargement ILOSTAT avec cache fichier, parsing CSV robuste, upsert idempotent, repeuplement depuis le cache après reset, traçabilité (`import_donnees`).

**Vérifier :**
- [ ] `make test-collecte` → **13 passed**
- [ ] `make cov-collecte` → `collecte_service ~68%`, `parser_service ~82%`
- [ ] Import réel : `POST /admin/imports/POP_XWAP_SEX_AGE_NB?from_date=2025&to_date=2026` → `{"statut":"succes","lignes_inserees": N>0}`
- [ ] Idempotence : relancer → `count(*)` de `observation` inchangé
- [ ] Reset : `make db-reset` puis réimport → réinsère depuis le CSV
- [ ] Intégrité FK : la requête de contrôle (§ Annexe) ne renvoie rien

**Reste :** — (éventuellement augmenter la couverture).

---

## Référentiels (pays / indicateurs / classifications) 🟡 PARTIEL

**Chaîne** : `GET /referentiels/*` → `referentiel_service` → `pays_dao` / `indicateur_dao` / `classification_dao`.

**Fait :** `lister_pays` (service + route). DAOs tous complets.

**Vérifier :**
- [ ] `cd backend && uv run pytest tests/test_referentiel_service.py tests/test_referentiel_controller.py -o addopts="-q"` → vert
- [ ] `GET /referentiels/pays` → 254 pays en JSON

**Reste :**
- [ ] `referentiel_service.lister_indicateurs` (via `indicateur_dao.lister`)
- [ ] `referentiel_service.lister_classifications` (via `classification_dao.lister`)
- [ ] `referentiel_controller.lister_indicateurs` → route `GET /referentiels/indicateurs`

---

## F3 — Analyse temporelle (évolution) 🟡 PARTIEL

**Chaîne** : `GET /analyses/evolution` → `analyse_service.evolution` → `observation_dao.lire_serie`.

**Fait :** route câblée (✅ testée), méthode publique `evolution` écrite.
**Bloqué par :** les helpers privés de `AnalyseService` n'existent pas → la route plante en réel et les tests échouent.

**Vérifier :**
- [ ] `cd backend && uv run pytest tests/test_analyse_controller.py -o addopts="-q"` → vert (le contrôleur simule le service)
- [ ] Après §« Helpers » ci-dessous : `GET /analyses/evolution?code_indicateur=...&code_pays=FRA` → une série JSON

**Reste :** voir le chantier **Helpers `AnalyseService`** (commun à F3/F4/F5/FO2) plus bas.

---

## F4 — Comparaison entre pays 🟡 PARTIEL

**Chaîne** : `GET /analyses/comparaison-pays` → `analyse_service.comparer_pays` → `observation_dao`.

**Fait :** route câblée, méthode publique `comparer_pays` écrite (tri décroissant, période par défaut = la plus récente).
**Bloqué par :** helpers privés manquants.

**Vérifier :**
- [ ] Les tests `test_comparer_pays_*` de `test_analyse_service.py` passent une fois les helpers écrits
- [ ] `GET /analyses/comparaison-pays?code_indicateur=...&codes_pays=FRA&codes_pays=DEU` → séries triées

**Reste :** chantier Helpers + brancher `# TODO : exiger la connexion` (ligne 71).

---

## F5 — Comparaison multi-indicateurs 🟡 PARTIEL

**Chaîne** : `GET /analyses/comparaison-indicateurs` → `analyse_service.comparer_indicateurs` → `observation_dao`.

**Fait :** route câblée, méthode publique écrite (unité dans le libellé, indicateur sans donnée ignoré).
**Bloqué par :** helpers privés manquants.

**Vérifier :**
- [ ] Les tests `test_comparer_indicateurs_*` passent après les helpers
- [ ] `GET /analyses/comparaison-indicateurs?codes_indicateur=A&codes_indicateur=B&code_pays=FRA`

**Reste :** chantier Helpers + brancher `# TODO : exiger la connexion` (ligne 93).

---

## FO2 — Cartographie 🟡 PARTIEL

**Chaîne** : `GET /analyses/carte` → `analyse_service.carte` → `observation_dao.lire_par_periode`.

**Fait :** route câblée, méthode publique `carte` écrite (une valeur par pays, tri par nom).
**Bloqué par :** helpers privés manquants. **Frontend : page carte inexistante.**

**Vérifier :**
- [ ] Les tests `test_carte_*` passent après les helpers
- [ ] `GET /analyses/carte?code_indicateur=...&periode=2025`

**Reste :** chantier Helpers + brancher `# TODO` (ligne 114) + créer la page frontend carte.

---

### 🔴 Chantier transverse F3/F4/F5/FO2 — Helpers de `AnalyseService`

`backend/src/service/analyse_service.py` : méthodes publiques OK, **~10 helpers privés à écrire** (débloque **39 tests**) :
`_sexe_ou_defaut`, `_trouver_indicateur`, `_trouver_pays`, `_verifier_classification`,
`_lire_serie_filtree`, `_lire_periode_filtree`, `_derniere_observation_par_pays`,
`_vers_points`, `_libelle_indicateur`, `_sans_doublons`.
**Critère de fin :** `cd backend && uv run pytest tests/test_analyse_service.py` → 39 verts.

---

## Authentification ❌ À FAIRE

**Chaîne** : `POST /auth/connexion` · `/auth/inscription` · `GET /auth/moi` → `authentification_service` / `utilisateur_service` → `utilisateur_dao` (✅).

**Fait :** `utilisateur_dao` complet, `hash_password` (✅).
**Reste :**
- [ ] `authentification_service` : `se_connecter`, `utilisateur_courant`, `verifier_role`
- [ ] `utilisateur_service` : `inscrire`, `promouvoir_admin`, `desactiver`
- [ ] `auth_controller` : `inscription`, `connexion`, `profil_courant`
- [ ] `controller/dependances` : `utilisateur_courant`, `exiger_connexion`, `exiger_admin`
- [ ] Remplacer `utils/securite.verify_token` (reliquat `PlayerDao` du template)
- [ ] Frontend `login.py` : vrai `POST /auth/connexion` (actuellement boutons factices)

---

## F6 — Administration ❌ À FAIRE (sauf import)

**Chaîne** : `/admin/*` → `donnees_service` / `journal_service` / `utilisateur_service` → DAOs (✅).

**Fait :** seule la route `lancer_import` (`POST /admin/imports/{id}`) fonctionne (cf. F1/F2).
**Reste :**
- [ ] `donnees_service` : `rechercher`, `corriger`, `supprimer`
- [ ] `journal_service` : `enregistrer`, `consulter`
- [ ] `admin_controller` : `lister_imports`, `corriger_observation`, `supprimer_observation`,
      `lister_utilisateurs`, `gerer_utilisateur`, `consulter_journal`
- [ ] Frontend `admin.py` : remplacer les tableaux mock par les routes `/admin/*`

---

## FO3 — Rapport PDF ❌ À FAIRE

**Chaîne** : `/rapports` · `/rapports/{id}` → `rapport_service` → `utils/graphiques` + `utils/pdf` → `rapport_dao` (✅).

**Reste :**
- [ ] `utils/graphiques` : `courbe`, `barres` (matplotlib)
- [ ] `utils/pdf` : `construire` (reportlab)
- [ ] `rapport_service` : `generer`, `lister`, `telecharger`
- [ ] `rapport_controller` : `demander_rapport`, `lister_rapports`, `telecharger_rapport`

---

## Collecte périodique ❌ À FAIRE

**Reste :**
- [ ] `utils/planificateur` : `demarrer`, `arreter` (APScheduler) + branchement dans `main.py`

---

## Frontend — état transversal

`api_client.py` est **complet** mais **aucune page ne l'utilise** : les 5 pages
(`home`, `login`, `analyse_temporelle`, `comparaison_pays`, `comparaison_multi`, `admin`)
affichent des **données aléatoires/mock**. À brancher sur les vraies routes au fur et à
mesure que les features backend sont prêtes (voir chaque section « Frontend »/« Reste »).

---

## Ordre de travail conseillé

1. **Helpers `AnalyseService`** → débloque F3/F4/F5/FO2 + 39 tests. *(gros gain, isolé)*
2. **Référentiels restants** → petits, utiles au frontend des analyses.
3. **Authentification + `dependances`** → prérequis de F6 et des `# TODO exiger la connexion`.
4. **F6 Administration**.
5. **FO3 Rapport PDF** (graphiques → pdf → service → controller).
6. **Brancher le frontend** sur les routes, feature par feature.
7. **Collecte périodique**.

---

## Annexe — commandes & contrôles

```bash
make test-collecte                                   # F1/F2
cd backend && uv run pytest tests/test_analyse_service.py -o addopts="-q"   # F3/F4/F5/FO2
cd backend && uv run pytest tests/dao -o addopts="-q"                        # DAOs
cd backend && uv run pytest tests -o addopts="-q"    # suite complète (sans arrêt)
make lint                                            # qualité
```
```sql
-- make db-shell : pays présents dans les observations mais absents du référentiel (doit être vide)
SELECT DISTINCT o.code_pays
FROM observation o LEFT JOIN pays p ON p.code_pays = o.code_pays
WHERE p.code_pays IS NULL;
```

**État des tests au bilan :** 51 passed · 39 failed (tous dans `test_analyse_service.py`) · lint vert.
Le chantier n°1 (Helpers) suffit à passer les 39 tests en échec.
