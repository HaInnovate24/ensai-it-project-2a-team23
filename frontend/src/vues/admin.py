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
    notif,
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
    notif("Accès réservé aux administrateurs.", "warn")
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
jeton = st.session_state.get("access_token")
indicateurs = get_indicateurs()
rep_users = api_client.get("/admin/utilisateurs", params={"jeton": jeton})
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


@st.dialog("Modifier le compte")
def _dialog_utilisateur(u: dict) -> None:
    """Modale d'édition d'un compte : rôle et statut, puis enregistrement."""
    uid = u.get("id")
    nom = str(u.get("nom_utilisateur", ""))
    role_actuel = "admin" if str(u.get("role", "")).lower() == "admin" else "utilisateur"
    actif_actuel = bool(u.get("actif", False))

    st.markdown(
        f"<div class='ls-serif' style='font-size:1.2rem'>{html.escape(nom)}</div>"
        f"<div class='ls-meta'>Identifiant {html.escape(str(uid))}</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    role_label = st.selectbox(
        "Rôle", ["Utilisateur", "Administrateur"],
        index=1 if role_actuel == "admin" else 0,
    )
    actif = st.toggle("Compte actif", value=actif_actuel)

    st.write("")
    col_ok, col_annuler = st.columns(2)
    enregistrer = col_ok.button("Enregistrer", type="primary", use_container_width=True)
    if col_annuler.button("Annuler", use_container_width=True):
        st.rerun()

    if enregistrer:
        jeton_actif = st.session_state.get("access_token")
        role_cible = "admin" if role_label == "Administrateur" else "utilisateur"
        erreurs: list[str] = []
        if role_cible != role_actuel:
            rep = api_client.patch(
                f"/admin/utilisateurs/{uid}/role",
                params={"jeton": jeton_actif, "role": role_cible},
            )
            if rep["status_code"] != 200:
                erreurs.append(message_erreur(rep))
        if actif != actif_actuel:
            rep = api_client.patch(
                f"/admin/utilisateurs/{uid}/statut",
                params={"jeton": jeton_actif, "actif": actif},
            )
            if rep["status_code"] != 200:
                erreurs.append(message_erreur(rep))
        if erreurs:
            for message in erreurs:
                notif(message, "ko")
        else:
            st.session_state["_user_resultat"] = f"Compte « {nom} » mis à jour."
            st.rerun()


# --- Section 1 : comptes utilisateurs ---------------------------------------
with st.container(border=True):
    st.markdown("<div class='ls-eyebrow plain'>Comptes</div>", unsafe_allow_html=True)
    st.markdown("<div class='ls-serif' style='font-size:1.4rem'>Gestion des utilisateurs</div>",
                unsafe_allow_html=True)

    message_user = st.session_state.pop("_user_resultat", None)
    if message_user:
        notif(message_user, "ok")

    if rep_users["status_code"] != 200:
        notif(message_erreur(rep_users), "ko")
    elif not utilisateurs:
        notif("Aucun utilisateur à afficher.", "info")
    else:
        largeurs = [0.6, 2.4, 1.3, 1, 1]
        entetes = ["ID", "Utilisateur", "Rôle", "Statut", ""]
        cols_h = st.columns(largeurs, vertical_alignment="center")
        for col, titre in zip(cols_h, entetes, strict=True):
            col.markdown(
                f"<div class='ls-eyebrow plain' style='margin:0'>{html.escape(titre)}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div class='ls-divider'></div>", unsafe_allow_html=True)

        for u in utilisateurs:
            uid = u.get("id")
            est_admin_ligne = str(u.get("role", "")).lower() == "admin"
            actif_actuel = bool(u.get("actif", False))

            c = st.columns(largeurs, vertical_alignment="center")
            c[0].markdown(
                f"<span style='color:#8A938D'>{html.escape(str(uid))}</span>",
                unsafe_allow_html=True,
            )
            c[1].markdown(html.escape(str(u.get("nom_utilisateur", ""))))
            c[2].markdown(
                "Administrateur" if est_admin_ligne else "Utilisateur",
            )
            c[3].markdown(
                badge("Actif", "ok") if actif_actuel else badge("Inactif", "neutre"),
                unsafe_allow_html=True,
            )
            if c[4].button("Modifier", key=f"edit_{uid}", use_container_width=True):
                _dialog_utilisateur(u)


@st.dialog("Confirmer l'import")
def _dialog_import(code: str, libelle: str, a_min: int, a_max: int) -> None:
    """Modale de confirmation puis exécution d'un import ILOSTAT."""
    st.markdown(
        "<div class='ls-eyebrow plain'>Indicateur</div>"
        f"<div class='ls-serif' style='font-size:1.15rem'>{html.escape(libelle)}</div>"
        f"<div class='ls-meta' style='margin-top:0.4rem'>Période · {a_min} – {a_max}</div>",
        unsafe_allow_html=True,
    )
    st.caption("Le téléchargement peut prendre plusieurs minutes.")
    st.write("")
    col_ok, col_annuler = st.columns(2)
    confirmer = col_ok.button("Lancer maintenant", type="primary", use_container_width=True)
    if col_annuler.button("Annuler", use_container_width=True):
        st.rerun()
    if confirmer:
        with st.spinner("Import en cours (téléchargement ILOSTAT)…"):
            reponse = api_client.post(
                f"/admin/imports/{code}",
                params={"from_date": a_min, "to_date": a_max},
                timeout=290,
            )
        if reponse["status_code"] == 200:
            corps = _corps(reponse)
            statut = str(corps.get("statut", "")).lower()
            st.session_state["_import_resultat"] = (
                "succes" in statut,
                f"Import terminé — statut : {corps.get('statut')}, "
                f"lignes insérées : {corps.get('lignes_inserees')}",
            )
        else:
            st.session_state["_import_resultat"] = (False, message_erreur(reponse))
        st.rerun()


# --- Section 2: Imports ILOSTAT --------------------------------------------
with st.container(border=True):
    st.markdown("<div class='ls-eyebrow plain'>Collecte</div>", unsafe_allow_html=True)
    st.markdown("<div class='ls-serif' style='font-size:1.4rem'>Imports de données</div>",
                unsafe_allow_html=True)
    st.caption("Télécharge les observations ILOSTAT et met la base à jour.")

    resultat = st.session_state.pop("_import_resultat", None)
    if resultat is not None:
        ok, message = resultat
        notif(message, "ok" if ok else "warn")

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
        if st.button("Lancer l'import", type="primary", use_container_width=True):
            _dialog_import(code_indicateur, indicateurs[code_indicateur], annee_min, annee_max)

    st.markdown("<div class='ls-divider'></div>", unsafe_allow_html=True)
    st.caption("Historique des imports")
    if rep_imports["status_code"] != 200:
        notif(message_erreur(rep_imports), "ko")
    elif not imports:
        notif("Aucun import enregistré.", "info")
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
            notif("Aucune entrée dans le journal pour le moment.", "info")
    else:
        notif(f"Journal indisponible ({message_erreur(rep_journal)}).", "warn")
