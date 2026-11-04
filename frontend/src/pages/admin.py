import html
from datetime import date

import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import get_indicateurs, message_erreur
from utils.ui import (
    ICONE_CIBLE,
    badge,
    carte_metrique,
    entete,
    est_admin,
    ligne_source,
    tableau,
)


def _dt(valeur) -> str:
    """Formate un horodatage ISO en 'AAAA-MM-JJ HH:MM', ou '—'."""
    texte = str(valeur or "")
    if not texte or texte == "None":
        return "—"
    return texte[:16].replace("T", " ")


def _n(valeur) -> str:
    """Formate un entier avec espaces comme séparateur de milliers."""
    try:
        return f"{int(valeur):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(valeur or 0)


def _badge_statut(statut) -> str:
    """Badge coloré selon le statut d'un import."""
    s = str(statut or "").lower()
    if "succes" in s:
        return badge("Succès", "ok")
    if "echec" in s:
        return badge("Échec", "ko")
    if "cours" in s:
        return badge("En cours", "warn")
    return badge(statut or "—", "neutre")

get_page_logger("Administration (F6)")

# Garde-fou : la navigation masque déjà cette page, mais on protège l'accès
# direct par URL.
if not est_admin():
    st.title("Administration")
    st.warning("Accès réservé aux administrateurs.")
    st.stop()

entete(
    "Administration",
    "Gérez les comptes, lancez les imports ILOSTAT et suivez l'activité.",
    eyebrow="Espace réservé",
)
ligne_source(["Console d'administration", "LaborScope"], f"Extrait du {date.today():%d/%m/%Y}")


def _corps(reponse: dict) -> dict:
    """Renvoie le corps JSON d'une réponse s'il s'agit d'un objet, sinon {}."""
    return reponse["data"] if isinstance(reponse["data"], dict) else {}


def _liste(reponse: dict) -> list:
    """Renvoie la liste ``data`` d'une réponse, ou une liste vide."""
    valeur = _corps(reponse).get("data")
    return valeur if isinstance(valeur, list) else []


# --- Chargements partagés ---------------------------------------------------
indicateurs = get_indicateurs()
rep_users = api_client.get("/admin/utilisateurs")
rep_imports = api_client.get("/admin/imports")
utilisateurs = _liste(rep_users)
imports = _liste(rep_imports)

# --- Bandeau de synthèse ----------------------------------------------------
nb_admins = sum(1 for u in utilisateurs if str(u.get("role")).lower() == "admin")
imports_ok = sum(1 for i in imports if str(i.get("statut")).lower() in ("succes", "statutimport.succes"))

st.write("")
c1, c2, c3 = st.columns(3)
with c1:
    carte_metrique("Comptes", str(len(utilisateurs)), "", f"dont {nb_admins} administrateur(s)",
                   icone_svg=ICONE_CIBLE)
with c2:
    carte_metrique("Indicateurs suivis", str(len(indicateurs)), "", "référentiel ILOSTAT")
with c3:
    total_lignes = sum(int(i.get("nombre_lignes") or 0) for i in imports)
    carte_metrique("Imports réalisés", str(len(imports)), "",
                   f"{imports_ok} réussi(s) · {total_lignes:,} lignes".replace(",", " "))

st.write("")

# --- Section 1 : comptes utilisateurs ---------------------------------------
with st.container(border=True):
    st.markdown("<div class='ls-eyebrow plain'>Comptes</div>", unsafe_allow_html=True)
    st.markdown("<div class='ls-serif' style='font-size:1.4rem'>Gestion des utilisateurs</div>",
                unsafe_allow_html=True)

    if rep_users["status_code"] != 200:
        st.error(message_erreur(rep_users))
    elif not utilisateurs:
        st.info("Aucun utilisateur à afficher.")
    else:
        lignes_u = []
        for u in utilisateurs:
            est_adm = str(u.get("role", "")).lower() == "admin"
            lignes_u.append([
                html.escape(str(u.get("id", ""))),
                html.escape(str(u.get("nom_utilisateur", ""))),
                badge("Admin", "ok") if est_adm else badge("Utilisateur", "neutre"),
                badge("Actif", "ok") if u.get("actif") else badge("Inactif", "ko"),
                _dt(u.get("date_creation")),
                _dt(u.get("derniere_connexion")),
            ])
        tableau(
            ["ID", "Utilisateur", "Rôle", "Actif", "Créé le", "Dernière connexion"],
            lignes_u,
            aligns=["num", "", "", "", "", ""],
        )

        st.markdown("<div class='ls-divider'></div>", unsafe_allow_html=True)
        st.caption("Modifier un compte")
        par_nom = {u["nom_utilisateur"]: u for u in utilisateurs}
        e1, e2, e3, e4 = st.columns([1.6, 1.2, 0.8, 1], vertical_alignment="bottom")
        with e1:
            choix = st.selectbox("Compte", list(par_nom), label_visibility="collapsed")
        cible = par_nom[choix]
        with e2:
            est_admin_actuel = str(cible.get("role")).lower() == "admin"
            role_label = st.selectbox(
                "Rôle", ["Utilisateur", "Administrateur"],
                index=1 if est_admin_actuel else 0, label_visibility="collapsed",
            )
        with e3:
            actif = st.toggle("Actif", value=bool(cible.get("actif", True)))
        with e4:
            enregistrer = st.button("Enregistrer", type="primary", use_container_width=True)

        if enregistrer:
            charge = dict(cible)
            charge["role"] = "admin" if role_label == "Administrateur" else "utilisateur"
            charge["actif"] = actif
            rep = api_client.put(f"/admin/utilisateurs/{cible['id']}", json=charge)
            if rep["status_code"] == 200:
                st.success(f"Compte « {choix} » mis à jour.")
                st.rerun()
            else:
                st.error(message_erreur(rep))

# --- Section 2 : imports ILOSTAT --------------------------------------------
with st.container(border=True):
    st.markdown("<div class='ls-eyebrow plain'>Collecte</div>", unsafe_allow_html=True)
    st.markdown("<div class='ls-serif' style='font-size:1.4rem'>Imports de données</div>",
                unsafe_allow_html=True)
    st.caption("Télécharge les observations depuis ILOSTAT (OIT) et met la base à jour.")

    i1, i2, i3 = st.columns([2, 1.4, 1], vertical_alignment="bottom")
    with i1:
        code_indicateur = st.selectbox(
            "Indicateur", options=list(indicateurs),
            format_func=lambda code: indicateurs[code],
        )
    with i2:
        annee_min, annee_max = st.select_slider(
            "Période", options=list(range(2014, 2027)), value=(2015, 2025),
        )
    with i3:
        lancer = st.button("Lancer l'import", type="primary", use_container_width=True)

    if lancer:
        with st.spinner("Import en cours (téléchargement ILOSTAT)…"):
            reponse = api_client.post(
                f"/admin/imports/{code_indicateur}",
                params={"from_date": annee_min, "to_date": annee_max},
                timeout=290,
            )
        if reponse["status_code"] == 200:
            corps = _corps(reponse)
            statut = str(corps.get("statut", "")).lower()
            msg = (f"Import terminé — statut : {corps.get('statut')}, "
                   f"lignes insérées : {corps.get('lignes_inserees')}")
            if "succes" in statut:
                st.success(msg)
            else:
                st.warning(msg)
            st.rerun()
        else:
            st.error(message_erreur(reponse))

    st.markdown("<div class='ls-divider'></div>", unsafe_allow_html=True)
    st.caption("Historique des imports")
    if rep_imports["status_code"] != 200:
        st.error(message_erreur(rep_imports))
    elif not imports:
        st.info("Aucun import enregistré.")
    else:
        lignes_i = []
        for i in sorted(imports, key=lambda x: x.get("id", 0), reverse=True):
            err = str(i.get("message_erreur") or "")
            err_court = (err[:60] + "…") if len(err) > 60 else (err or "—")
            lignes_i.append([
                html.escape(str(i.get("id", ""))),
                html.escape(str(i.get("indicateur_code", ""))),
                _badge_statut(i.get("statut")),
                _n(i.get("nombre_lignes")),
                _dt(i.get("date_debut")),
                _dt(i.get("date_fin")),
                html.escape(err_court),
            ])
        tableau(
            ["ID", "Indicateur", "Statut", "Lignes", "Début", "Fin", "Détail"],
            lignes_i,
            aligns=["num", "", "", "num", "", "", ""],
        )

# --- Section 3 : journal d'activité -----------------------------------------
with st.container(border=True):
    st.markdown("<div class='ls-eyebrow plain'>Traçabilité</div>", unsafe_allow_html=True)
    st.markdown("<div class='ls-serif' style='font-size:1.4rem'>Journal d'activité</div>",
                unsafe_allow_html=True)

    rep_journal = api_client.get("/journal/")
    if rep_journal["status_code"] == 200:
        journal = _liste(rep_journal)
        if journal:
            st.dataframe(pd.DataFrame(journal), use_container_width=True, hide_index=True)
        else:
            st.info("Aucune entrée dans le journal pour le moment.")
    else:
        st.warning(f"Journal indisponible ({message_erreur(rep_journal)}).")
