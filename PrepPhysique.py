import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import requests
import base64
import os
import hashlib
import time

from sports_analytics import (
    supabase,
    SUPABASE_URL,
    SUPABASE_KEY,
    connexion,
    deconnexion,
    creer_compte,
    modifier_compte,
    supprimer_compte,
    lister_comptes,
    ajouter_athlete_manual,
    modifier_athlete,
    supprimer_profil_athlete,
    creer_equipe,
    supprimer_equipe,
    FORMAT_BLESSURE,
    obtenir_reponses_avec_definitions,
    calculer_statut_disponibilite,
    enregistrer_reponse_evenement,
    obtenir_reponse_evenement,
    definir_minutes_avant,
    definir_minutes_apres,
    definir_type_questionnaire,
    assigner_questionnaire,
    obtenir_assignations,
    questionnaire_disponible_pour,
    obtenir_fichiers_evenement,
    lire_fichier_gps,
    matcher_nom_athlete,
    enregistrer_rapport_gps,
    obtenir_rapports_gps,
    COLONNES_GPS_NUMERIQUES,
    obtenir_reponses_athlete,
    obtenir_ou_creer_rpe_auto,
    LABEL_RPE_AUTO,
    TITRE_RPE_AUTO,
    parse_dt, fmt_date_fr, cle_seance, groupes_seances,
    inserer_avec_repli, maj_avec_repli,
    FORMAT_DOULEUR, FORMAT_PRESENCE, TITRE_PRESENCE_AUTO, LABEL_PRESENCE, LABELS_PRESENCE,
    est_questionnaire_auto, obtenir_ou_creer_presence_auto, statut_presence,
    obtenir_reponses_events, calculer_effectif, supprimer_assignation,
    LIBELLES_GPS, obtenir_donnees_alertes, calculer_alertes,
    construire_df_reponses, construire_df_gps, filtrer_periode, stats_par_question, table_rpe_vs_cible,
)

NOMS_METRIQUES_GPS = {
    "distance_totale_m": "Distance totale (m)",
    "distance_haute_intensite_m": "Distance haute intensité (m)",
    "distance_haute_vitesse_m": "Distance haute vitesse (m)",
    "distance_sprint_m": "Distance sprint (m)",
    "nb_accelerations": "Accélérations",
    "nb_decelerations": "Décélérations",
    "vmax_kmh": "Vmax (km/h)",
    "meterage_par_minute": "Distance par minute (m/min)",
    "duree_secondes": "Durée (secondes)",
}

st.set_page_config(
    page_title="Performance+ | Prép. Physique",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg-base: #0a0e1a;
        --bg-panel: #131a2b;
        --bg-panel-2: #172038;
        --border-soft: #263049;
        --text-main: #f1f5f9;
        --text-dim: #93a0bd;
        --accent: #ff5a1f;
        --accent-2: #ffb020;
        --accent-cyan: #22d3ee;
        --success: #22c55e;
        --danger: #ef4444;
    }

    html, body, .stApp {
        background: radial-gradient(circle at 15% 0%, #101a30 0%, var(--bg-base) 45%) fixed;
        color: var(--text-main);
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, h5 {
        font-family: 'Sora', sans-serif !important;
        color: var(--text-main) !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }
    h1 { font-weight: 800 !important; }
    p, span, label, .stMarkdown, .stCaption { font-family: 'Inter', sans-serif; }
    [data-testid="stCaptionContainer"] { color: var(--text-dim) !important; }

    [data-testid="collapsedControl"] {
        top: 1.5rem !important;
        left: 1rem !important;
        background-color: var(--bg-panel) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }

    header [data-testid="stToolbar"] {
        display: none !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1424 0%, #0a0e1a 100%);
        border-right: 1px solid var(--border-soft);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 6px;
        transition: all 0.15s ease;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        border-color: var(--accent);
        background: #1a2338;
    }

    .stButton>button {
        border-radius: 10px !important;
        font-family: 'Sora', sans-serif;
        font-weight: 600;
        border: 1px solid var(--border-soft);
        transition: all 0.15s ease;
    }
    .stButton>button:hover { transform: translateY(-1px); border-color: var(--accent); }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%) !important;
        color: #0a0e1a !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(255, 90, 31, 0.35);
    }
    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(255, 90, 31, 0.5);
        transform: translateY(-2px);
    }
    .stDownloadButton>button {
        border-radius: 10px !important;
        border: 1px solid var(--accent-cyan) !important;
        color: var(--accent-cyan) !important;
        background: transparent !important;
    }

    div[data-testid="stForm"] {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 16px;
        padding: 26px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }
    div[data-testid="stExpander"] {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft) !important;
        border-radius: 14px !important;
        overflow: hidden;
    }
    div[data-testid="stExpander"] summary {
        font-family: 'Sora', sans-serif;
        font-weight: 600;
    }

    div[data-testid="stMetric"] {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-left: 3px solid var(--accent);
        border-radius: 12px;
        padding: 14px 18px;
    }
    div[data-testid="stMetricLabel"] { color: var(--text-dim) !important; }
    div[data-testid="stMetricValue"] { font-family: 'Sora', sans-serif; color: var(--text-main) !important; }

    button[data-baseweb="tab"] {
        font-family: 'Sora', sans-serif;
        font-weight: 600;
        color: var(--text-dim) !important;
        border-radius: 10px 10px 0 0 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom: 3px solid var(--accent) !important;
    }

    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    div[data-baseweb="select"] > div {
        background-color: var(--bg-panel-2) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 8px !important;
        color: var(--text-main) !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }

    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border-soft); }
    hr { border-color: var(--border-soft) !important; }
</style>
""", unsafe_allow_html=True)

LABEL_QUESTION_BLESSURE = "Blessure / douleur empêchant de s'entraîner ?"

if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

if st.session_state.user_profile is None:
    try:
        current_session = supabase.auth.get_session()
        if current_session and current_session.user:
            prof_res = supabase.table("profiles").select("*").eq("id", current_session.user.id).single().execute()
            if prof_res.data:
                st.session_state.user_profile = prof_res.data
    except Exception:
        pass

def ecran_connexion():
    st.markdown("""
    <div style="text-align:center; padding: 40px 0 10px 0;">
        <div class="brand-kicker" style="font-size:2.4em;">⚡ PERFORMANCE+</div>
        <div class="brand-tagline" style="font-size:1em;">Préparation physique & suivi de performance</div>
    </div>
    """, unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.3, 1])
    with col_login:
        st.subheader("🔐 Connexion")
        st.caption("Un compte est requis pour accéder au logiciel.")

        with st.form("form_login"):
            email = st.text_input("E-mail")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Veuillez renseigner l'e-mail et le mot de passe.")
        else:
            with st.spinner("Connexion en cours..."):
                session, profile, erreur = connexion(email, password)
            if erreur:
                st.error(erreur)
            else:
                st.session_state.user_profile = profile
                flash_succes(f"Bienvenue {profile.get('full_name', '')} !")
                st.rerun()

if not st.session_state.user_profile:
    ecran_connexion()
    st.stop()

profil_connecte = st.session_state.user_profile
role_connecte = profil_connecte.get("role", "athlete")
mon_id = profil_connecte.get("id")

st.sidebar.markdown("""
<div class="brand-kicker">⚡ PERFORMANCE+</div>
<div class="brand-tagline">Prép. physique & performance</div>
""", unsafe_allow_html=True)
st.sidebar.markdown(f"**👤 {profil_connecte.get('full_name', 'Utilisateur')}**")
st.sidebar.caption(f"Rôle : {'🏋️ Coach' if role_connecte == 'coach' else '🏃 Athlète'}")
if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
    deconnexion()
    st.session_state.user_profile = None
    st.rerun()
st.sidebar.markdown("---")

st.markdown("""
<div style="display:flex; align-items:baseline; gap:12px; margin-bottom: -10px;">
    <span style="font-family:'Sora',sans-serif; font-weight:800; font-size:2.1em;">⚡ Performance+</span>
    <span style="color:var(--text-dim); font-size:1em;">Suivi de performance</span>
</div>
""", unsafe_allow_html=True)

if role_connecte == "coach":
    menu_options = [
        "📅 Planning & Séances",
        "🔔 Alertes",
        "👥 Effectif",
        "📁 Fichiers & Rapports GPS",
        "📝 Questionnaires",
        "📊 Analytique",
        "⚙️ Gestion des profils",
        "🔊 Générateur de Bips Audio",
    ]
else:
    menu_options = [
        "📅 Séances à venir",
        "📆 Calendrier",
        "📊 Mes données",
    ]

def rendre_formulaire_questionnaire(q_obj, event_id, key_suffix, reponses_deja=None, athlete_id=None):
    cible_id = athlete_id or mon_id
    reponses_deja = reponses_deja or {}
    answers_dict = {}
    rpe_val = None
    valeurs_manquantes = []
    with st.form(f"form_{key_suffix}"):
        for idx, q in enumerate(q_obj.get("questions", [])):
            lbl = q.get("label", f"Question {idx + 1}")
            fmt = q.get("format")
            valeur_existante = reponses_deja.get(lbl)

            if fmt == "scale":
                scale_max = int(q.get("scale_max", 5))
                options = list(range(1, scale_max + 1))
                est_rpe = "rpe" in lbl.lower()
                try:
                    idx_defaut = options.index(int(float(valeur_existante))) if valeur_existante not in (None, "") else (None if est_rpe else 0)
                except (ValueError, TypeError):
                    idx_defaut = None if est_rpe else 0
                ans = st.selectbox(f"{lbl} (1-{scale_max})", options, index=idx_defaut, key=f"{key_suffix}_{idx}", placeholder="Choisis une valeur")
                if ans is None:
                    valeurs_manquantes.append(lbl)
                else:
                    answers_dict[lbl] = float(ans)
                    if est_rpe:
                        rpe_val = float(ans)
            elif fmt == "number":
                try:
                    val_defaut = float(valeur_existante) if valeur_existante not in (None, "") else 0.0
                except (ValueError, TypeError):
                    val_defaut = 0.0
                ans = st.number_input(lbl, value=val_defaut, key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = float(ans)
            elif fmt == FORMAT_PRESENCE:
                opts_p = ["Oui", "Non"]
                v_p = str(valeur_existante).strip().capitalize() if valeur_existante not in (None, "") else None
                ans = st.selectbox(f"✅ {lbl}", opts_p, index=opts_p.index(v_p) if v_p in opts_p else None, key=f"{key_suffix}_{idx}", placeholder="Choisis Oui ou Non")
                if ans is None:
                    valeurs_manquantes.append(lbl)
                else:
                    answers_dict[lbl] = ans
            elif fmt == FORMAT_DOULEUR:
                ans = st.text_input(f"🩹 {lbl}", value="" if str(valeur_existante).strip().lower() in ("", "none", "aucune") else str(valeur_existante),
                                    key=f"{key_suffix}_{idx}", placeholder="Ex : ischio gauche — laisse vide si aucune douleur")
                answers_dict[lbl] = ans.strip() or "Aucune"
            elif fmt == FORMAT_BLESSURE:
                idx_defaut = 1 if str(valeur_existante).strip().lower() == "oui" else 0
                ans = st.selectbox(f"🚑 {lbl}", ["Non", "Oui"], index=idx_defaut, key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = ans
            else:
                ans = st.text_input(lbl, value=str(valeur_existante) if valeur_existante is not None else "", key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = ans

        libelle_bouton = "💾 Mettre à jour" if reponses_deja else "🚀 Envoyer"
        if st.form_submit_button(libelle_bouton, type="primary"):
            if valeurs_manquantes:
                st.error("Choisis une valeur pour : " + ", ".join(valeurs_manquantes))
                ok, err = False, None
            else:
                ok, err = enregistrer_reponse_evenement(cible_id, event_id, q_obj["id"], answers_dict, rpe_val)
            if valeurs_manquantes:
                pass
            elif ok:
                st.session_state.pop("cache_statuts_dispo", None)
                st.session_state.get("forms_ouverts", set()).discard(key_suffix)
                st.session_state.pop("_cache_alertes", None)
                flash_succes(f"« {q_obj.get('title')} » envoyé : tes réponses ont bien été enregistrées.")
                st.rerun()
            else:
                st.error(f"Erreur lors de l'enregistrement : {err}")

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
JOURS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

def maintenant_local():
    """Heure actuelle en France (le serveur Streamlit tourne en UTC : sans ça, l'ouverture des questionnaires serait décalée de 1 à 2 h)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Paris")).replace(tzinfo=None)
    except Exception:
        return datetime.now()

def _parser_datetime_event(ev, champ="start_time"):
    try:
        return datetime.fromisoformat((ev.get(champ) or "").replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None

def afficher_fichiers_evenement(event_id, key_prefix=""):
    """Affiche les documents (PDF / images) attachés à une séance : aperçu + téléchargement."""
    fichiers = obtenir_fichiers_evenement(event_id)
    if not fichiers:
        return
    st.markdown("##### 📎 Documents de la séance")
    for f in fichiers:
        f_url = f.get("file_url", "") or ""
        nom_f = f.get("file_name") or "document"
        ext = (f.get("file_type") or nom_f.rsplit(".", 1)[-1]).lower()
        st.markdown(f"**📄 {f.get('title', 'Document')}**")
        if f.get("description"):
            st.caption(f.get("description"))
        donnees = None
        if f_url.startswith("data:"):
            try:
                donnees = base64.b64decode(f_url.split(",", 1)[1])
            except Exception:
                st.caption("⚠️ Fichier indisponible")
                continue
        if ext in ("png", "jpg", "jpeg"):
            st.image(donnees if donnees is not None else f_url, use_container_width=True)
        elif ext == "pdf" and st.checkbox("👁️ Afficher le PDF", key=f"{key_prefix}_view_{f['id']}"):
            st.markdown(f'<iframe src="{f_url}" width="100%" height="650" style="border:1px solid #263049;border-radius:10px;"></iframe>', unsafe_allow_html=True)
        if donnees is not None:
            st.download_button("💾 Télécharger", data=donnees, file_name=nom_f, key=f"{key_prefix}_dl_{f['id']}")
        else:
            st.markdown(f"[🔗 Ouvrir le document]({f_url})")

menu = st.sidebar.radio("Navigation", menu_options)

def upload_file_direct_http(bucket_name, storage_path, file_bytes, mime_type):
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY,
        "Content-Type": mime_type
    }
    resp = requests.post(url, data=file_bytes, headers=headers, timeout=30)
    if resp.status_code in [200, 201]:
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{storage_path}"
    else:
        raise Exception(f"Erreur Upload HTTP {resp.status_code}: {resp.text}")

def get_statuts_disponibilite():
    if "cache_statuts_dispo" not in st.session_state:
        profiles_all = supabase.table("profiles").select("*").execute().data or []
        responses_def = obtenir_reponses_avec_definitions()
        st.session_state.cache_statuts_dispo = calculer_statut_disponibilite(profiles_all, responses_def)
    return st.session_state.cache_statuts_dispo

# =====================================================================
# OUTILS COMMUNS : confirmations, dates françaises, alertes, analytique
# =====================================================================
SQL_MIGRATION = """-- À exécuter une seule fois dans Supabase (SQL Editor)
alter table events add column if not exists target_rpe numeric;
alter table events add column if not exists rpe_desactive boolean default false;
alter table profiles add column if not exists jersey_number integer;
alter table profiles add column if not exists birth_date date;
alter table profiles add column if not exists height_cm numeric;
alter table profiles add column if not exists weight_kg numeric;
alter table profiles add column if not exists position text;
alter table profiles add column if not exists notes text;"""


def flash_succes(message, genre="succes"):
    """Message de confirmation qui survit au rechargement de la page (st.rerun)."""
    st.session_state.setdefault("_flash", []).append((genre, message))


def afficher_flash():
    for genre, message in st.session_state.pop("_flash", []):
        if genre == "erreur":
            st.error(message)
        elif genre == "avertissement":
            st.warning(message)
        else:
            st.success(message if str(message).startswith("✅") else f"✅ {message}")


def date_fr(*args, **kwargs):
    """Sélecteur de date au format français JJ/MM/AAAA."""
    kwargs.setdefault("format", "DD/MM/YYYY")
    return st.date_input(*args, **kwargs)


def hid(texte):
    return hashlib.md5(str(texte).encode("utf-8")).hexdigest()[:10]


def aff_df(df, masquer=("athlete_id", "event_id", "DateObj")):
    return df.drop(columns=[c for c in masquer if c in df.columns])


# ---------------------------------------------------------------------
# Coach : filtre des séances « à moi » (seulement s'il y a plusieurs coachs)
# ---------------------------------------------------------------------
def filtre_coach_id():
    if "_nb_coachs" not in st.session_state:
        try:
            st.session_state["_nb_coachs"] = len(supabase.table("profiles").select("id").eq("role", "coach").execute().data or [])
        except Exception:
            st.session_state["_nb_coachs"] = 1
    return mon_id if st.session_state["_nb_coachs"] > 1 else None


def mes_evenements(events):
    cid = filtre_coach_id()
    return [e for e in events if (not cid) or e.get("coach_id") in (None, cid)]


# ---------------------------------------------------------------------
# Alertes
# ---------------------------------------------------------------------
ICONES_ALERTES = {"douleur": "🩹", "blessure": "🚑", "rpe_joueur": "🔥", "rpe_equipe": "👥",
                  "wellness_stat": "📉", "gps_stat": "🛰️"}
NOMS_ALERTES = {"douleur": "Douleur musculaire", "blessure": "Blessure", "rpe_joueur": "RPE joueur vs cible",
                "rpe_equipe": "RPE équipe vs cible", "wellness_stat": "Réponse wellness extrême", "gps_stat": "GPS inhabituel"}


def get_alertes_coach(force=False):
    jours = int(st.session_state.get("_al_jours", 30))
    sj = float(st.session_state.get("_al_seuil_j", 2.0))
    se = float(st.session_state.get("_al_seuil_e", 2.0))
    cle = (jours, sj, se)
    cache = st.session_state.get("_cache_alertes")
    if not force and cache and cache["cle"] == cle and (time.time() - cache["t"]) < 90:
        return cache["data"]
    donnees = obtenir_donnees_alertes(filtre_coach_id())
    data = calculer_alertes(donnees, jours, sj, se, maintenant=maintenant_local())
    st.session_state["_cache_alertes"] = {"cle": cle, "t": time.time(), "data": data}
    return data


def alertes_non_vues(force=False):
    vues = st.session_state.setdefault("alertes_vues", set())
    return [a for a in get_alertes_coach(force) if a["cle"] not in vues]


# ---------------------------------------------------------------------
# Sélecteur de période (semaine / mois / année / personnalisée)
# ---------------------------------------------------------------------
def selecteur_periode(prefix):
    import calendar as _cal
    aujourdhui = maintenant_local().date()
    type_p = st.radio("📆 Période affichée :", ["Tout", "Semaine", "Mois", "Année", "Personnalisée"], horizontal=True, key=f"{prefix}_per_type")
    debut = fin = None
    if type_p == "Semaine":
        jour = date_fr("Un jour de la semaine à afficher :", aujourdhui, key=f"{prefix}_per_sem")
        debut = jour - timedelta(days=jour.weekday())
        fin = debut + timedelta(days=6)
    elif type_p == "Mois":
        c1, c2 = st.columns(2)
        m = c1.selectbox("Mois :", list(range(1, 13)), index=aujourdhui.month - 1, format_func=lambda i: MOIS_FR[i - 1].capitalize(), key=f"{prefix}_per_mois")
        y = int(c2.number_input("Année :", 2000, 2100, aujourdhui.year, 1, key=f"{prefix}_per_mois_an"))
        debut, fin = datetime(y, m, 1).date(), datetime(y, m, _cal.monthrange(y, m)[1]).date()
    elif type_p == "Année":
        y = int(st.number_input("Année :", 2000, 2100, aujourdhui.year, 1, key=f"{prefix}_per_an"))
        debut, fin = datetime(y, 1, 1).date(), datetime(y, 12, 31).date()
    elif type_p == "Personnalisée":
        c1, c2 = st.columns(2)
        debut = date_fr("Du :", aujourdhui - timedelta(days=30), key=f"{prefix}_per_du")
        fin = date_fr("Au :", aujourdhui, key=f"{prefix}_per_au")
        if debut > fin:
            st.warning("La date de début est après la date de fin : les deux sont inversées.")
            debut, fin = fin, debut
    if debut:
        st.caption(f"Période affichée : du {debut.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}")
    return debut, fin


# ---------------------------------------------------------------------
# Analytique partagée (coach : joueur / équipe / plusieurs joueurs — athlète : lui seul)
# ---------------------------------------------------------------------
def _libelle_seance(cle, groupes):
    return f"{fmt_date_fr(cle[1], True)} — {cle[0]} ({len(groupes[cle])} joueur{'s' if len(groupes[cle]) > 1 else ''})"


def render_analytique(df_resp_all, df_gps_all, events_by_id, noms_by_id, mode, nom_scope, prefix):
    """
    mode : "joueur" | "equipe" | "multi"
    Onglets : Réponses par question · Graphique · Séance · Les données GPS · Données brutes
    """
    est_equipe = mode == "equipe"
    scope_ids = set(noms_by_id.keys())
    debut, fin = selecteur_periode(prefix)
    df_resp = filtrer_periode(df_resp_all, debut, fin)
    df_gps = filtrer_periode(df_gps_all, debut, fin)
    cols_gps = [LIBELLES_GPS[m] for m in COLONNES_GPS_NUMERIQUES]

    tab_q, tab_g, tab_s, tab_gps, tab_brut = st.tabs(["Réponses par question", "Graphique", "Séance", "Les données GPS", "Données brutes"])

    # ---------------- Réponses par question : moyennes ----------------
    with tab_q:
        stats = stats_par_question(df_resp)
        if df_resp.empty:
            st.info("Aucune réponse sur cette période.")
        else:
            titre = {"equipe": f"👥 Moyenne de l'équipe {nom_scope} sur chaque question",
                     "multi": "👥 Moyenne des joueurs sélectionnés sur chaque question"}.get(mode, f"👤 Moyenne de {nom_scope} sur chaque question")
            st.markdown(f"### {titre}")
            if stats.empty:
                st.info("Pas de réponses numériques à moyenner sur cette période.")
            else:
                st.dataframe(stats, use_container_width=True, hide_index=True)
                st.download_button("📥 Exporter les moyennes (CSV)", data=stats.to_csv(index=False).encode("utf-8"), file_name="moyennes_questions.csv", mime="text/csv", key=f"{prefix}_dl_moy")
                if mode in ("equipe", "multi"):
                    num = df_resp[df_resp["Valeur_num"].notna() & ~df_resp["Question"].isin(LABELS_PRESENCE)]
                    piv = num.pivot_table(index="Joueur", columns="Question", values="Valeur_num", aggfunc="mean").round(2)
                    with st.expander("Voir la moyenne de chaque joueur"):
                        st.dataframe(piv, use_container_width=True)
            textes = df_resp[df_resp["Valeur_num"].isna() & ~df_resp["Question"].isin(LABELS_PRESENCE)]
            if not textes.empty:
                with st.expander("📝 Réponses texte (douleurs, commentaires...)"):
                    st.dataframe(aff_df(textes.sort_values("DateObj", ascending=False))[["Date", "Joueur", "Séance", "Question", "Valeur"]], use_container_width=True, hide_index=True)

    # ---------------- Graphique ----------------
    with tab_g:
        num = df_resp[df_resp["Valeur_num"].notna() & ~df_resp["Question"].isin(LABELS_PRESENCE)] if not df_resp.empty else df_resp
        if num is None or num.empty:
            st.info("Pas de données numériques pour tracer un graphique sur cette période.")
        else:
            questions = sorted(num["Question"].unique().tolist())
            choix = st.multiselect("📊 Données à afficher dans le graphique :", questions, default=questions[:1], key=f"{prefix}_g_questions")
            normaliser = st.checkbox("Mettre toutes les données à la même échelle (0–100 %) pour mieux les comparer", key=f"{prefix}_g_norm") if len(choix) > 1 else False
            if not choix:
                st.info("Choisissez au moins une donnée.")
            else:
                sub = num[num["Question"].isin(choix)]
                if mode == "multi":
                    for q in choix:
                        agg = sub[sub["Question"] == q].groupby(["DateObj", "Joueur"], as_index=False)["Valeur_num"].mean()
                        fig = px.line(agg, x="DateObj", y="Valeur_num", color="Joueur", markers=True, template="plotly_dark", title=q)
                        fig.update_xaxes(tickformat="%d/%m/%Y", title="Date")
                        fig.update_layout(yaxis_title="Valeur")
                        st.plotly_chart(fig, use_container_width=True)
                    export = sub.groupby(["Date", "Joueur", "Question"], as_index=False)["Valeur_num"].mean()
                else:
                    agg = sub.groupby(["DateObj", "Question"], as_index=False)["Valeur_num"].mean()
                    if normaliser:
                        agg["Valeur_num"] = agg.groupby("Question")["Valeur_num"].transform(
                            lambda s: (s - s.min()) / (s.max() - s.min()) * 100 if s.max() != s.min() else 50.0)
                    titre = f"Moyenne de l'équipe {nom_scope}" if est_equipe else f"Évolution — {nom_scope}"
                    fig = px.line(agg, x="DateObj", y="Valeur_num", color="Question", markers=True, template="plotly_dark", title=titre)
                    fig.update_xaxes(tickformat="%d/%m/%Y", title="Date")
                    fig.update_layout(yaxis_title="% de l'échelle observée" if normaliser else "Valeur / Score", legend_title_text="")
                    st.plotly_chart(fig, use_container_width=True)
                    export = agg.assign(Date=agg["DateObj"].apply(lambda d: d.strftime("%d/%m/%Y"))).drop(columns=["DateObj"])
                st.download_button("📥 Exporter les données du graphique (CSV)", data=export.to_csv(index=False).encode("utf-8"), file_name="graphique.csv", mime="text/csv", key=f"{prefix}_dl_graph")

        st.markdown("---")
        st.markdown("#### 🎯 RPE réalisé vs RPE cible")
        t_rpe = table_rpe_vs_cible(df_resp, events_by_id)
        if t_rpe.empty:
            st.info("Aucun RPE enregistré sur cette période.")
        else:
            etiquettes = [f"{r['Séance']} ({r['Date'][:5]})" for _, r in t_rpe.iterrows()]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=etiquettes, y=t_rpe["RPE réalisé"], name="RPE réalisé", marker_color="#ff5a1f"))
            if t_rpe["RPE cible"].notna().any():
                fig.add_trace(go.Scatter(x=etiquettes, y=t_rpe["RPE cible"], name="RPE cible", mode="lines+markers", line=dict(color="#22d3ee", width=3)))
            else:
                st.caption("Aucun RPE cible n'a été défini sur ces séances (à renseigner dans Planning & Séances).")
            fig.update_layout(template="plotly_dark", yaxis=dict(range=[0, 10], title="RPE"), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(aff_df(t_rpe), use_container_width=True, hide_index=True)

    # ---------------- Séance ----------------
    with tab_s:
        evs_scope = [e for e in events_by_id.values() if e.get("athlete_id") in scope_ids]
        groupes = groupes_seances(evs_scope)
        if not groupes:
            st.info("Aucune séance pour cette sélection.")
        else:
            cles = sorted(groupes.keys(), key=lambda k: k[1], reverse=True)
            sel = st.selectbox("📌 Choisir une séance :", cles, format_func=lambda k: _libelle_seance(k, groupes), key=f"{prefix}_s_sel")
            evs = groupes[sel]
            ids_s = {e["id"] for e in evs}
            st.subheader(f"{sel[0]} — {fmt_date_fr(sel[1], True)}")
            d_resp = df_resp_all[df_resp_all["event_id"].isin(ids_s)] if not df_resp_all.empty else df_resp_all
            d_gps = df_gps_all[df_gps_all["event_id"].isin(ids_s)] if not df_gps_all.empty else df_gps_all

            # Effectif / présence
            rep_ev = {}
            if not d_resp.empty:
                for _, r in d_resp.iterrows():
                    rep_ev.setdefault(r["event_id"], {})[r["Question"]] = r["Valeur"]
            eff = calculer_effectif(evs, rep_ev, noms_by_id)
            if mode == "joueur":
                statut = next((k for k in ("disponible", "absent", "indispo", "sans_reponse") if eff[k]), "sans_reponse")
                lib = {"disponible": "✅ Disponible", "absent": "❌ Absent", "indispo": "🩹 Indisponible", "sans_reponse": "❓ Présence non renseignée"}[statut]
                raison = eff[statut][0]["raison"] if eff[statut] else ""
                st.markdown(f"**Présence :** {lib}" + (f" — {raison}" if raison else ""))
            else:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("✅ Disponibles", len(eff["disponible"]))
                c2.metric("❌ Absents", len(eff["absent"]))
                c3.metric("🩹 Blessés / douleur", len(eff["indispo"]))
                c4.metric("❓ Sans réponse", len(eff["sans_reponse"]))
                with st.expander("Voir la liste des joueurs"):
                    for cle_s, titre_s in [("disponible", "✅ Disponibles"), ("absent", "❌ Absents"), ("indispo", "🩹 Blessés / douleur"), ("sans_reponse", "❓ Sans réponse")]:
                        if eff[cle_s]:
                            st.markdown(f"**{titre_s}** : " + ", ".join(f"{x['nom']}" + (f" ({x['raison']})" if x['raison'] else "") for x in eff[cle_s]))

            # RPE vs cible
            t_s = table_rpe_vs_cible(d_resp, events_by_id) if not d_resp.empty else pd.DataFrame()
            cible_s = next((e.get("target_rpe") for e in evs if e.get("target_rpe") is not None), None)
            m1, m2, m3 = st.columns(3)
            reel = t_s["RPE réalisé"].iloc[0] if not t_s.empty else None
            m1.metric("RPE réalisé (moyenne)", f"{reel:g}" if reel is not None else "—")
            m2.metric("🎯 RPE cible", f"{float(cible_s):g}" if cible_s is not None else "—")
            m3.metric("Écart", f"{reel - float(cible_s):+.1f}" if (reel is not None and cible_s is not None) else "—")

            # Graphique de la séance
            st.markdown("##### 📈 Graphique de la séance")
            nums = d_resp[d_resp["Valeur_num"].notna() & ~d_resp["Question"].isin(LABELS_PRESENCE)] if not d_resp.empty else d_resp
            if nums is None or nums.empty:
                st.info("Aucune réponse numérique pour cette séance.")
            else:
                q_s = st.selectbox("Donnée :", sorted(nums["Question"].unique()), key=f"{prefix}_s_q")
                dq = nums[nums["Question"] == q_s]
                fig = px.bar(dq, x="Joueur", y="Valeur_num", template="plotly_dark", title=q_s)
                if mode != "joueur" and len(dq) > 1:
                    fig.add_hline(y=dq["Valeur_num"].mean(), line_dash="dash", line_color="#22d3ee", annotation_text=f"Moyenne {dq['Valeur_num'].mean():.2f}")
                fig.update_layout(yaxis_title="Valeur")
                st.plotly_chart(fig, use_container_width=True)

            # GPS de la séance : graphique puis tableau
            st.markdown("##### 🛰️ Données GPS de la séance")
            if d_gps is None or d_gps.empty:
                st.info("Aucun rapport GPS pour cette séance.")
            else:
                m_s = st.selectbox("Métrique GPS :", cols_gps, key=f"{prefix}_s_gps")
                fig = px.bar(d_gps, x="Joueur", y=m_s, template="plotly_dark", title=m_s)
                if mode != "joueur" and len(d_gps) > 1:
                    fig.add_hline(y=d_gps[m_s].mean(), line_dash="dash", line_color="#22d3ee", annotation_text=f"Moyenne {d_gps[m_s].mean():.1f}")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(aff_df(d_gps), use_container_width=True, hide_index=True)

            # Données brutes de la séance
            st.markdown("##### 📋 Données brutes de la séance")
            if d_resp is None or d_resp.empty:
                st.info("Aucune réponse pour cette séance.")
            else:
                st.dataframe(aff_df(d_resp)[["Joueur", "Date", "Question", "Valeur"]], use_container_width=True, hide_index=True)

            # Comparer des séances
            st.markdown("---")
            st.markdown("##### 🔁 Comparer avec d'autres séances")
            autres = st.multiselect("Séances à comparer :", [k for k in cles if k != sel], format_func=lambda k: _libelle_seance(k, groupes), key=f"{prefix}_s_cmp")
            if autres:
                nums_all = df_resp_all[df_resp_all["Valeur_num"].notna() & ~df_resp_all["Question"].isin(LABELS_PRESENCE)] if not df_resp_all.empty else df_resp_all
                choix_m = ["RPE"] + (sorted(nums_all["Question"].unique()) if nums_all is not None and not nums_all.empty else []) + (cols_gps if not df_gps_all.empty else [])
                m_c = st.selectbox("Donnée à comparer :", choix_m, key=f"{prefix}_s_cmp_m")
                lignes = []
                for k in [sel] + autres:
                    ids_k = {e["id"] for e in groupes[k]}
                    if m_c in cols_gps:
                        serie = df_gps_all[df_gps_all["event_id"].isin(ids_k)][m_c].dropna()
                    elif m_c == "RPE":
                        dk = df_resp_all[df_resp_all["event_id"].isin(ids_k) & df_resp_all["Question"].str.lower().str.contains("rpe") & df_resp_all["Valeur_num"].notna()]
                        serie = dk["Valeur_num"]
                    else:
                        dk = df_resp_all[df_resp_all["event_id"].isin(ids_k) & (df_resp_all["Question"] == m_c) & df_resp_all["Valeur_num"].notna()]
                        serie = dk["Valeur_num"]
                    lignes.append({"Séance": f"{k[0]} ({fmt_date_fr(k[1])})", "Moyenne": round(float(serie.mean()), 2) if len(serie) else None, "Nb valeurs": int(len(serie))})
                dfc = pd.DataFrame(lignes)
                fig = px.bar(dfc, x="Séance", y="Moyenne", template="plotly_dark", title=f"{m_c} — comparaison de séances")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(dfc, use_container_width=True, hide_index=True)

    # ---------------- Données GPS : graphique PUIS tableau ----------------
    with tab_gps:
        st.markdown("### 🛰️ Données & Rapports GPS")
        if df_gps is None or df_gps.empty:
            st.info("Aucun rapport GPS sur cette période pour cette sélection.")
        else:
            metrique = st.selectbox("Métrique à tracer :", cols_gps, key=f"{prefix}_gps_m")
            if est_equipe:
                agg = df_gps.groupby(["DateObj", "Séance"], as_index=False)[cols_gps].mean()
                nb = df_gps.groupby(["DateObj", "Séance"])["Joueur"].nunique().rename("Nb joueurs").reset_index()
                agg = agg.merge(nb, on=["DateObj", "Séance"]).sort_values("DateObj")
                agg["Date"] = agg["DateObj"].apply(lambda d: d.strftime("%d/%m/%Y"))
                agg["Séance (date)"] = agg["Séance"] + " — " + agg["Date"]
                fig = px.bar(agg, x="Séance (date)", y=metrique, template="plotly_dark", title=f"Moyenne équipe {nom_scope} — {metrique}")
                st.plotly_chart(fig, use_container_width=True)
                tableau = aff_df(agg.drop(columns=["Séance (date)"]).round(2))
                st.markdown("#### 👥 Moyenne de l'équipe, séance par séance")
                st.dataframe(tableau, use_container_width=True, hide_index=True)
                with st.expander("Voir le détail par joueur"):
                    st.dataframe(aff_df(df_gps.sort_values("DateObj")).round(2), use_container_width=True, hide_index=True)
                export = tableau
            else:
                d = df_gps.sort_values("DateObj").copy()
                d["Séance (date)"] = d["Séance"] + " — " + d["Date"]
                fig = px.bar(d, x="Séance (date)", y=metrique, color="Joueur", barmode="group", template="plotly_dark", title=metrique)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("#### Données brutes GPS")
                export = aff_df(d.drop(columns=["Séance (date)"])).round(2)
                st.dataframe(export, use_container_width=True, hide_index=True)
            st.download_button("📥 Exporter les données GPS (CSV)", data=export.to_csv(index=False).encode("utf-8"), file_name="donnees_gps.csv", mime="text/csv", key=f"{prefix}_dl_gps")

    # ---------------- Données brutes ----------------
    with tab_brut:
        st.markdown("### 📋 Données brutes")
        if df_resp is not None and not df_resp.empty:
            st.markdown("**Réponses aux questionnaires**")
            brut = aff_df(df_resp.sort_values("DateObj", ascending=False))[["Date", "Joueur", "Séance", "Question", "Valeur"]]
            st.dataframe(brut, use_container_width=True, hide_index=True)
            st.download_button("📥 Exporter les réponses (CSV)", data=brut.to_csv(index=False).encode("utf-8"), file_name="reponses_brutes.csv", mime="text/csv", key=f"{prefix}_dl_brut")
        if df_gps is not None and not df_gps.empty:
            st.markdown("**Données GPS**")
            st.dataframe(aff_df(df_gps.sort_values("DateObj", ascending=False)), use_container_width=True, hide_index=True)
        if (df_resp is None or df_resp.empty) and (df_gps is None or df_gps.empty):
            st.info("Aucune donnée brute sur cette période.")


# ---------------------------------------------------------------------
# Athlète : bouton qui ouvre / ferme un questionnaire
# ---------------------------------------------------------------------
def bouton_ouvrir(libelle, cle, desactive=False):
    ouverts = st.session_state.setdefault("forms_ouverts", set())
    est_ouvert = cle in ouverts
    if st.button(("🔽 Masquer : " if est_ouvert else "") + libelle, key=f"btnopen_{cle}", use_container_width=True, disabled=desactive):
        if est_ouvert:
            ouverts.discard(cle)
        else:
            ouverts.add(cle)
        st.rerun()
    return cle in ouverts


# ---- Questionnaires automatiques (présence + RPE) : créés une fois, dès la 1re visite du coach ----
if role_connecte == "coach" and not st.session_state.get("_auto_q_ok"):
    obtenir_ou_creer_rpe_auto()
    obtenir_ou_creer_presence_auto()
    st.session_state["_auto_q_ok"] = True

# ---- Compteur d'alertes dans la barre latérale (coach) ----
if role_connecte == "coach":
    try:
        _n_alertes = len(alertes_non_vues())
        if _n_alertes:
            st.sidebar.warning(f"🔔 {_n_alertes} alerte(s) à consulter")
    except Exception:
        pass

# =====================================================================
# PAGE : PLANNING & SÉANCES
# =====================================================================
if menu == "📅 Planning & Séances":
    import calendar as _calendar
    st.header("📅 Planning & Séances")
    afficher_flash()

    res_athletes = supabase.table("profiles").select("id, full_name, team_id").eq("role", "athlete").execute()
    athletes_list = res_athletes.data if res_athletes.data else []
    dict_athletes = {a.get("full_name", f"Athlète {a['id']}"): a["id"] for a in athletes_list if a.get("full_name")}
    noms_by_id = {v: k for k, v in dict_athletes.items()}

    teams_list_all = supabase.table("teams").select("*").execute().data or []
    dict_teams_all = {t["name"]: t["id"] for t in teams_list_all}

    statuts = get_statuts_disponibilite()
    ids_blesses = {aid for aid, s in statuts.items() if s["statut"] == "blesse"}
    n_blesses = len(ids_blesses)
    n_dispo = len(dict_athletes) - n_blesses

    st.markdown("#### 🩹 Disponibilité de l'effectif")
    c_stat1, c_stat2, c_stat3 = st.columns(3)
    c_stat1.metric("👥 Effectif total", len(dict_athletes))
    c_stat2.metric("✅ Disponibles", n_dispo)
    c_stat3.metric("🚑 En réathlétisation", n_blesses)

    st.markdown("---")
    st.subheader("🚨 Alertes récentes")
    alertes_resume = alertes_non_vues()
    if not alertes_resume:
        st.success("Aucune alerte récente (douleur, blessure, RPE, valeurs extrêmes).")
    else:
        st.warning(f"{len(alertes_resume)} alerte(s) à consulter — détail et filtres dans l'onglet « 🔔 Alertes ».")
        for a in alertes_resume[:5]:
            st.markdown(f"- {ICONES_ALERTES.get(a['type'], '⚠️')} **{a['athlete']}** · {a['seance']} ({a['date']}) — {a['message']}")

    st.markdown("---")
    tab_nouvelle, tab_existantes, tab_rpe = st.tabs(["🆕 Planifier une nouvelle séance", "📋 Séances planifiées (modifier / supprimer)", "🚫 RPE obligatoire"])

    # ------------------------------------------------------------------
    # Nouvelle séance
    # ------------------------------------------------------------------
    with tab_nouvelle:
        def label_avec_statut(nom):
            aid = dict_athletes[nom]
            return f"🚑 {nom} (réathlétisation)" if aid in ids_blesses else nom

        noms_tries = sorted(dict_athletes.keys())
        labels_affiches = {label_avec_statut(n): n for n in noms_tries}
        options_cible = ["-- Tous les athlètes --"] + [f"🛡️ Équipe : {n}" for n in sorted(dict_teams_all.keys())] + list(labels_affiches.keys())

        col_a, col_b = st.columns(2)
        with col_a:
            title = st.text_input("Titre de la séance", key="plan_titre")
            event_type = st.selectbox("Type d'événement", ["training", "match"], key="plan_type")
            cible_label = st.selectbox("Pour qui ?", options_cible, key="plan_cible")
            exclure_blesses = st.checkbox(
                "🚑 Exclure automatiquement les joueurs en réathlétisation (tous les athlètes / équipe)",
                value=True, key="plan_excl"
            )
            location = st.text_input("Lieu", key="plan_lieu")
            definir_rpe = st.checkbox("🎯 Définir un RPE cible pour cette séance", value=True, key="plan_def_rpe")
            rpe_cible = st.number_input("RPE cible (1-10)", min_value=1.0, max_value=10.0, value=7.0, step=0.5, key="plan_rpe_cible") if definir_rpe else None

        with col_b:
            event_date = date_fr("Date de la séance", datetime.now(), key="plan_date")
            start_time = st.time_input("Heure de début", datetime.strptime("10:00", "%H:%M").time(), key="plan_h1")
            end_time = st.time_input("Heure de fin", datetime.strptime("11:30", "%H:%M").time(), key="plan_h2")

        st.caption("📝 Chaque athlète recevra automatiquement un questionnaire de présence (présence / blessure / douleur) à remplir jusqu'au début de la séance, et un RPE (1-10) à remplir après la séance.")
        st.markdown("---")
        is_recurring = st.checkbox("🔄 Activer la répétition hebdomadaire", value=False, key="plan_rec")
        until_date = date_fr("Date de fin de la répétition", event_date + timedelta(days=60), key="plan_rec_fin") if is_recurring else None

        if st.button("🚀 Planifier la/les séance(s)", type="primary", key="btn_planifier"):
            if not title:
                st.error("Veuillez saisir un titre.")
            else:
                if cible_label == "-- Tous les athlètes --":
                    target_ids = [aid for nom, aid in dict_athletes.items() if not (exclure_blesses and aid in ids_blesses)]
                elif cible_label.startswith("🛡️ Équipe : "):
                    tid = dict_teams_all[cible_label.replace("🛡️ Équipe : ", "")]
                    target_ids = [a["id"] for a in athletes_list if a.get("team_id") == tid and not (exclure_blesses and a["id"] in ids_blesses)]
                else:
                    target_ids = [dict_athletes[labels_affiches[cible_label]]]

                dates_to_schedule = [event_date]
                if is_recurring and until_date:
                    curr = event_date + timedelta(days=7)
                    while curr <= until_date:
                        dates_to_schedule.append(curr)
                        curr += timedelta(days=7)

                events_to_insert = []
                for d in dates_to_schedule:
                    dt_start = datetime.combine(d, start_time)
                    dt_end = datetime.combine(d, end_time)
                    for a_id in target_ids:
                        e_data = {
                            "title": title, "event_type": event_type,
                            "start_time": dt_start.isoformat(), "end_time": dt_end.isoformat(),
                            "location": location or "Non spécifié", "athlete_id": a_id, "coach_id": mon_id,
                        }
                        if rpe_cible is not None:
                            e_data["target_rpe"] = rpe_cible
                        events_to_insert.append(e_data)

                if not events_to_insert:
                    st.warning("Aucun joueur disponible à programmer.")
                else:
                    _, ignores, err = inserer_avec_repli("events", events_to_insert, ["target_rpe", "coach_id"])
                    if err:
                        st.error(f"Erreur Supabase : {err}")
                    else:
                        obtenir_ou_creer_rpe_auto()
                        obtenir_ou_creer_presence_auto()
                        flash_succes(f"Séance « {title} » planifiée : {len(dates_to_schedule)} date(s) × {len(target_ids)} joueur(s). "
                                     "Questionnaire de présence et RPE ajoutés automatiquement.")
                        if "target_rpe" in ignores:
                            flash_succes("Le RPE cible n'a pas pu être enregistré : la colonne `target_rpe` n'existe pas encore. "
                                         "Exécutez une fois ce SQL dans Supabase puis replanifiez :\n\n```sql\nalter table events add column if not exists target_rpe numeric;\n```", "avertissement")
                        st.session_state.pop("_cache_alertes", None)
                        st.rerun()

    # ------------------------------------------------------------------
    # Séances planifiées : effectif + calendrier + modification
    # ------------------------------------------------------------------
    with tab_existantes:
        st.markdown("#### 👁️ Affichage du planning")
        vue_planning = st.selectbox("Voir le planning de :", ["Mon planning global (toutes mes séances)", "Une équipe spécifique", "Un joueur spécifique"], key="select_vue_planning_coach")
        tous_events = mes_evenements(supabase.table("events").select("*").order("start_time", desc=True).execute().data or [])

        if vue_planning == "Une équipe spécifique" and dict_teams_all:
            eq_choisie_p = st.selectbox("Choisir l'équipe :", list(dict_teams_all.keys()), key="select_eq_plan_spec")
            ids_eq_athletes = {a["id"] for a in athletes_list if a.get("team_id") == dict_teams_all[eq_choisie_p]}
            tous_events = [e for e in tous_events if e.get("athlete_id") in ids_eq_athletes]
        elif vue_planning == "Un joueur spécifique" and dict_athletes:
            joueur_choisi_p = st.selectbox("Choisir le joueur :", list(dict_athletes.keys()), key="select_joueur_plan_spec")
            tous_events = [e for e in tous_events if e.get("athlete_id") == dict_athletes[joueur_choisi_p]]

        groupes = groupes_seances(tous_events)
        groupes_par_cle = {"||".join(k): v for k, v in groupes.items()}

        if not tous_events:
            st.info("Aucune séance planifiée pour cette sélection.")
        else:
            reponses_events = obtenir_reponses_events([e["id"] for e in tous_events])

            # ---- Effectif des prochaines séances ----
            now_loc = maintenant_local()
            prochaines = sorted([k for k in groupes if (parse_dt(k[1]) or now_loc) >= now_loc - timedelta(hours=3)], key=lambda k: k[1])[:6]
            with st.expander("👥 Effectif des prochaines séances (selon les réponses de présence)", expanded=True):
                if not prochaines:
                    st.caption("Aucune séance à venir.")
                else:
                    lignes_eff = []
                    for k in prochaines:
                        eff = calculer_effectif(groupes[k], reponses_events, noms_by_id)
                        lignes_eff.append({"Séance": k[0], "Date": fmt_date_fr(k[1], True), "Prévus": len(groupes[k]),
                                           "✅ Disponibles": len(eff["disponible"]), "❌ Absents": len(eff["absent"]),
                                           "🩹 Blessés / douleur": len(eff["indispo"]), "❓ Sans réponse": len(eff["sans_reponse"])})
                    st.dataframe(pd.DataFrame(lignes_eff), use_container_width=True, hide_index=True)
                    st.caption("Un joueur est compté ✅ s'il répond Présent = Oui, Blessure = Non et Douleur = Non / Aucune / Rien. Clique sur une séance dans le calendrier pour voir la liste des joueurs.")

            # ---- Calendrier ----
            events_par_jour = {}
            for k in groupes:
                d0 = parse_dt(k[1])
                if d0:
                    events_par_jour.setdefault(d0.date(), []).append(k)
            for lst in events_par_jour.values():
                lst.sort(key=lambda k: k[1])

            if "cal_mois_ref" not in st.session_state:
                st.session_state.cal_mois_ref = datetime.now().date().replace(day=1)
            if "cal_seance_sel" not in st.session_state:
                st.session_state.cal_seance_sel = None

            c_nav1, c_nav2, c_nav3 = st.columns([1, 3, 1])
            with c_nav1:
                if st.button("◀ Mois précédent", use_container_width=True, key="plan_mois_prec"):
                    ref = st.session_state.cal_mois_ref
                    st.session_state.cal_mois_ref = (ref.replace(day=1) - timedelta(days=1)).replace(day=1)
                    st.rerun()
            with c_nav2:
                ref = st.session_state.cal_mois_ref
                st.markdown(f"<h4 style='text-align:center;'>📅 {MOIS_FR[ref.month - 1].capitalize()} {ref.year}</h4>", unsafe_allow_html=True)
            with c_nav3:
                if st.button("Mois suivant ▶", use_container_width=True, key="plan_mois_suiv"):
                    ref = st.session_state.cal_mois_ref
                    st.session_state.cal_mois_ref = (ref.replace(day=28) + timedelta(days=4)).replace(day=1)
                    st.rerun()

            annee, mois = st.session_state.cal_mois_ref.year, st.session_state.cal_mois_ref.month
            for c, jl in zip(st.columns(7), JOURS_FR):
                c.markdown(f"<div style='text-align:center; color:#94a3b8; font-weight:600;'>{jl}</div>", unsafe_allow_html=True)

            for semaine in _calendar.monthcalendar(annee, mois):
                for c, jour_num in zip(st.columns(7), semaine):
                    if jour_num == 0:
                        c.markdown("&nbsp;", unsafe_allow_html=True)
                        continue
                    date_cell = datetime(annee, mois, jour_num).date()
                    est_aujourdhui = date_cell == datetime.now().date()
                    style_jour = "color:#38bdf8; font-weight:800;" if est_aujourdhui else "color:#f1f5f9; font-weight:600;"
                    c.markdown(f"<div style='{style_jour}'>{jour_num}</div>", unsafe_allow_html=True)
                    for k in events_par_jour.get(date_cell, [])[:4]:
                        grp = groupes[k]
                        emoji_type = "⚔️" if grp[0].get("event_type") == "match" else "🏋️"
                        suffixe = f" ×{len(grp)}" if len(grp) > 1 else ""
                        aide = f"{k[0]} — {fmt_date_fr(k[1], True)} — " + (", ".join(noms_by_id.get(e.get('athlete_id'), '?') for e in grp[:6]) + ("…" if len(grp) > 6 else ""))
                        if c.button(f"{emoji_type} {k[0][:9]}{suffixe}", key=f"cal_btn_{hid('||'.join(k))}", help=aide, use_container_width=True):
                            st.session_state.cal_seance_sel = "||".join(k)
                            st.rerun()
                    if len(events_par_jour.get(date_cell, [])) > 4:
                        c.caption(f"+{len(events_par_jour[date_cell]) - 4} autre(s)")

            st.markdown("---")
            cle_sel = st.session_state.cal_seance_sel
            grp_sel = groupes_par_cle.get(cle_sel) if cle_sel else None

            if grp_sel:
                ev_sel = grp_sel[0]
                ids_groupe = [e["id"] for e in grp_sel]
                gid = hid(cle_sel)
                st.subheader(f"✏️ {ev_sel.get('title')} — {fmt_date_fr(ev_sel.get('start_time'), True)}")

                # ---- Effectif de la séance ----
                eff = calculer_effectif(grp_sel, reponses_events, noms_by_id)
                st.markdown("##### 👥 Effectif de la séance")
                e1, e2, e3, e4, e5 = st.columns(5)
                e1.metric("Joueurs prévus", len(grp_sel))
                e2.metric("✅ Disponibles", len(eff["disponible"]))
                e3.metric("❌ Absents", len(eff["absent"]))
                e4.metric("🩹 Blessés / douleur", len(eff["indispo"]))
                e5.metric("❓ Sans réponse", len(eff["sans_reponse"]))
                for cle_e, titre_e in [("disponible", "✅ Joueurs disponibles sur la séance"), ("absent", "❌ Absents"),
                                       ("indispo", "🩹 Blessés / douleur (retirés de la séance)"), ("sans_reponse", "❓ N'ont pas encore répondu")]:
                    if eff[cle_e]:
                        st.markdown(f"**{titre_e} ({len(eff[cle_e])}) :** " + ", ".join(x["nom"] + (f" — {x['raison']}" if x["raison"] else "") for x in eff[cle_e]))

                st.markdown("##### ✏️ Modifier la séance" + (f" (s'applique aux {len(grp_sel)} joueurs)" if len(grp_sel) > 1 else ""))
                dt_start_existing = parse_dt(ev_sel.get("start_time")) or datetime.now()
                dt_end_existing = parse_dt(ev_sel.get("end_time")) or dt_start_existing
                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    edit_title = st.text_input("Titre", value=ev_sel.get("title", ""), key=f"edit_title_{gid}")
                    edit_type = st.selectbox("Type", ["training", "match"], index=0 if ev_sel.get("event_type") != "match" else 1, key=f"edit_type_{gid}")
                    if len(grp_sel) == 1:
                        nom_actuel = noms_by_id.get(ev_sel.get("athlete_id"))
                        liste_noms = sorted(dict_athletes.keys())
                        idx_ath = liste_noms.index(nom_actuel) if nom_actuel in liste_noms else 0
                        edit_athlete_nom = st.selectbox("Athlète concerné", liste_noms, index=idx_ath, key=f"edit_ath_{gid}")
                    else:
                        edit_athlete_nom = None
                        st.caption("Joueurs : " + ", ".join(sorted(noms_by_id.get(e.get("athlete_id"), "?") for e in grp_sel)))
                    edit_location = st.text_input("Lieu", value=ev_sel.get("location", "") or "", key=f"edit_loc_{gid}")
                    cible_existante = next((e.get("target_rpe") for e in grp_sel if e.get("target_rpe") is not None), None)
                    edit_def_rpe = st.checkbox("🎯 RPE cible défini", value=cible_existante is not None, key=f"edit_defrpe_{gid}")
                    edit_rpe = st.number_input("RPE cible (1-10)", 1.0, 10.0, float(cible_existante) if cible_existante is not None else 7.0, 0.5, key=f"edit_rpe_{gid}") if edit_def_rpe else None
                with c_e2:
                    edit_date = date_fr("Date", value=dt_start_existing.date(), key=f"edit_date_{gid}")
                    edit_start = st.time_input("Heure de début", value=dt_start_existing.time(), key=f"edit_start_{gid}")
                    edit_end = st.time_input("Heure de fin", value=dt_end_existing.time(), key=f"edit_end_{gid}")

                c_b1, c_b2, c_b3 = st.columns(3)
                with c_b1:
                    if st.button("💾 Enregistrer", type="primary", key=f"save_ev_{gid}"):
                        maj = {
                            "title": edit_title, "event_type": edit_type,
                            "location": edit_location or "Non spécifié",
                            "start_time": datetime.combine(edit_date, edit_start).isoformat(),
                            "end_time": datetime.combine(edit_date, edit_end).isoformat(),
                            "target_rpe": edit_rpe,
                        }
                        if edit_athlete_nom:
                            maj["athlete_id"] = dict_athletes[edit_athlete_nom]
                        ok, ignores, err = maj_avec_repli("events", maj, ids_groupe, ["target_rpe"])
                        if not ok:
                            st.error(f"Erreur lors de la mise à jour : {err}")
                        else:
                            st.session_state.cal_seance_sel = None
                            st.session_state.pop("_cache_alertes", None)
                            flash_succes(f"Séance « {edit_title} » mise à jour ({len(ids_groupe)} joueur(s)).")
                            if ignores:
                                flash_succes("Le RPE cible n'a pas été enregistré (colonne `target_rpe` absente). Exécutez : `alter table events add column if not exists target_rpe numeric;` dans Supabase.", "avertissement")
                            st.rerun()
                with c_b2:
                    if st.button("❌ Supprimer", type="primary", key=f"del_ev_{gid}"):
                        supabase.table("events").delete().in_("id", ids_groupe).execute()
                        st.session_state.cal_seance_sel = None
                        flash_succes(f"Séance « {ev_sel.get('title')} » supprimée ({len(ids_groupe)} joueur(s)).")
                        st.rerun()
                with c_b3:
                    if st.button("✖ Fermer", key=f"close_ev_{gid}"):
                        st.session_state.cal_seance_sel = None
                        st.rerun()
            else:
                st.info("👆 Clique sur une séance du calendrier pour voir son effectif et la modifier.")

    with tab_rpe:
        st.subheader("🚫 RPE obligatoire après la séance")
        st.caption(
            "Par défaut, chaque athlète doit remplir son RPE (1-10) après chaque séance, dans l'heure qui suit. "
            "Ici, vous pouvez retirer cette obligation pour un athlète sur une ou plusieurs séances, "
            "ou pour tous les joueurs d'une séance. Vous pouvez aussi la remettre."
        )
        if st.session_state.get("flash_rpe"):
            st.success(st.session_state.pop("flash_rpe"))

        mode_rpe = st.radio("Retirer le RPE pour :", ["👤 Un athlète (une ou plusieurs séances)", "👥 Une séance entière (tous les joueurs)"],
                            horizontal=True, key="rpe_mode_radio")
        evs_rpe = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []
        inv_rpe = {v: k for k, v in dict_athletes.items()}

        def _lib_ev(e):
            d = fmt_date_fr(e.get("start_time"), True)
            return f"{e.get('title', 'Séance')} — {d}" + ("  🚫 RPE retiré" if e.get("rpe_desactive") else "")

        ids_cibles = []
        if not dict_athletes or not evs_rpe:
            st.info("Aucune séance planifiée pour le moment.")
        elif mode_rpe.startswith("👤"):
            nom_rpe = st.selectbox("Athlète :", sorted(dict_athletes.keys()), key="rpe_sel_athlete")
            evs_ath = [e for e in evs_rpe if e.get("athlete_id") == dict_athletes[nom_rpe]]
            par_id = {e["id"]: e for e in evs_ath}
            ids_cibles = st.multiselect("Séance(s) concernée(s) :", list(par_id.keys()), format_func=lambda i: _lib_ev(par_id[i]), key="rpe_sel_events_ath")
        else:
            groupes_rpe = {}
            for e in evs_rpe:
                groupes_rpe.setdefault((e.get("title"), e.get("start_time")), []).append(e)
            cles = st.multiselect(
                "Séance(s) concernée(s) :", list(groupes_rpe.keys()),
                format_func=lambda k: f"{k[0]} — {fmt_date_fr(k[1], True)} ({len(groupes_rpe[k])} joueur(s))",
                key="rpe_sel_events_groupe"
            )
            ids_cibles = [e["id"] for k in cles for e in groupes_rpe[k]]

        c_r1, c_r2 = st.columns(2)
        for colonne, valeur, libelle, message in [
            (c_r1, True, "🚫 Retirer le RPE obligatoire", "RPE retiré pour {n} séance(s)."),
            (c_r2, False, "✅ Remettre le RPE obligatoire", "RPE remis pour {n} séance(s)."),
        ]:
            with colonne:
                if st.button(libelle, key=f"btn_rpe_{valeur}", disabled=not ids_cibles, type="primary" if valeur else "secondary"):
                    try:
                        supabase.table("events").update({"rpe_desactive": valeur}).in_("id", ids_cibles).execute()
                        st.session_state["flash_rpe"] = message.format(n=len(ids_cibles))
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Impossible d'enregistrer : {ex}")
                        st.info("Si l'erreur parle d'une colonne « rpe_desactive » inconnue, exécutez une fois ceci dans Supabase (SQL Editor) puis réessayez :")
                        st.code("alter table events add column if not exists rpe_desactive boolean default false;", language="sql")

        retires = [e for e in evs_rpe if e.get("rpe_desactive")]
        if retires:
            st.markdown("#### Séances dont le RPE est retiré")
            st.dataframe(pd.DataFrame([{"Athlète": inv_rpe.get(e.get("athlete_id"), "?"), "Séance": e.get("title"), "Date": fmt_date_fr(e.get("start_time"), True)} for e in retires]),
                         use_container_width=True)

# =====================================================================
# PAGE : ALERTES
# =====================================================================
elif menu == "🔔 Alertes":
    st.header("🔔 Alertes")
    afficher_flash()
    st.caption("Douleurs musculaires, blessures, RPE trop éloigné du RPE cible, réponses wellness et données GPS extrêmes (très éloignées du groupe ou des valeurs habituelles du joueur).")

    with st.expander("⚙️ Réglages des alertes"):
        opts_jours = [7, 14, 30, 60, 90]
        jours_sel = st.selectbox("Période analysée :", opts_jours, index=opts_jours.index(st.session_state.get("_al_jours", 30)) if st.session_state.get("_al_jours", 30) in opts_jours else 2,
                                 format_func=lambda j: f"{j} derniers jours", key="al_w_jours")
        seuil_j = st.number_input("RPE d'un joueur : alerte si l'écart avec le RPE cible est d'au moins", 0.5, 9.0, float(st.session_state.get("_al_seuil_j", 2.0)), 0.5, key="al_w_sj")
        seuil_e = st.number_input("RPE moyen d'un groupe : alerte si l'écart avec le RPE cible est d'au moins", 0.5, 9.0, float(st.session_state.get("_al_seuil_e", 2.0)), 0.5, key="al_w_se")
        st.session_state["_al_jours"], st.session_state["_al_seuil_j"], st.session_state["_al_seuil_e"] = jours_sel, seuil_j, seuil_e

    c_a1, c_a2, c_a3 = st.columns([2, 1, 1])
    with c_a1:
        types_sel = st.multiselect("Types d'alertes :", list(NOMS_ALERTES.keys()), default=list(NOMS_ALERTES.keys()),
                                   format_func=lambda t: f"{ICONES_ALERTES[t]} {NOMS_ALERTES[t]}", key="al_w_types")
    with c_a2:
        afficher_vues = st.checkbox("Afficher aussi les alertes vues", value=False, key="al_w_vues")
    with c_a3:
        actualiser = st.button("🔄 Actualiser", use_container_width=True, key="al_btn_refresh")

    toutes = get_alertes_coach(force=actualiser)
    vues = st.session_state.setdefault("alertes_vues", set())
    affichees = [a for a in toutes if a["type"] in types_sel and (afficher_vues or a["cle"] not in vues)]

    m1, m2, m3 = st.columns(3)
    m1.metric("Alertes à traiter", len([a for a in toutes if a["cle"] not in vues]))
    m2.metric("🔴 Priorité haute", len([a for a in toutes if a["gravite"] == "haute" and a["cle"] not in vues]))
    m3.metric("Déjà vues", len([a for a in toutes if a["cle"] in vues]))

    if not affichees:
        st.success("Aucune alerte à afficher. 👌")
    else:
        if st.button("✔️ Tout marquer comme vu", key="al_btn_all_seen"):
            vues.update(a["cle"] for a in affichees)
            flash_succes(f"{len(affichees)} alerte(s) marquée(s) comme vue(s).")
            st.rerun()
        for a in affichees:
            boite = st.error if a["gravite"] == "haute" else st.warning
            etat = " *(vue)*" if a["cle"] in vues else ""
            boite(f"{ICONES_ALERTES.get(a['type'], '⚠️')} **{a['athlete']}** — {a['seance']} ({a['date']}){etat}\n\n{a['message']}")
            if a["cle"] not in vues:
                if st.button("✔️ Marquer comme vue", key=f"al_seen_{hid(a['cle'])}"):
                    vues.add(a["cle"])
                    st.rerun()
        st.caption("Les alertes marquées comme vues sont masquées pour cette session ; elles réapparaissent si vous vous reconnectez.")

# =====================================================================
# PAGE : EFFECTIF
# =====================================================================
elif menu == "👥 Effectif":
    st.header("👥 Effectif")
    afficher_flash()

    teams_eff = supabase.table("teams").select("*").execute().data or []
    if not teams_eff:
        st.info("Aucune équipe. Créez-en une dans « ⚙️ Gestion des profils ».")
    else:
        dict_teams_eff = {t["name"]: t["id"] for t in teams_eff}
        eq_nom = st.selectbox("🛡️ Équipe :", sorted(dict_teams_eff.keys()), key="eff_equipe_sel")
        eq_id = dict_teams_eff[eq_nom]
        tous_ath = supabase.table("profiles").select("*").eq("role", "athlete").execute().data or []
        joueurs = sorted([p for p in tous_ath if p.get("team_id") == eq_id], key=lambda p: (p.get("full_name") or "").lower())

        COLS_INFO = ["jersey_number", "birth_date", "height_cm", "weight_kg", "position", "notes"]
        if joueurs and any(c not in joueurs[0] for c in COLS_INFO):
            st.warning("Certaines colonnes (numéro, naissance, taille, poids, poste, notes) n'existent pas encore dans la table `profiles`. Exécutez ce SQL une fois dans Supabase, puis rechargez la page :")
            st.code(SQL_MIGRATION, language="sql")

        def _age(d):
            if not d:
                return None
            n = maintenant_local().date()
            return n.year - d.year - ((n.month, n.day) < (d.month, d.day))

        def _num(v):
            try:
                return None if v in (None, "") or v != v else float(v)
            except (ValueError, TypeError):
                return None

        lignes_eff = []
        for p in joueurs:
            bd = parse_dt(p.get("birth_date"))
            bd = bd.date() if bd else None
            lignes_eff.append({
                "Nom & prénom": p.get("full_name") or "", "N°": _num(p.get("jersey_number")), "Date de naissance": bd,
                "Âge": _age(bd), "Taille (cm)": _num(p.get("height_cm")), "Poids (kg)": _num(p.get("weight_kg")),
                "Poste": p.get("position") or "", "Notes / informations": p.get("notes") or "",
            })

        if not joueurs:
            st.info("Aucun joueur dans cette équipe pour le moment. Ajoutez-en ci-dessous.")
        else:
            df_eff = pd.DataFrame(lignes_eff)
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Joueurs", len(df_eff))
            k2.metric("Âge moyen", f"{df_eff['Âge'].dropna().mean():.1f} ans" if df_eff["Âge"].notna().any() else "—")
            k3.metric("Taille moyenne", f"{df_eff['Taille (cm)'].dropna().mean():.0f} cm" if df_eff["Taille (cm)"].notna().any() else "—")
            k4.metric("Poids moyen", f"{df_eff['Poids (kg)'].dropna().mean():.1f} kg" if df_eff["Poids (kg)"].notna().any() else "—")

            st.caption("Double-cliquez sur une case pour la modifier, puis cliquez sur « Enregistrer ». L'âge se calcule à partir de la date de naissance.")
            edite = st.data_editor(
                df_eff, key=f"eff_editor_{eq_id}", hide_index=True, use_container_width=True, num_rows="fixed", disabled=["Âge"],
                column_config={
                    "N°": st.column_config.NumberColumn("N°", min_value=0, max_value=999, step=1, format="%d"),
                    "Date de naissance": st.column_config.DateColumn("Date de naissance", format="DD/MM/YYYY", min_value=datetime(1950, 1, 1).date(), max_value=datetime.now().date()),
                    "Âge": st.column_config.NumberColumn("Âge", format="%d ans"),
                    "Taille (cm)": st.column_config.NumberColumn("Taille (cm)", min_value=100, max_value=250, step=1, format="%d"),
                    "Poids (kg)": st.column_config.NumberColumn("Poids (kg)", min_value=30, max_value=200, step=0.5, format="%.1f"),
                },
            )
            if st.button("💾 Enregistrer les modifications de l'effectif", type="primary", key=f"eff_save_{eq_id}"):
                erreurs, nb = [], 0
                for p, (_, nouv) in zip(joueurs, edite.iterrows()):
                    def _d(v):
                        return None if v is None or v != v else v
                    bd_new = _d(nouv["Date de naissance"])
                    maj = {
                        "full_name": str(nouv["Nom & prénom"]).strip() or p.get("full_name"),
                        "jersey_number": None if _d(nouv["N°"]) is None else int(nouv["N°"]),
                        "birth_date": bd_new.isoformat() if hasattr(bd_new, "isoformat") else None,
                        "height_cm": None if _d(nouv["Taille (cm)"]) is None else float(nouv["Taille (cm)"]),
                        "weight_kg": None if _d(nouv["Poids (kg)"]) is None else float(nouv["Poids (kg)"]),
                        "position": str(nouv["Poste"] or "").strip() or None,
                        "notes": str(nouv["Notes / informations"] or "").strip() or None,
                    }
                    avant = {"full_name": p.get("full_name"), "jersey_number": p.get("jersey_number"), "birth_date": p.get("birth_date"),
                             "height_cm": p.get("height_cm"), "weight_kg": p.get("weight_kg"), "position": p.get("position"), "notes": p.get("notes")}
                    def _n(v):
                        if v is None or v == "":
                            return None
                        try:
                            return round(float(v), 4)
                        except (ValueError, TypeError):
                            return str(v).strip()
                    if {k: _n(v) for k, v in maj.items()} == {k: _n(v) for k, v in avant.items()}:
                        continue
                    try:
                        supabase.table("profiles").update(maj).eq("id", p["id"]).execute()
                        nb += 1
                    except Exception as ex:
                        erreurs.append(f"{p.get('full_name')} : {ex}")
                if erreurs:
                    st.error("Erreur lors de l'enregistrement :")
                    for e in erreurs:
                        st.code(e)
                    st.info("Si l'erreur parle d'une colonne inconnue, exécutez le SQL ci-dessus (une seule fois) puis réessayez.")
                    st.code(SQL_MIGRATION, language="sql")
                else:
                    flash_succes(f"Effectif de l'équipe « {eq_nom} » enregistré ({nb} joueur(s) modifié(s)).")
                    st.rerun()

        st.markdown("---")
        st.markdown("##### ➕ Ajouter un joueur existant à cette équipe")
        hors_equipe = sorted([p for p in tous_ath if p.get("team_id") != eq_id and p.get("full_name")], key=lambda p: p["full_name"].lower())
        if hors_equipe:
            choix_ajout = st.selectbox("Joueur :", [p["id"] for p in hors_equipe], format_func=lambda i: next(p["full_name"] for p in hors_equipe if p["id"] == i), key=f"eff_add_{eq_id}")
            if st.button("Ajouter à l'équipe", key=f"eff_add_btn_{eq_id}"):
                supabase.table("profiles").update({"team_id": eq_id}).eq("id", choix_ajout).execute()
                flash_succes(f"Joueur ajouté à l'équipe « {eq_nom} ».")
                st.rerun()
        else:
            st.caption("Tous les athlètes sont déjà dans cette équipe. Pour créer un nouvel athlète : « ⚙️ Gestion des profils » → Comptes.")

# =====================================================================
# PAGE : FICHIERS & RAPPORTS GPS
# =====================================================================
elif menu == "📁 Fichiers & Rapports GPS":
    st.header("📁 Fichiers de Séances & Rapports GPS")
    afficher_flash()

    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
    dict_athletes = {a.get("full_name"): a["id"] for a in res_athletes if a.get("full_name")}
    res_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []

    dict_events = {}
    dict_events_info = {}
    for ev in res_events:
        ev_id = ev["id"]
        ev_title = ev.get("title") or "Séance"
        ev_start = ev.get("start_time", "")
        ev_ath_id = ev.get("athlete_id")
        date_str = fmt_date_fr(ev_start, True)
        ath_name = next((name for name, aid in dict_athletes.items() if aid == ev_ath_id), "Tous")
        label = f"{ev_title} ({date_str}) - Athlète : {ath_name}"
        dict_events[label] = ev
        dict_events_info[ev_id] = {"title": ev_title, "date": date_str, "athlete": ath_name}

    tab_upload, tab_list, tab_gps = st.tabs([
        "📤 Joindre un PDF à une séance",
        "📚 Documents publiés (Voir / Gérer)",
        "🛰️ Importer un rapport GPS (xlsx)",
    ])

    with tab_upload:
        if not dict_events:
            st.warning("Aucune séance planifiée.")
        else:
            groupes_ev = groupes_seances(res_events)
            cles_ev = sorted(groupes_ev.keys(), key=lambda k: k[1], reverse=True)
            cle_pdf = st.selectbox("📌 Choisir la séance :", cles_ev, format_func=lambda k: f"{k[0]} — {fmt_date_fr(k[1], True)} ({len(groupes_ev[k])} joueur(s))", key="sel_evt_pdf_up")
            grp_pdf = groupes_ev[cle_pdf]
            session_title = st.text_input("Nom du document / Titre du PDF :", value=cle_pdf[0], key="inp_titre_pdf")
            description = st.text_area("Instructions :", key="inp_desc_pdf")
            uploaded_file = st.file_uploader("Fichier PDF ou Image", type=["pdf", "png", "jpg", "jpeg"], key="up_pdf_file")
            st.caption(f"Le document sera visible par les {len(grp_pdf)} joueur(s) de cette séance.")

            if st.button("🚀 Publier sur la séance", type="primary", key="btn_publier_pdf"):
                if not session_title or not uploaded_file:
                    st.error("Renseignez un nom et un fichier.")
                else:
                    file_bytes = uploaded_file.getvalue()
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    mime_type = uploaded_file.type or "application/octet-stream"
                    storage_path = f"{int(datetime.now().timestamp())}_{uploaded_file.name}"
                    try:
                        file_url = upload_file_direct_http("session-files", storage_path, file_bytes, mime_type)
                    except Exception:
                        file_url = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode('utf-8')}"
                    horodatage = datetime.now().isoformat()
                    records = [{
                        "title": session_title, "description": description, "file_name": uploaded_file.name, "file_url": file_url,
                        "file_type": file_ext, "athlete_id": e.get("athlete_id"), "event_id": e["id"], "created_at": horodatage,
                    } for e in grp_pdf]
                    try:
                        supabase.table("session_files").insert(records).execute()
                        flash_succes(f"PDF envoyé : « {session_title} » est publié sur la séance « {cle_pdf[0]} » pour {len(records)} joueur(s).")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erreur lors de l'envoi du document : {ex}")

    with tab_list:
        st.subheader("📚 Documents déjà publiés sur les séances")
        files_db = supabase.table("session_files").select("*").order("created_at", desc=True).execute().data or []
        if not files_db:
            st.info("Aucun document publié pour le moment.")
        else:
            groupes_f = {}
            for f in files_db:
                groupes_f.setdefault((f.get("title"), f.get("file_name"), f.get("created_at")), []).append(f)
            for cle_f, lst in groupes_f.items():
                f0 = lst[0]
                ev_info = dict_events_info.get(f0.get("event_id"), {"title": "Séance globale", "date": ""})
                gid_f = hid(str(cle_f))
                with st.expander(f"📄 {f0.get('title')} — Séance : {ev_info['title']} ({ev_info['date']}) · {len(lst)} joueur(s)"):
                    st.write(f"**Fichier :** `{f0.get('file_name')}`")
                    if f0.get("description"):
                        st.write(f"**Instructions :** {f0.get('description')}")
                    f_url = f0.get("file_url", "") or ""
                    if f_url.startswith("data:"):
                        st.download_button("💾 Télécharger / Voir le document", data=base64.b64decode(f_url.split(",", 1)[1]), file_name=f0.get("file_name", "document.pdf"), key=f"dl_doc_{gid_f}")
                    else:
                        st.markdown(f"[🔗 Ouvrir / Consulter le document]({f_url})")

                    ev0 = next((e for e in res_events if e["id"] == f0.get("event_id")), None)
                    freres = [e for e in res_events if ev0 and cle_seance(e) == cle_seance(ev0)]
                    couverts = {f.get("event_id") for f in lst}
                    manquants = [e for e in freres if e["id"] not in couverts]
                    if manquants:
                        st.warning(f"Ce document n'est visible que par {len(lst)} joueur(s) sur {len(freres)} pour cette séance.")
                        if st.button("📤 Rendre visible pour tous les joueurs de la séance", key=f"share_doc_{gid_f}"):
                            copies = [{k: v for k, v in f0.items() if k != "id"} | {"event_id": e["id"], "athlete_id": e.get("athlete_id")} for e in manquants]
                            supabase.table("session_files").insert(copies).execute()
                            flash_succes(f"Document « {f0.get('title')} » partagé avec {len(manquants)} joueur(s) supplémentaire(s).")
                            st.rerun()
                    if st.button("❌ Supprimer ce document", key=f"del_doc_btn_{gid_f}"):
                        supabase.table("session_files").delete().in_("id", [f["id"] for f in lst]).execute()
                        flash_succes(f"Document « {f0.get('title')} » supprimé.")
                        st.rerun()

    with tab_gps:
        st.subheader("🛰️ Importer un rapport GPS (fichier Excel / CSV)")
        st.caption(
            "Chaque joueur du fichier dont le nom correspond à un profil athlète de l'application est enregistré "
            "(accents, majuscules et ordre Nom/Prénom ignorés). Les autres joueurs sont ignorés. "
            "Réimporter la même séance remplace les données déjà importées."
        )
        if not dict_events:
            st.warning("Créez d'abord une séance.")
        else:
            gps_event_label = st.selectbox("📌 Séance concernée :", list(dict_events.keys()), key="gps_event_sel")
            gps_file = st.file_uploader("Fichier GPS", type=["csv", "xlsx", "xls"], key="gps_file_uploader")

            if gps_file:
                file_bytes_content = gps_file.getvalue()
                try:
                    lignes = lire_fichier_gps(file_bytes_content, nom_fichier=gps_file.name)
                except Exception as ex:
                    lignes = []
                    st.error(f"Erreur lecture fichier : {ex}")

                if lignes:
                    apercu, noms_reconnus = [], []
                    for l in lignes:
                        uid = matcher_nom_athlete(l.get("player_name"), dict_athletes)
                        profil = next((n for n, i in dict_athletes.items() if i == uid), None) if uid else None
                        if uid:
                            noms_reconnus.append(f"{l.get('player_name')} → {profil}")
                        apercu.append({"Statut": "✅ Profil trouvé" if uid else "⚪ Pas de profil", "Profil dans l'app": profil or "—", **l})

                    st.write(f"**Aperçu ({len(lignes)} ligne(s) détectée(s)) :**")
                    st.dataframe(pd.DataFrame(apercu), use_container_width=True)

                    if noms_reconnus:
                        st.success(f"✅ {len(noms_reconnus)} joueur(s) du fichier ont un profil et seront importés : " + " ; ".join(noms_reconnus))
                    else:
                        st.warning("⚠️ Aucun joueur du fichier ne correspond à un profil athlète : rien ne sera importé. Vérifiez l'orthographe du nom dans 'Gestion des profils'.")

                    if st.button("💾 Importer ce rapport GPS", type="primary", key="btn_import_gps", disabled=(len(noms_reconnus) == 0)):
                        selected_event = dict_events[gps_event_label]
                        with st.spinner("Import en cours..."):
                            res = enregistrer_rapport_gps(selected_event["id"], [dict(l) for l in lignes], dict_athletes)

                        # Pas de st.rerun() ici : sinon le message disparaît aussitôt.
                        if res["inseres"] > 0:
                            st.success(
                                f"✅ Rapport GPS envoyé : {res['inseres']} ligne(s) enregistrée(s) dans la base : "
                                + ", ".join(res["importes"])
                                + ". Retrouvez-les dans 📊 Analytique → Les données GPS."
                            )
                            if res["verifie"] is not None:
                                st.caption(f"🔎 Vérification : {res['verifie']} ligne(s) relue(s) dans la base pour cette séance.")
                        else:
                            st.error("❌ Aucune ligne n'a pu être enregistrée dans la base.")

                        if res["colonnes_ignorees"]:
                            st.warning(
                                "⚠️ Ces colonnes n'existent pas dans la table `gps_reports` de Supabase, leurs valeurs n'ont donc pas été "
                                "sauvegardées : **" + ", ".join(res["colonnes_ignorees"]) + "**. Pour les conserver, exécutez dans Supabase (SQL Editor) :"
                            )
                            st.code("\n".join(
                                f"alter table gps_reports add column if not exists {c} "
                                + ("timestamptz" if c == "recorded_at" else "double precision") + ";"
                                for c in res["colonnes_ignorees"]
                            ), language="sql")
                        if res["erreurs"]:
                            st.error("Erreur(s) renvoyée(s) par la base de données :")
                            for e in res["erreurs"]:
                                st.code(e)
                            st.info(
                                "💡 Si l'erreur parle de « row-level security » / « permission denied », la clé SUPABASE_KEY utilisée par le site "
                                "est la clé publique (anon) : remplacez-la par la clé **service_role** dans les secrets Streamlit, "
                                "ou ajoutez une policy d'insertion sur `gps_reports`."
                            )
                        if res["non_trouves"]:
                            st.info(f"ℹ️ {len(res['non_trouves'])} joueur(s) du fichier sans profil dans l'application (ignorés).")
                else:
                    st.info("Aucune ligne exploitable trouvée automatiquement. Vérifiez les colonnes de votre fichier ou essayez un export CSV classique.")

# =====================================================================
# PAGE : QUESTIONNAIRES
# =====================================================================
elif menu == "📝 Questionnaires":
    st.header("📝 Gestion complète des Questionnaires")
    afficher_flash()
    st.caption("🤖 Deux questionnaires sont ajoutés automatiquement à chaque séance : « Présence & Blessures » (jusqu'au début de la séance) et « RPE » 1-10 (après la séance). Les questionnaires ci-dessous sont les vôtres.")
    tab_creer, tab_gerer, tab_envoyer, tab_assignes, tab_repondre = st.tabs(["🆕 Créer un modèle", "⚙️ Modifier / Supprimer", "📩 Assigner", "📋 Questionnaires assignés", "✍️ Saisie manuelle"])

    NOMS_FORMATS = {
        "scale": "Échelle numérique", "text": "Texte libre", "number": "Nombre libre",
        FORMAT_BLESSURE: "🚑 Oui/Non (blessure)", FORMAT_DOULEUR: "🩹 Douleur musculaire (texte → alerte)", FORMAT_PRESENCE: "✅ Présence (Oui/Non)",
    }

    with tab_creer:
        q_title = st.text_input("Titre du questionnaire", key="inp_titre_q_new")
        q_type_sel = st.selectbox("Type", ["Pre-Event (Wellness)", "Post-Event (RPE)"], key="sel_type_q_new")
        q_type = "pre_event" if "Pre" in q_type_sel else "post_event"
        if "questions_draft" not in st.session_state:
            st.session_state.questions_draft = []

        new_q_label = st.text_input("Intitulé de la question", key="inp_intitule_q")
        q_format = st.selectbox("Format", ["Échelle numérique", "Texte libre", "Nombre libre", "🚑 Oui/Non (blessure)", "🩹 Douleur musculaire (texte → alerte)"], key="sel_fmt_q")
        scale_max = st.number_input("Échelle : de 1 à", 2, 10, 5, key="num_scale_max_q") if "Échelle" in q_format else None

        if st.button("+ Ajouter la question au modèle", key="btn_add_q_draft"):
            if new_q_label:
                if "Douleur" in q_format:
                    fmt = FORMAT_DOULEUR
                elif "blessure" in q_format.lower():
                    fmt = FORMAT_BLESSURE
                elif "Échelle" in q_format:
                    fmt = "scale"
                elif "Nombre" in q_format:
                    fmt = "number"
                else:
                    fmt = "text"
                st.session_state.questions_draft.append({"label": new_q_label, "format": fmt, "scale_max": scale_max})
                st.rerun()
            else:
                st.error("Saisissez l'intitulé de la question.")

        for idx, q in enumerate(st.session_state.questions_draft):
            extra = f" — échelle 1 à {q['scale_max']}" if q["format"] == "scale" else ""
            st.info(f"Q{idx+1}: {q['label']} ({NOMS_FORMATS.get(q['format'], q['format'])}{extra})")

        if st.button("💾 Enregistrer le questionnaire complet", type="primary", key="btn_save_q_model"):
            if q_title and st.session_state.questions_draft:
                try:
                    supabase.table("questionnaires").insert({"title": q_title, "type": q_type, "questions": st.session_state.questions_draft}).execute()
                    st.session_state.questions_draft = []
                    flash_succes(f"Questionnaire « {q_title} » créé avec succès.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erreur lors de la création : {ex}")
            else:
                st.error("Saisissez un titre et ajoutez au moins une question.")

    with tab_gerer:
        st.subheader("✏️ Modifier ou Supprimer un questionnaire existant")
        q_list_all = [q for q in (supabase.table("questionnaires").select("*").execute().data or []) if not est_questionnaire_auto(q)]
        if not q_list_all:
            st.info("Aucun questionnaire créé.")
        else:
            dict_q_all = {q["title"]: q for q in q_list_all}
            sel_q_mod = st.selectbox("Sélectionner un questionnaire :", list(dict_q_all.keys()), key="sel_q_modify_tab")
            q_sel_obj = dict_q_all[sel_q_mod]
            q_id = q_sel_obj["id"]

            new_q_title = st.text_input("Modifier le titre :", value=q_sel_obj.get("title", ""), key=f"edit_q_title_{q_id}")
            new_q_type = st.selectbox("Modifier le type :", ["pre_event", "post_event"], index=0 if q_sel_obj.get("type") == "pre_event" else 1,
                                      format_func=lambda t: "🌅 Avant la séance (pre_event)" if t == "pre_event" else "🌙 Après la séance (post_event)", key=f"edit_q_type_{q_id}")

            st.markdown("##### Questions actuelles :")
            liste_formats = list(NOMS_FORMATS.keys())
            updated_questions = []
            for i, q_item in enumerate(q_sel_obj.get("questions", [])):
                col_q1, col_q2, col_q3 = st.columns([3, 2, 1.3])
                with col_q1:
                    uq_label = st.text_input(f"Question {i+1}", value=q_item.get("label", ""), key=f"uq_lbl_{q_id}_{i}")
                with col_q2:
                    fmt_actuel = q_item.get("format", "scale")
                    uq_fmt = st.selectbox(f"Format {i+1}", liste_formats, index=liste_formats.index(fmt_actuel) if fmt_actuel in liste_formats else 0,
                                          format_func=lambda f: NOMS_FORMATS[f], key=f"uq_fmt_{q_id}_{i}")
                with col_q3:
                    if uq_fmt == "scale":
                        uq_max = int(st.number_input(f"Échelle 1 à", 2, 10, int(q_item.get("scale_max") or 5), key=f"uq_max_{q_id}_{i}"))
                    else:
                        uq_max = q_item.get("scale_max")
                updated_questions.append({"label": uq_label, "format": uq_fmt, "scale_max": uq_max})
            st.caption("Les réponses déjà enregistrées gardent leur valeur d'origine quand vous changez une échelle.")

            c_mg1, c_mg2 = st.columns(2)
            with c_mg1:
                if st.button("💾 Mettre à jour ce questionnaire", type="primary", key=f"btn_save_mod_q_{q_id}"):
                    supabase.table("questionnaires").update({"title": new_q_title, "type": new_q_type, "questions": updated_questions}).eq("id", q_id).execute()
                    flash_succes(f"Questionnaire « {new_q_title} » mis à jour (questions et échelles).")
                    st.rerun()
            with c_mg2:
                if st.button("❌ Supprimer définitivement ce questionnaire", type="primary", key=f"btn_del_q_{q_id}"):
                    supabase.table("questionnaires").delete().eq("id", q_id).execute()
                    flash_succes(f"Questionnaire « {q_sel_obj.get('title')} » supprimé.")
                    st.rerun()

    with tab_envoyer:
        st.subheader("📩 Assigner un questionnaire")
        q_data = [q for q in (supabase.table("questionnaires").select("*").execute().data or []) if not est_questionnaire_auto(q)]
        a_data = supabase.table("profiles").select("id, full_name, team_id").eq("role", "athlete").execute().data or []
        t_data = supabase.table("teams").select("*").execute().data or []
        if not q_data:
            st.info("Créez d'abord un questionnaire.")
        elif not a_data:
            st.info("Aucun athlète enregistré.")
        else:
            dict_q_obj = {q["title"]: q for q in q_data}
            dict_a = {a["full_name"]: a["id"] for a in a_data if a.get("full_name")}
            dict_a_inv = {v: k for k, v in dict_a.items()}
            dict_t = {t["name"]: t["id"] for t in t_data}

            sel_q_title = st.selectbox("Choisir le questionnaire :", list(dict_q_obj.keys()), key="sel_q_assign_title")
            q_obj_sel = dict_q_obj[sel_q_title]

            timing_mode = st.radio("Ce questionnaire se remplit :", ["🌅 Avant la séance (ex : Wellness)", "🌙 Après la séance (ex : RPE)"],
                                   index=0 if q_obj_sel.get("type") == "pre_event" else 1, key=f"rad_timing_mode_assign_{q_obj_sel['id']}")
            est_pre = timing_mode.startswith("🌅")
            if est_pre:
                minutes_val = st.number_input("⏰ Combien de minutes AVANT chaque séance ce questionnaire s'ouvre-t-il ?", min_value=5, max_value=1440,
                                              value=int(q_obj_sel.get("trigger_minutes") or 60), step=5, key=f"num_min_avant_assign_{q_obj_sel['id']}")
                st.caption("Il se ferme au début de la séance.")
            else:
                minutes_val = st.number_input("⏰ Combien de minutes APRÈS la fin de la séance ce questionnaire reste-t-il ouvert ?", min_value=5, max_value=1440,
                                              value=int(q_obj_sel.get("post_window_minutes") or 180), step=5, key=f"num_min_apres_assign_{q_obj_sel['id']}")
                st.caption("Il s'ouvre à la fin de la séance.")

            cible_mode = st.radio("Assigner à :", ["👤 Un ou plusieurs athlètes", "🛡️ Une équipe"], horizontal=True, key="rad_cible_assign")
            if cible_mode.startswith("👤"):
                sel_a = st.multiselect("Athlète(s) concerné(s) :", list(dict_a.keys()), key="multisel_athletes_assign")
                ids_cibles = [dict_a[n] for n in sel_a]
                libelle_cible = f"{len(ids_cibles)} athlète(s)"
            else:
                if not dict_t:
                    st.warning("Aucune équipe. Créez-en une dans « ⚙️ Gestion des profils ».")
                    ids_cibles, libelle_cible = [], ""
                else:
                    eq_assign = st.selectbox("Équipe :", sorted(dict_t.keys()), key="sel_equipe_assign")
                    ids_cibles = [a["id"] for a in a_data if a.get("team_id") == dict_t[eq_assign]]
                    libelle_cible = f"l'équipe {eq_assign} ({len(ids_cibles)} joueur(s))"
                    if ids_cibles:
                        st.caption("Joueurs concernés : " + ", ".join(sorted(dict_a_inv[i] for i in ids_cibles if i in dict_a_inv)) + ". Les joueurs ajoutés plus tard à l'équipe ne seront pas inclus automatiquement.")
                    else:
                        st.warning("Cette équipe n'a aucun joueur.")

            portee_choix = st.radio("Portée de l'assignation :", ["Toutes les séances", "Une séance précise"], key="rad_portee_assign")
            event_par_athlete = {}
            if portee_choix == "Une séance précise" and ids_cibles:
                evs_possibles = supabase.table("events").select("id, title, start_time, end_time, athlete_id").in_("athlete_id", ids_cibles).order("start_time").execute().data or []
                grp_poss = groupes_seances(evs_possibles)
                if grp_poss:
                    cles_poss = sorted(grp_poss.keys(), key=lambda k: k[1], reverse=True)
                    cle_choisie = st.selectbox("Sélectionner la séance précise :", cles_poss, format_func=lambda k: f"{fmt_date_fr(k[1], True)} — {k[0]} ({len(grp_poss[k])} joueur(s))", key="sel_ev_precise_assign")
                    event_par_athlete = {e["athlete_id"]: e["id"] for e in grp_poss[cle_choisie]}
                else:
                    st.warning("Aucune séance planifiée pour ces joueurs.")

            if st.button("💾 Enregistrer et attribuer l'assignation", type="primary", key="btn_do_assign_q_final"):
                if not ids_cibles:
                    st.error("Sélectionnez au moins un athlète ou une équipe.")
                elif portee_choix == "Une séance précise" and not event_par_athlete:
                    st.error("Choisissez une séance précise.")
                else:
                    definir_type_questionnaire(q_obj_sel["id"], "pre_event" if est_pre else "post_event")
                    if est_pre:
                        definir_minutes_avant(q_obj_sel["id"], int(minutes_val))
                    else:
                        definir_minutes_apres(q_obj_sel["id"], int(minutes_val))
                    nb_ok, erreurs = 0, []
                    for aid in ids_cibles:
                        if portee_choix == "Une séance précise":
                            if aid not in event_par_athlete:
                                continue
                            ok_a, err_a = assigner_questionnaire(q_obj_sel["id"], aid, event_par_athlete[aid])
                        else:
                            ok_a, err_a = assigner_questionnaire(q_obj_sel["id"], aid, None)
                        if ok_a:
                            nb_ok += 1
                        else:
                            erreurs.append(f"{dict_a_inv.get(aid, aid)} : {err_a}")
                    if erreurs:
                        st.error("Certaines assignations ont échoué :")
                        for e in erreurs:
                            st.code(e)
                    if nb_ok:
                        flash_succes(f"Questionnaire « {sel_q_title} » assigné à {libelle_cible} ({nb_ok} assignation(s) enregistrée(s)).")
                        if not erreurs:
                            st.rerun()

    with tab_assignes:
        st.subheader("📋 Questionnaires assignés")
        q_tous = supabase.table("questionnaires").select("*").execute().data or []
        assignations = obtenir_assignations()
        profs = supabase.table("profiles").select("id, full_name").execute().data or []
        noms_assign = {p["id"]: p.get("full_name", "?") for p in profs}
        ev_ids_ass = list({a.get("event_id") for a in assignations if a.get("event_id")})
        evs_ass = {}
        for i in range(0, len(ev_ids_ass), 80):
            for e in supabase.table("events").select("id, title, start_time").in_("id", ev_ids_ass[i:i + 80]).execute().data or []:
                evs_ass[e["id"]] = e

        def _timing(q):
            if q.get("title") == TITRE_PRESENCE_AUTO:
                return "Dès la création de la séance", "Au début de la séance"
            if q.get("title") == TITRE_RPE_AUTO:
                return "À la fin de la séance", "Reste à remplir jusqu'à la réponse"
            if q.get("type") == "pre_event":
                return f"{int(q.get('trigger_minutes') or 60)} min avant la séance", "Au début de la séance"
            return "À la fin de la séance", f"{int(q.get('post_window_minutes') or 180)} min après la fin de la séance"

        lignes_ass = []
        for q in q_tous:
            ouv, ferm = _timing(q)
            type_txt = "🌅 Avant" if q.get("type") == "pre_event" else "🌙 Après"
            if est_questionnaire_auto(q):
                lignes_ass.append({"Questionnaire": f"{q['title']}", "Type": type_txt, "Assigné à": "Tous les athlètes (automatique)", "Séance": "Toutes les séances", "Ouverture": ouv, "Fermeture": ferm})
                continue
            aq = [a for a in assignations if a.get("questionnaire_id") == q["id"]]
            if not aq:
                lignes_ass.append({"Questionnaire": q["title"], "Type": type_txt, "Assigné à": "Tous les athlètes (aucune assignation précise)", "Séance": "Toutes les séances", "Ouverture": ouv, "Fermeture": ferm})
            for a in aq:
                ev = evs_ass.get(a.get("event_id"))
                lignes_ass.append({"Questionnaire": q["title"], "Type": type_txt, "Assigné à": noms_assign.get(a.get("athlete_id"), "?"),
                                   "Séance": f"{ev.get('title')} — {fmt_date_fr(ev.get('start_time'), True)}" if ev else "Toutes les séances",
                                   "Ouverture": ouv, "Fermeture": ferm})
        if lignes_ass:
            st.dataframe(pd.DataFrame(lignes_ass), use_container_width=True, hide_index=True)
        else:
            st.info("Aucun questionnaire.")

        st.markdown("---")
        st.markdown("#### ✏️ Modifier les délais ou retirer des assignations")
        q_modifs = [q for q in q_tous if not est_questionnaire_auto(q)]
        if not q_modifs:
            st.caption("Aucun questionnaire personnalisé à modifier.")
        else:
            dict_qm = {q["title"]: q for q in q_modifs}
            sel_qm = st.selectbox("Questionnaire :", list(dict_qm.keys()), key="sel_q_assignes_modif")
            qm = dict_qm[sel_qm]
            if qm.get("type") == "pre_event":
                nv_minutes = st.number_input("⏰ S'ouvre combien de minutes AVANT la séance ?", 5, 1440, int(qm.get("trigger_minutes") or 60), 5, key=f"mod_min_{qm['id']}")
            else:
                nv_minutes = st.number_input("⏰ Reste ouvert combien de minutes APRÈS la fin de la séance ?", 5, 1440, int(qm.get("post_window_minutes") or 180), 5, key=f"mod_min_{qm['id']}")
            aq_m = [a for a in assignations if a.get("questionnaire_id") == qm["id"]]
            retirer_idx = []
            if aq_m:
                df_aq = pd.DataFrame([{
                    "Retirer": False, "Athlète": noms_assign.get(a.get("athlete_id"), "?"),
                    "Séance": (f"{evs_ass[a['event_id']].get('title')} — {fmt_date_fr(evs_ass[a['event_id']].get('start_time'), True)}" if a.get("event_id") in evs_ass else "Toutes les séances"),
                } for a in aq_m])
                edit_aq = st.data_editor(df_aq, hide_index=True, use_container_width=True, disabled=["Athlète", "Séance"], key=f"aq_editor_{qm['id']}",
                                         column_config={"Retirer": st.column_config.CheckboxColumn("Retirer l'assignation")})
                retirer_idx = [i for i, v in enumerate(edit_aq["Retirer"].tolist()) if v]
            else:
                st.caption("Aucune assignation précise : ce questionnaire est ouvert à tous les athlètes. Utilisez l'onglet « Assigner » pour le réserver à des joueurs ou à une équipe.")
            if st.button("💾 Appliquer les modifications", type="primary", key=f"btn_apply_assign_{qm['id']}"):
                if qm.get("type") == "pre_event":
                    definir_minutes_avant(qm["id"], int(nv_minutes))
                else:
                    definir_minutes_apres(qm["id"], int(nv_minutes))
                nb_retires = 0
                for i in retirer_idx:
                    ok_s, _ = supprimer_assignation(aq_m[i])
                    nb_retires += 1 if ok_s else 0
                flash_succes(f"Délai de « {sel_qm} » mis à jour ({int(nv_minutes)} min)" + (f" et {nb_retires} assignation(s) retirée(s)." if retirer_idx else "."))
                st.rerun()

    with tab_repondre:
        athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
        dict_athletes = {a.get("full_name"): a["id"] for a in athletes if a.get("full_name")}
        if dict_athletes:
            sel_athlete_name = st.selectbox("Athlète :", list(dict_athletes.keys()), key="sel_ath_saisie_man")
            selected_athlete_id = dict_athletes[sel_athlete_name]
            events_ath = supabase.table("events").select("id, title, start_time").eq("athlete_id", selected_athlete_id).execute().data or []
            dict_events_rep = {f"{ev.get('title')} — {fmt_date_fr(ev.get('start_time'), True)}": ev["id"] for ev in events_ath}
            q_list = supabase.table("questionnaires").select("*").execute().data or []
            if dict_events_rep and q_list:
                sel_event_label = st.selectbox("Séance :", list(dict_events_rep.keys()), key="sel_evt_saisie_man")
                selected_event_id = dict_events_rep[sel_event_label]
                sel_q_title = st.selectbox("Questionnaire :", [q["title"] for q in q_list], key="sel_q_saisie_man")
                q_obj = next(q for q in q_list if q["title"] == sel_q_title)
                rep = obtenir_reponse_evenement(selected_athlete_id, selected_event_id)
                rendre_formulaire_questionnaire(q_obj, selected_event_id, f"manuel_{selected_athlete_id}", (rep.get("answers") or {}) if rep else {}, athlete_id=selected_athlete_id)

# =====================================================================
# PAGE (ATHLÈTE) : SÉANCES À VENIR
# =====================================================================
elif menu == "📅 Séances à venir":
    st.header("📅 Mes séances")
    afficher_flash()
    maintenant = maintenant_local()
    st.caption(
        "🩹 La présence / blessure se remplit dès que la séance est planifiée, jusqu'à son début. "
        "🌅 Le wellness s'ouvre avant la séance (délai fixé par ton coach). "
        "🌙 Le RPE s'ouvre à la fin de la séance : remplis-le dans l'heure qui suit. Une séance reste ici tant que son RPE n'est pas rempli."
    )

    events_mine_raw = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
    q_all = supabase.table("questionnaires").select("*").execute().data or []
    q_pre = [q for q in q_all if q.get("type") == "pre_event" and not est_questionnaire_auto(q)]
    q_auto = obtenir_ou_creer_rpe_auto()
    q_pres = obtenir_ou_creer_presence_auto()
    q_post_perso = [q for q in q_all if q.get("type") != "pre_event" and not est_questionnaire_auto(q)]
    assignations = obtenir_assignations()

    # Documents (PDF) disponibles par séance
    ids_evs = [e["id"] for e in events_mine_raw]
    ev_avec_pdf = set()
    for i in range(0, len(ids_evs), 80):
        try:
            ev_avec_pdf |= {f.get("event_id") for f in (supabase.table("session_files").select("event_id").in_("event_id", ids_evs[i:i + 80]).execute().data or [])}
        except Exception:
            pass

    # Réponses déjà données, regroupées par séance (tous questionnaires fusionnés)
    reponses_par_event = {}
    for r in obtenir_reponses_athlete(mon_id):
        ans = r.get("answers") or {}
        if isinstance(ans, str):
            try:
                ans = json.loads(ans)
            except Exception:
                ans = {}
        if isinstance(ans, dict):
            reponses_par_event.setdefault(r.get("event_id"), {}).update(ans)

    def rpe_deja_rempli(ev_id):
        return any("rpe" in str(k).lower() and v not in (None, "") for k, v in reponses_par_event.get(ev_id, {}).items())

    rpe_en_attente, a_venir = [], []
    for ev in events_mine_raw:
        d0 = _parser_datetime_event(ev)
        if not d0:
            continue
        d1 = _parser_datetime_event(ev, "end_time") or d0
        if d1 < d0:
            d1 = d0
        rpe_requis = bool(q_auto) and not ev.get("rpe_desactive")
        if maintenant >= d1:
            if rpe_requis and not rpe_deja_rempli(ev["id"]) and d1 >= maintenant - timedelta(days=7):
                rpe_en_attente.append((ev, d0, d1, rpe_requis))
        else:
            a_venir.append((ev, d0, d1, rpe_requis))
    rpe_en_attente.sort(key=lambda t: t[1])
    a_venir.sort(key=lambda t: t[1])

    def bloc_seance(ev, d0, d1, rpe_requis, ouvert):
        emoji = "⚔️" if ev.get("event_type") == "match" else "🏋️"
        titre = f"{emoji} {ev.get('title', 'Séance')} — {fmt_date_fr(ev.get('start_time'), True)}"
        if ev["id"] in ev_avec_pdf:
            titre += "  📎 PDF"
        if d0.date() == maintenant.date():
            titre += "  🔴 Aujourd'hui"
        with st.expander(titre, expanded=ouvert):
            if ev.get("location"):
                st.caption(f"📍 {ev['location']}")
            afficher_fichiers_evenement(ev["id"], key_prefix=f"av_{ev['id']}")
            reponses_deja = reponses_par_event.get(ev["id"], {})

            # ---- Présence / blessure / douleur : de la création jusqu'au début de la séance ----
            if q_pres:
                st.markdown("##### 🩹 Présence & blessures")
                deja_pres = LABEL_PRESENCE in reponses_deja
                if maintenant >= d0:
                    st.caption("✅ Réponse enregistrée." if deja_pres else "⏱️ La séance a commencé : la présence ne peut plus être renseignée.")
                else:
                    if deja_pres:
                        statut_p, raison_p = statut_presence(reponses_deja)
                        st.caption({"disponible": "✅ Tu as répondu : présent(e) et disponible.", "absent": "❌ Tu as répondu : absent(e).",
                                    "indispo": f"🩹 Tu as répondu : indisponible ({raison_p}).", "sans_reponse": ""}[statut_p])
                    cle_p = f"pres_{ev['id']}_{q_pres['id']}"
                    if bouton_ouvrir("✏️ Modifier ma réponse présence / blessure" if deja_pres else "🩹 Répondre : présence, blessure, douleur", cle_p):
                        rendre_formulaire_questionnaire(q_pres, ev["id"], cle_p, reponses_deja)

            # ---- Wellness : uniquement dans la fenêtre [début - délai ; début[ ----
            q_pre_dispo = [q for q in q_pre if questionnaire_disponible_pour(q["id"], mon_id, ev["id"], assignations)]
            if q_pre_dispo:
                st.markdown("##### 🌅 Avant la séance — Wellness")
            for q in q_pre_dispo:
                minutes_avant = int(q.get("trigger_minutes") or 60)
                ouverture = d0 - timedelta(minutes=minutes_avant)
                deja_repondu = any(qq.get("label") in reponses_deja for qq in (q.get("questions") or []))
                if maintenant < ouverture:
                    st.info(f"« {q.get('title')} » s'ouvrira le {fmt_date_fr(ouverture)} à {ouverture.strftime('%H:%M')} ({minutes_avant} min avant la séance).")
                elif maintenant >= d0:
                    st.caption(f"✅ « {q.get('title')} » : déjà rempli." if deja_repondu else f"⏱️ « {q.get('title')} » : fenêtre terminée (la séance a commencé).")
                else:
                    st.success(f"🟢 « {q.get('title')} » est ouvert jusqu'à {d0.strftime('%H:%M')}.")
                    cle_w = f"pre_{ev['id']}_{q['id']}"
                    if bouton_ouvrir(f"✏️ Modifier : {q.get('title')}" if deja_repondu else f"🌅 Répondre au questionnaire : {q.get('title')}", cle_w):
                        rendre_formulaire_questionnaire(q, ev["id"], cle_w, reponses_deja)

            # ---- RPE : à partir de la fin de la séance ----
            st.markdown("##### 🌙 Après la séance — RPE")
            if maintenant < d1:
                if rpe_requis:
                    st.info(f"Le RPE s'ouvrira à la fin de la séance ({d1.strftime('%H:%M')}). Tu devras le remplir dans l'heure qui suit.")
                else:
                    st.caption("Pas de RPE demandé pour cette séance.")
            else:
                if q_auto and rpe_requis:
                    limite = d1 + timedelta(hours=1)
                    if maintenant <= limite:
                        st.warning(f"⏳ RPE à remplir avant {limite.strftime('%H:%M')}.")
                    else:
                        st.error("⏰ RPE en retard : remplis-le maintenant, ton coach attend cette information.")
                    cle_r = f"rpe_{ev['id']}_{q_auto['id']}"
                    if bouton_ouvrir("🌙 Répondre au RPE", cle_r):
                        rendre_formulaire_questionnaire(q_auto, ev["id"], cle_r, reponses_deja)
                for q in q_post_perso:
                    if not questionnaire_disponible_pour(q["id"], mon_id, ev["id"], assignations):
                        continue
                    fenetre = int(q.get("post_window_minutes") or 180)
                    if maintenant > d1 + timedelta(minutes=fenetre):
                        continue
                    cle_o = f"post_{ev['id']}_{q['id']}"
                    if bouton_ouvrir(f"🌙 Répondre : {q.get('title')}", cle_o):
                        rendre_formulaire_questionnaire(q, ev["id"], cle_o, reponses_deja)

    if not rpe_en_attente and not a_venir:
        st.info("Aucune séance à venir et aucun RPE en attente. 👌")
    if rpe_en_attente:
        st.markdown("### 🔴 RPE à remplir")
        for ev, d0, d1, rr in rpe_en_attente:
            bloc_seance(ev, d0, d1, rr, True)
    if a_venir:
        st.markdown("### 📅 À venir")
        for i, (ev, d0, d1, rr) in enumerate(a_venir):
            bloc_seance(ev, d0, d1, rr, i == 0 and not rpe_en_attente)

# =====================================================================
# PAGE (ATHLÈTE) : CALENDRIER (vue mensuelle + vue annuelle)
# =====================================================================
elif menu == "📆 Calendrier":
    import calendar as _calendar
    import html as _html

    st.header("📆 Calendrier")
    afficher_flash()
    aujourdhui = maintenant_local().date()
    events_mine_raw = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []

    ids_evs = [e["id"] for e in events_mine_raw]
    ev_avec_pdf = set()
    for i in range(0, len(ids_evs), 80):
        try:
            ev_avec_pdf |= {f.get("event_id") for f in (supabase.table("session_files").select("event_id").in_("event_id", ids_evs[i:i + 80]).execute().data or [])}
        except Exception:
            pass

    events_par_jour = {}
    for ev in events_mine_raw:
        d = _parser_datetime_event(ev)
        if d:
            events_par_jour.setdefault(d.date(), []).append(ev)
    for lst in events_par_jour.values():
        lst.sort(key=lambda e: e.get("start_time") or "")

    if "ath_cal_ref" not in st.session_state:
        st.session_state.ath_cal_ref = aujourdhui.replace(day=1)
    if "ath_cal_vue" not in st.session_state:
        st.session_state.ath_cal_vue = "🗓️ Mois"
    if "ath_cal_event" not in st.session_state:
        st.session_state.ath_cal_event = None

    def _decaler_mois(delta):
        ref = st.session_state.ath_cal_ref
        m = ref.month - 1 + delta
        st.session_state.ath_cal_ref = ref.replace(year=ref.year + m // 12, month=m % 12 + 1, day=1)

    def _decaler_annee(delta):
        ref = st.session_state.ath_cal_ref
        st.session_state.ath_cal_ref = ref.replace(year=ref.year + delta, day=1)

    def _ouvrir_mois(annee, mois):
        st.session_state.ath_cal_ref = datetime(annee, mois, 1).date()
        st.session_state.ath_cal_vue = "🗓️ Mois"
        st.session_state.ath_cal_event = None

    st.radio("Vue :", ["🗓️ Mois", "📆 Année"], horizontal=True, key="ath_cal_vue")
    ref = st.session_state.ath_cal_ref

    if st.session_state.ath_cal_vue == "📆 Année":
        c1, c2, c3 = st.columns([1, 3, 1])
        c1.button("◀ Année précédente", use_container_width=True, key="ath_an_prev", on_click=_decaler_annee, args=(-1,))
        c2.markdown(f"<h3 style='text-align:center;'>📆 {ref.year}</h3>", unsafe_allow_html=True)
        c3.button("Année suivante ▶", use_container_width=True, key="ath_an_next", on_click=_decaler_annee, args=(1,))

        def html_mini_mois(annee, mois):
            h = ("<div style='background:#131a2b;border:1px solid #263049;border-radius:12px;padding:8px 10px;margin-bottom:6px;'>"
                 f"<div style='font-family:Sora,sans-serif;font-weight:700;margin-bottom:4px;'>{MOIS_FR[mois - 1].capitalize()}</div>"
                 "<table style='width:100%;border-collapse:separate;border-spacing:2px;text-align:center;font-size:0.8em;'><tr>")
            h += "".join(f"<th style='color:#93a0bd;font-weight:600;'>{j[0]}</th>" for j in JOURS_FR) + "</tr>"
            for semaine in _calendar.monthcalendar(annee, mois):
                h += "<tr>"
                for j in semaine:
                    if j == 0:
                        h += "<td></td>"
                        continue
                    d = datetime(annee, mois, j).date()
                    evs = events_par_jour.get(d, [])
                    style, titre, pastille = "padding:3px 0;border-radius:6px;color:#f1f5f9;", "", ""
                    if evs:
                        est_match = any(e.get("event_type") == "match" for e in evs)
                        style += f"background:{'#ef4444' if est_match else '#ff5a1f'};color:#0a0e1a;font-weight:700;"
                        titre = " title='" + _html.escape(" | ".join(str(e.get("title", "Séance")) for e in evs), quote=True) + "'"
                        if any(e["id"] in ev_avec_pdf for e in evs):
                            pastille = "<sup>📎</sup>"
                    if d == aujourdhui:
                        style += "outline:2px solid #22d3ee;"
                    h += f"<td{titre} style='{style}'>{j}{pastille}</td>"
                h += "</tr>"
            return h + "</table></div>"

        st.caption("🟧 entraînement · 🟥 match · 📎 document PDF · contour bleu = aujourd'hui. Clique sur « Ouvrir » pour voir le détail d'un mois.")
        for ligne in range(4):
            for k, col in enumerate(st.columns(3)):
                mois = ligne * 3 + k + 1
                with col:
                    st.markdown(html_mini_mois(ref.year, mois), unsafe_allow_html=True)
                    nb = sum(len(v) for d, v in events_par_jour.items() if d.year == ref.year and d.month == mois)
                    st.button(f"Ouvrir {MOIS_FR[mois - 1]} ({nb} séance{'s' if nb > 1 else ''})", key=f"ath_open_{ref.year}_{mois}",
                              use_container_width=True, on_click=_ouvrir_mois, args=(ref.year, mois))
    else:
        c1, c2, c3 = st.columns([1, 3, 1])
        c1.button("◀ Mois précédent", use_container_width=True, key="ath_cal_prev", on_click=_decaler_mois, args=(-1,))
        c2.markdown(f"<h4 style='text-align:center;'>📅 {MOIS_FR[ref.month - 1].capitalize()} {ref.year}</h4>", unsafe_allow_html=True)
        c3.button("Mois suivant ▶", use_container_width=True, key="ath_cal_next", on_click=_decaler_mois, args=(1,))

        for c, jl in zip(st.columns(7), JOURS_FR):
            c.markdown(f"<div style='text-align:center; color:#94a3b8; font-weight:600;'>{jl}</div>", unsafe_allow_html=True)

        for semaine in _calendar.monthcalendar(ref.year, ref.month):
            for c, jour_num in zip(st.columns(7), semaine):
                if jour_num == 0:
                    c.markdown("&nbsp;", unsafe_allow_html=True)
                    continue
                date_cell = datetime(ref.year, ref.month, jour_num).date()
                style_jour = "color:#38bdf8; font-weight:800;" if date_cell == aujourdhui else "color:#f1f5f9; font-weight:600;"
                c.markdown(f"<div style='{style_jour}'>{jour_num}</div>", unsafe_allow_html=True)
                evs_jour = events_par_jour.get(date_cell, [])
                for ev in evs_jour[:4]:
                    emoji_type = "⚔️" if ev.get("event_type") == "match" else "🏋️"
                    pdf = " 📎" if ev["id"] in ev_avec_pdf else ""
                    if c.button(f"{emoji_type} {ev.get('title', 'Séance')[:8]}{pdf}", key=f"ath_cal_btn_{ev['id']}", help=str(ev.get("title")), use_container_width=True):
                        st.session_state.ath_cal_event = ev["id"]
                        st.rerun()
                if len(evs_jour) > 4:
                    c.caption(f"+{len(evs_jour) - 4} autre(s)")

        st.markdown("---")
        ev_sel = next((e for e in events_mine_raw if e["id"] == st.session_state.ath_cal_event), None)
        if not ev_sel:
            st.info("👆 Clique sur une séance pour voir son détail (documents PDF, tes réponses, ton rapport GPS).")
        else:
            d0 = _parser_datetime_event(ev_sel)
            d1 = _parser_datetime_event(ev_sel, "end_time")
            horaire = (d0.strftime("%d/%m/%Y à %H:%M") + (f" → {d1.strftime('%H:%M')}" if d1 else "")) if d0 else ""
            st.subheader(f"{ev_sel.get('title', 'Séance')} — {horaire}")
            if ev_sel.get("location"):
                st.caption(f"📍 {ev_sel['location']}")
            if ev_sel.get("target_rpe") is not None:
                st.caption(f"🎯 RPE cible de la séance : {float(ev_sel['target_rpe']):g}")
            afficher_fichiers_evenement(ev_sel["id"], key_prefix=f"cal_{ev_sel['id']}")

            rep = obtenir_reponse_evenement(mon_id, ev_sel["id"])
            reponses_deja = (rep.get("answers") or {}) if rep else {}
            st.markdown("##### 📝 Mes réponses pour cette séance")
            if reponses_deja:
                cols_rep = st.columns(min(len(reponses_deja), 4) or 1)
                for idx, (question, valeur) in enumerate(reponses_deja.items()):
                    with cols_rep[idx % 4]:
                        st.metric(label=str(question), value=str(valeur))
            else:
                st.caption("Aucune réponse donnée pour cette séance.")

            gps_ev = obtenir_rapports_gps(athlete_id=mon_id, event_id=ev_sel["id"])
            if gps_ev:
                st.markdown("---")
                st.markdown("##### 🛰️ Mon rapport GPS pour cette séance")
                g = gps_ev[0]
                metriques = [m for m in COLONNES_GPS_NUMERIQUES if g.get(m) is not None]
                for debut_m in range(0, len(metriques), 3):
                    for col_g, m in zip(st.columns(3), metriques[debut_m:debut_m + 3]):
                        v = g.get(m)
                        texte = f"{float(v) / 60:.0f} min" if m == "duree_secondes" else f"{v:g}"
                        col_g.metric(LIBELLES_GPS[m], texte)

            if st.button("✖ Fermer le détail", key="ath_cal_close"):
                st.session_state.ath_cal_event = None
                st.rerun()

# =====================================================================
# PAGE (ATHLÈTE) : MES DONNÉES (même analytique que le coach, pour un seul joueur)
# =====================================================================
elif menu == "📊 Mes données":
    st.header("📊 Mes données")
    afficher_flash()
    nom_moi = profil_connecte.get("full_name") or "Moi"
    mes_events = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
    events_by_id_me = {e["id"]: e for e in mes_events}
    noms_me = {mon_id: nom_moi}
    df_resp_me = construire_df_reponses(obtenir_reponses_athlete(mon_id), events_by_id_me, noms_me)
    df_gps_me = construire_df_gps(obtenir_rapports_gps(athlete_id=mon_id), events_by_id_me, noms_me)
    render_analytique(df_resp_me, df_gps_me, events_by_id_me, noms_me, "joueur", nom_moi, "md")

# =====================================================================
# PAGE : ANALYTIQUE
# =====================================================================
elif menu == "📊 Analytique":
    st.header("📊 Analytique")
    afficher_flash()

    profiles = supabase.table("profiles").select("*").execute().data or []
    dict_profiles = {p["id"]: p.get("full_name", "") for p in profiles}
    dict_athletes = {p.get("full_name"): p["id"] for p in profiles if p.get("role") == "athlete" and p.get("full_name")}
    teams_all = supabase.table("teams").select("*").execute().data or []
    dict_teams_an = {t["name"]: t["id"] for t in teams_all}

    mode_analyse = st.radio("Analyser :", ["👤 Un joueur", "👥 Une équipe", "🆚 Plusieurs joueurs"], horizontal=True, key="rad_mode_analytique")
    scope_ids, mode_key, nom_scope = [], "joueur", ""

    if mode_analyse == "👤 Un joueur":
        j = st.selectbox("Joueur :", sorted(dict_athletes.keys()), key="sel_j_analytique")
        if j:
            scope_ids, mode_key, nom_scope = [dict_athletes[j]], "joueur", j
    elif mode_analyse == "👥 Une équipe":
        eq = st.selectbox("Équipe :", sorted(dict_teams_an.keys()), key="sel_eq_analytique")
        if eq:
            tid = dict_teams_an[eq]
            scope_ids = [p["id"] for p in profiles if p.get("team_id") == tid and p.get("role") == "athlete"]
            mode_key, nom_scope = "equipe", eq
    else:
        noms_sel = st.multiselect("Joueurs :", sorted(dict_athletes.keys()), key="multisel_cmp_analytique")
        scope_ids, mode_key, nom_scope = [dict_athletes[n] for n in noms_sel], "multi", "Joueurs sélectionnés"

    if not scope_ids:
        st.info("Sélectionnez un joueur, une équipe ou plusieurs joueurs.")
        st.stop()

    scope_set = set(scope_ids)
    noms_scope = {i: dict_profiles.get(i, "") for i in scope_ids}
    events_scope = [e for e in mes_evenements(supabase.table("events").select("*").execute().data or []) if e.get("athlete_id") in scope_set]
    events_by_id_an = {e["id"]: e for e in events_scope}

    reponses_scope = []
    for i in range(0, len(scope_ids), 50):
        reponses_scope += supabase.table("questionnaire_responses").select("*").in_("athlete_id", scope_ids[i:i + 50]).execute().data or []
    gps_scope = [g for g in obtenir_rapports_gps() if g.get("athlete_id") in scope_set]

    df_resp_an = construire_df_reponses(reponses_scope, events_by_id_an, noms_scope)
    df_gps_an = construire_df_gps(gps_scope, events_by_id_an, noms_scope)
    render_analytique(df_resp_an, df_gps_an, events_by_id_an, noms_scope, mode_key, nom_scope, "an")

# =====================================================================
# PAGE : GESTION DES PROFILS
# =====================================================================
elif menu == "⚙️ Gestion des profils":
    st.header("⚙️ Gestion des profils")
    afficher_flash()
    tab_ath, tab_teams, tab_comptes = st.tabs(["👤 Athlètes & Tests", "🛡️ Équipes", "🔑 Comptes"])

    with tab_ath:
        teams_data = supabase.table("teams").select("*").execute().data or []
        dict_teams_add = {t["name"]: t["id"] for t in teams_data}
        st.subheader("✏️ Modifier un athlète et ajouter des tests physiques")
        ath_data = supabase.table("profiles").select("*").eq("role", "athlete").execute().data or []
        dict_ath_lookup = {a.get("full_name", f"Athlète {a['id']}"): a for a in ath_data}

        if dict_ath_lookup:
            selected_ath_name = st.selectbox("Sélectionner un athlète :", list(dict_ath_lookup.keys()), key="sel_ath_mgt_prof")
            selected_ath = dict_ath_lookup[selected_ath_name]
            ath_id = selected_ath["id"]

            c_mod1, c_mod2 = st.columns(2)
            with c_mod1:
                upd_name = st.text_input("Nom & Prénom", value=selected_ath.get("full_name", ""), key=f"ath_name_{ath_id}")
            with c_mod2:
                current_team_id = selected_ath.get("team_id")
                current_team_name = next((tname for tname, tid in dict_teams_add.items() if tid == current_team_id), "Aucune")
                team_idx = (["Aucune"] + list(dict_teams_add.keys())).index(current_team_name) if current_team_name in dict_teams_add else 0
                upd_team = st.selectbox("Changer d'équipe", ["Aucune"] + list(dict_teams_add.keys()), index=team_idx, key=f"ath_team_select_{ath_id}")

            if st.button("💾 Mettre à jour le profil athlète", key=f"upd_p_{ath_id}", type="primary"):
                new_t_id = dict_teams_add[upd_team] if upd_team != "Aucune" else None
                supabase.table("profiles").update({"full_name": upd_name, "team_id": new_t_id}).eq("id", ath_id).execute()
                flash_succes("Profil mis à jour !")
                st.rerun()

            st.markdown("---")
            st.markdown(f"##### 📈 Tests physiques de {selected_ath.get('full_name')}")
            tests_db = supabase.table("physical_tests").select("*").eq("athlete_id", ath_id).execute().data or []
            if tests_db:
                for t in tests_db:
                    st.write(f"• **{t.get('test_name')}** : {t.get('test_value')} {t.get('unit')}")
            else:
                st.caption("Aucun test enregistré.")

            st.markdown("##### ➕ Ajouter un test physique et son résultat")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: t_nom = st.text_input("Nom du test (ex: VMA, 1RM)", key=f"t_nom_{ath_id}")
            with col_t2: t_val = st.number_input("Résultat / Valeur", value=0.0, key=f"t_val_{ath_id}")
            with col_t3: t_unit = st.text_input("Unité (ex: km/h, kg)", value="km/h", key=f"t_unit_{ath_id}")

            if st.button("🚀 Enregistrer le test", key=f"btn_save_t_{ath_id}"):
                if t_nom:
                    supabase.table("physical_tests").insert({"athlete_id": ath_id, "test_name": t_nom, "test_value": t_val, "unit": t_unit}).execute()
                    flash_succes("Test ajouté !")
                    st.rerun()
        else:
            st.info("Aucun athlète enregistré.")

    with tab_teams:
        st.subheader("🛡️ Gérer, modifier les équipes et ses joueurs")
        teams_list = supabase.table("teams").select("*").execute().data or []
        
        st.markdown("##### ➕ Créer une nouvelle équipe")
        new_t = st.text_input("Nom de la nouvelle équipe", key="input_create_team_mgt")
        if st.button("Créer l'équipe", type="primary"):
            if new_t:
                creer_equipe(new_t)
                flash_succes("Équipe créée !")
                st.rerun()

        if teams_list:
            st.markdown("---")
            dict_teams_mgt = {t["name"]: t for t in teams_list}
            sel_t_mgt = st.selectbox("Sélectionner l'équipe à gérer :", list(dict_teams_mgt.keys()), key="sel_team_mgt_box")
            t_obj = dict_teams_mgt[sel_t_mgt]
            t_id = t_obj["id"]

            renamed_t = st.text_input("Modifier le nom de l'équipe :", value=t_obj["name"], key=f"rename_team_inp_{t_id}")
            c_eq1, c_eq2 = st.columns(2)
            with c_eq1:
                if st.button("💾 Enregistrer le nouveau nom", key=f"btn_save_rename_eq_{t_id}"):
                    supabase.table("teams").update({"name": renamed_t}).eq("id", t_id).execute()
                    flash_succes("Équipe renommée !")
                    st.rerun()
            with c_eq2:
                if st.button("❌ Supprimer cette équipe", type="primary", key=f"del_eq_{t_id}"):
                    supprimer_equipe(t_id)
                    flash_succes("Équipe supprimée.")
                    st.rerun()

            st.markdown("##### 👥 Liste des joueurs dans cette équipe (possibilité de retirer)")
            membres_equipe = supabase.table("profiles").select("id, full_name").eq("team_id", t_id).execute().data or []
            if membres_equipe:
                for mem in membres_equipe:
                    col_m1, col_m2 = st.columns([3, 1])
                    with col_m1:
                        st.write(f"• **{mem.get('full_name')}**")
                    with col_m2:
                        if st.button("Retirer de l'équipe", key=f"rem_mem_{mem['id']}"):
                            supabase.table("profiles").update({"team_id": None}).eq("id", mem["id"]).execute()
                            flash_succes(f"{mem.get('full_name')} a été retiré de l'équipe.")
                            st.rerun()
            else:
                st.caption("Aucun joueur dans cette équipe pour le moment.")

    with tab_comptes:
        st.subheader("🔑 Créer un compte athlète")
        st.caption("Seuls les comptes athlètes se créent ici. Les comptes coach se créent directement dans Supabase.")
        with st.form("form_creer_compte_mgt"):
            c1, c2 = st.columns(2)
            with c1:
                new_email = st.text_input("E-mail")
                new_password = st.text_input("Mot de passe", type="password")
                new_role = "athlete"
            with c2:
                new_full_name = st.text_input("Nom complet")
                teams_data = supabase.table("teams").select("*").execute().data or []
                dict_teams_cpt = {t["name"]: t["id"] for t in teams_data}
                new_team = st.selectbox("Équipe", ["Aucune"] + list(dict_teams_cpt.keys()))

            if st.form_submit_button("🚀 Créer le compte", type="primary"):
                if new_email and new_password and new_full_name:
                    t_id = dict_teams_cpt.get(new_team) if new_team != "Aucune" else None
                    ok, msg = creer_compte(new_email, new_password, new_full_name, new_role, t_id)
                    if ok: flash_succes(msg); st.rerun()
                    else: st.error(msg)

# =====================================================================
# PAGE : GÉNÉRATEUR DE BIPS AUDIO
# =====================================================================
elif menu == "🔊 Générateur de Bips Audio":
    import wave
    import math
    import struct
    import io

    st.header("🔊 Générateur de Bips Audio (Tests VMA & Pacing)")

    afficher_flash()
    st.write("Créez sur-mesure des bandes sonores rythmées par des bips haute intensité pour vos tests de terrain.")

    def generate_beep_audio(interval_mode, base_interval, min_interval, total_beps, accel_trigger, accel_value, step_decrement, bip_freq=1800, bip_duration=0.2, wave_type="Carrée (Buzzer Puissant / VMEVAL)"):
        sample_rate = 88200
        audio_frames = bytearray()

        def create_wave(freq, duration_sec, w_type):
            num_samples = int(sample_rate * duration_sec)
            frames = bytearray()
            fade_len = int(sample_rate * 0.002)

            for i in range(num_samples):
                envelope = 1.0
                if i < fade_len: envelope = i / fade_len
                elif i > num_samples - fade_len: envelope = (num_samples - i) / fade_len

                sin_val = math.sin(2 * math.pi * freq * i / sample_rate)
                raw_signal = 1.0 if ("Carrée" in w_type and sin_val >= 0) else (-1.0 if "Carrée" in w_type else sin_val)
                value = int(32767 * 0.98 * envelope * raw_signal)
                frames.extend(struct.pack('<h', value))
            return frames

        def create_silence(duration_sec):
            return bytearray(struct.pack('<h', 0) * int(sample_rate * duration_sec))

        current_interval = float(base_interval)
        elapsed_time = 0.0

        for b in range(1, total_beps + 1):
            is_accel_step = False
            if interval_mode == "Progressif / Accéléré" and b > 1:
                if accel_trigger == "Tous les X bips" and (b - 1) % int(accel_value) == 0: is_accel_step = True
                elif accel_trigger == "Toutes les X secondes" and elapsed_time >= accel_value:
                    is_accel_step = True
                    elapsed_time = 0.0
                if is_accel_step:
                    current_interval = max(float(min_interval), current_interval - float(step_decrement))

            if is_accel_step:
                beep_wave = create_wave(2400, bip_duration * 0.6, wave_type) + create_silence(0.04) + create_wave(2400, bip_duration, wave_type)
                used_bip_dur = (bip_duration * 1.6) + 0.04
            else:
                beep_wave = create_wave(bip_freq, bip_duration, wave_type)
                used_bip_dur = bip_duration

            audio_frames.extend(beep_wave)
            audio_frames.extend(create_silence(max(0.0, current_interval - used_bip_dur)))
            elapsed_time += current_interval

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_frames)
        return wav_buffer.getvalue()

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        st.subheader("⚙️ Rythme & Structure")
        mode = st.radio("Type de test :", ["Constant (Intervalle fixe)", "Progressif / Accéléré"], key="audio_mode_gen")
        base_int = st.number_input("Intervalle de départ entre chaque bip (secondes) :", min_value=0.5, max_value=120.0, value=5.0, step=0.5, key="num_base_int")
        total_beps = st.number_input("Nombre total de bips à générer :", min_value=2, max_value=500, value=30, step=1, key="num_tot_beps")

    with col_cfg2:
        st.subheader("🔊 Timbre & Puissance du Bip")
        wave_type = st.selectbox("Type de son :", ["Carrée (Buzzer Puissant / VMEVAL)", "Sinusoïdale (Bip classique)"], key="sel_wave_type")
        bip_duration = st.slider("Durée du bip sonore (secondes) :", min_value=0.05, max_value=2.0, value=0.25, step=0.05, key="slider_bip_dur")
        bip_freq = st.slider("Hauteur du son / Fréquence (Hz) :", min_value=600, max_value=3500, value=2000, step=100, key="slider_bip_freq")

    st.markdown("---")
    if mode == "Progressif / Accéléré":
        st.subheader("🚀 Paramètres d'accélération")
        ca1, ca2, ca3, ca4 = st.columns(4)
        with ca1: accel_trigger = st.selectbox("Déclencheur :", ["Tous les X bips", "Toutes les X secondes"], key="sel_accel_trig")
        with ca2: accel_val = st.number_input("N :", min_value=1, max_value=600, value=5, key="num_accel_val")
        with ca3: step_decrement = st.number_input("Réduction (sec) :", min_value=0.1, max_value=10.0, value=0.5, step=0.1, key="num_step_dec")
        with ca4: min_int = st.number_input("Minimum (sec) :", min_value=0.2, max_value=30.0, value=1.0, step=0.1, key="num_min_int")
    else:
        accel_trigger, accel_val, step_decrement, min_int = "Tous les X bips", 1, 0.0, base_int

    st.markdown("---")
    if st.button("🎵 Générer la bande sonore", type="primary", use_container_width=True, key="btn_gen_audio_file"):
        with st.spinner("Génération du son en cours..."):
            audio_data = generate_beep_audio(mode, base_int, min_int, total_beps, accel_trigger, accel_val, step_decrement, bip_freq, bip_duration, wave_type)
            st.success("✅ Fichier sonore généré !")
            st.audio(audio_data, format="audio/wav")
            st.download_button("💾 Télécharger (.WAV)", data=audio_data, file_name="test_bips.wav", mime="audio/wav", use_container_width=True, key="dl_wav_audio")
