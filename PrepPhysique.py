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
    FORMAT_DOULEUR, FORMAT_PRESENCE, TITRE_PRESENCE_AUTO, LABEL_PRESENCE, LABEL_BLESSURE_PRES, LABEL_DOULEUR_PRES, LABELS_PRESENCE,
    est_questionnaire_auto, obtenir_ou_creer_presence_auto, statut_presence,
    obtenir_reponses_events, calculer_effectif, supprimer_assignation,
    LIBELLES_GPS, obtenir_donnees_alertes, calculer_alertes,
    construire_df_reponses, construire_df_gps, filtrer_periode, stats_par_question, table_rpe_vs_cible,
    resume_effectif, construire_df_cible, LIBELLE_CIBLE, reponses_texte,
    obtenir_regles_alertes, creer_regle_alerte, maj_regle_alerte, supprimer_regle_alerte, CONDITIONS_ALERTE, decrire_regle,
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

# Gestion de l'état de la barre latérale via la session Streamlit
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

st.set_page_config(
    page_title="Performance+ | Prép. Physique",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
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

    header[data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stDecoration"] { display: none !important; }

    /* ===== Mise en page plus aérée et plus moderne ===== */
    .block-container { padding-top: 2.2rem !important; max-width: 1280px; }
    div[data-testid="stAlert"] { border-radius: 12px !important; border: 1px solid var(--border-soft) !important; }
    div[data-baseweb="tab-list"] { gap: 4px; overflow-x: auto; scrollbar-width: none; border-bottom: 1px solid var(--border-soft); }
    div[data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    div[data-testid="stMetric"] { box-shadow: 0 4px 14px rgba(0,0,0,0.25); }
    .stButton>button, .stDownloadButton>button { min-height: 42px; }
    h2 { font-size: 1.75rem !important; margin-bottom: 0.4rem !important; }
    section[data-testid="stSidebar"] .stButton>button { width: 100%; }

    /* ===== Téléphone ===== */
    @media (max-width: 768px) {
        .block-container { padding: 5.2rem 0.8rem 3rem 0.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.15rem !important; }
        div[data-testid="stMetric"] { padding: 10px 12px; }
        div[data-testid="stMetricValue"] { font-size: 1.35rem !important; }
        button[data-baseweb="tab"] { padding: 8px 10px !important; font-size: 0.82rem !important; }
        .stButton>button, .stDownloadButton>button { min-height: 48px; font-size: 0.95rem; }
        div[data-testid="stExpander"] summary { padding: 0.7rem 0.8rem; }
        section[data-testid="stSidebar"] div[role="radiogroup"] label { padding: 13px 14px; }
    }
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
                try:
                    st.session_state["_auth_tokens"] = (session.access_token, session.refresh_token)
                except Exception:
                    pass
                flash_succes(f"Bienvenue {profile.get('full_name', '')} !")
                st.rerun()

if not st.session_state.user_profile:
    ecran_connexion()
    st.stop()

profil_connecte = st.session_state.user_profile
role_connecte = profil_connecte.get("role", "athlete")
mon_id = profil_connecte.get("id")

# --- BOUTON NATIF POUR OUVRIR / FERMER LE MENU (EN HAUT DE LA SIDEBAR) ---
if st.sidebar.button("📂 Ouvrir / Fermer le Menu", type="primary", use_container_width=True):
    if st.session_state.sidebar_state == "expanded":
        st.session_state.sidebar_state = "collapsed"
    else:
        st.session_state.sidebar_state = "expanded"
    st.rerun()

st.sidebar.markdown("""
<div class="brand-kicker">⚡ PERFORMANCE+</div>
""", unsafe_allow_html=True)
st.sidebar.markdown(f"**👤 {profil_connecte.get('full_name', 'Utilisateur')}**")
st.sidebar.caption(f"Rôle : {'🏋️ Coach' if role_connecte == 'coach' else '🏃 Athlète'}")
if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
    deconnexion()
    st.session_state.user_profile = None
    st.rerun()
st.sidebar.markdown("---")

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
    """Heure actuelle en France (le serveur Streamlit tourne en UTC)."""
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
    """Affiche les documents (PDF / images) attachés à une séance."""
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
# OUTILS COMMUNS
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


SQL_ALERTES = """create table if not exists alert_rules (
  id uuid primary key default gen_random_uuid(),
  coach_id uuid not null,
  name text,
  questionnaire_id uuid,
  question_label text not null,
  condition text not null,
  threshold numeric not null,
  severity text default 'moyenne',
  active boolean default true,
  created_at timestamptz default now()
);
alter table alert_rules enable row level security;
create policy "coach_gere_regles_alertes" on alert_rules for all to authenticated
using (exists (select 1 from profiles p where p.id = auth.uid() and p.role = 'coach'))
with check (exists (select 1 from profiles p where p.id = auth.uid() and p.role = 'coach'));"""

SQL_PROPRIETAIRES = """alter table profiles add column if not exists created_by uuid;
alter table teams add column if not exists created_by uuid;
alter table questionnaires add column if not exists created_by uuid;"""


def flash_succes(message, genre="succes"):
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
    kwargs.setdefault("format", "DD/MM/YYYY")
    return st.date_input(*args, **kwargs)


def hid(texte):
    return hashlib.md5(str(texte).encode("utf-8")).hexdigest()[:10]


def aff_df(df, masquer=("athlete_id", "event_id", "DateObj")):
    return df.drop(columns=[c for c in masquer if c in df.columns])


def nb_coachs():
    if "_nb_coachs" not in st.session_state:
        try:
            st.session_state["_nb_coachs"] = len(supabase.table("profiles").select("id").eq("role", "coach").execute().data or [])
        except Exception:
            st.session_state["_nb_coachs"] = 1
    return st.session_state["_nb_coachs"]


def cloisonnement_actif():
    if "_colonne_created_by" not in st.session_state:
        try:
            lignes = supabase.table("profiles").select("*").limit(1).execute().data or []
            st.session_state["_colonne_created_by"] = bool(lignes) and "created_by" in lignes[0]
        except Exception:
            st.session_state["_colonne_created_by"] = False
    return st.session_state["_colonne_created_by"]


def est_a_moi(ligne):
    if not cloisonnement_actif():
        return True
    proprietaire = ligne.get("created_by")
    if proprietaire in (None, ""):
        return nb_coachs() <= 1
    return proprietaire == mon_id


def mes_athletes():
    return [p for p in (supabase.table("profiles").select("*").eq("role", "athlete").execute().data or []) if est_a_moi(p)]


def mes_equipes():
    return [t for t in (supabase.table("teams").select("*").execute().data or []) if est_a_moi(t)]


def ids_mes_athletes():
    return {p["id"] for p in mes_athletes()}


def mes_evenements(events):
    ids = ids_mes_athletes()
    return [e for e in events if e.get("athlete_id") in ids]


def mes_questionnaires(liste):
    return [q for q in liste if est_questionnaire_auto(q) or est_a_moi(q)]


def athletes_sans_proprietaire():
    if not cloisonnement_actif():
        return []
    return [p for p in (supabase.table("profiles").select("*").eq("role", "athlete").execute().data or []) if p.get("created_by") in (None, "")]


ICONES_ALERTES = {"douleur": "🩹", "blessure": "🚑", "rpe_joueur": "🔥", "rpe_equipe": "👥",
                  "wellness_stat": "📉", "gps_stat": "🛰️", "perso": "⚙️"}
NOMS_ALERTES = {"douleur": "Douleur musculaire", "blessure": "Blessure", "rpe_joueur": "RPE joueur vs cible",
                "rpe_equipe": "RPE équipe vs cible", "wellness_stat": "Réponse wellness extrême", "gps_stat": "GPS inhabituel",
                "perso": "Mes alertes personnalisées"}


def get_alertes_coach(force=False):
    jours = int(st.session_state.get("_al_jours", 30))
    sj = float(st.session_state.get("_al_seuil_j", 2.0))
    se = float(st.session_state.get("_al_seuil_e", 2.0))
    cle = (jours, sj, se)
    cache = st.session_state.get("_cache_alertes")
    if not force and cache and cache["cle"] == cle and (time.time() - cache["t"]) < 90:
        return cache["data"]
    donnees = obtenir_donnees_alertes(ids_mes_athletes(), mon_id)
    data = calculer_alertes(donnees, jours, sj, se, maintenant=maintenant_local())
    st.session_state["_cache_alertes"] = {"cle": cle, "t": time.time(), "data": data}
    return data


def alertes_non_vues(force=False):
    vues = st.session_state.setdefault("alertes_vues", set())
    return [a for a in get_alertes_coach(force) if a["cle"] not in vues]


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
            debut, fin = fin, debut
    if debut:
        st.caption(f"Période affichée : du {debut.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}")
    return debut, fin


def _libelle_seance(cle, groupes):
    return f"{fmt_date_fr(cle[1], True)} — {cle[0]} ({len(groupes[cle])} joueur{'s' if len(groupes[cle]) > 1 else ''})"


def render_analytique(df_resp_all, df_gps_all, events_by_id, noms_by_id, mode, nom_scope, prefix):
    est_equipe = mode == "equipe"
    scope_ids = set(noms_by_id.keys())
    debut, fin = selecteur_periode(prefix)
    df_resp = filtrer_periode(df_resp_all, debut, fin)
    df_gps = filtrer_periode(df_gps_all, debut, fin)
    cols_gps = [LIBELLES_GPS[m] for m in COLONNES_GPS_NUMERIQUES]

    tab_q, tab_g, tab_s, tab_gps, tab_brut = st.tabs(["Réponses par question", "Graphique", "Séance", "Les données GPS", "Données brutes"])

    with tab_q:
        stats = stats_par_question(df_resp)
        if df_resp.empty:
            st.info("Aucune réponse sur cette période.")
        else:
            titre = {"equipe": f"👥 Moyenne de l'équipe {nom_scope} sur chaque question",
                     "multi": "👥 Moyenne des joueurs sélectionnés sur chaque question"}.get(mode, f"👤 Moyenne de {nom_scope} sur chaque question")
            st.markdown(f"### {titre}")
            if stats.empty:
                st.info("Aucune réponse à afficher sur cette période.")
            else:
                st.caption("Moyenne, min et max de chaque question numérique. Les réponses texte sont détaillées plus bas.")
                st.dataframe(stats, use_container_width=True, hide_index=True)
                st.download_button("📥 Exporter les moyennes et réponses (CSV)", data=stats.to_csv(index=False).encode("utf-8"), file_name="reponses_par_question.csv", mime="text/csv", key=f"{prefix}_dl_moy")
                if mode in ("equipe", "multi"):
                    num = df_resp[df_resp["Valeur_num"].notna() & ~df_resp["Question"].isin(LABELS_PRESENCE)]
                    if not num.empty:
                        piv = num.pivot_table(index="Joueur", columns="Question", values="Valeur_num", aggfunc="mean").round(2)
                        with st.expander("Voir la moyenne de chaque joueur"):
                            st.dataframe(piv, use_container_width=True)
            textes = reponses_texte(df_resp)
            if not textes.empty:
                st.markdown("#### 📝 Détail des réponses texte (douleurs, commentaires...)")
                st.dataframe(aff_df(textes.sort_values("DateObj", ascending=False))[["Date", "Joueur", "Séance", "Question", "Valeur"]], use_container_width=True, hide_index=True)

    with tab_g:
        num = df_resp[df_resp["Valeur_num"].notna() & ~df_resp["Question"].isin(LABELS_PRESENCE)] if not df_resp.empty else df_resp
        df_cible = construire_df_cible(events_by_id, noms_by_id, debut, fin)
        if not df_cible.empty:
            num = pd.concat([num, df_cible], ignore_index=True) if (num is not None and not num.empty) else df_cible
        if num is None or num.empty:
            st.info("Pas de données numériques pour tracer un graphique sur cette période.")
        else:
            questions = sorted(num["Question"].unique().tolist())
            choix = st.multiselect("📊 Données à afficher dans le graphique :", questions, default=questions[:1], key=f"{prefix}_g_questions")
            normaliser = st.checkbox("Mettre toutes les données à la même échelle (0–100 %)", key=f"{prefix}_g_norm") if len(choix) > 1 else False
            if not choix:
                st.info("Choisissez au moins une donnée.")
            else:
                sub = num[num["Question"].isin(choix)]
                if mode == "multi":
                    for q in choix:
                        sq = sub[sub["Question"] == q]
                        if q == LIBELLE_CIBLE:
                            agg = sq.groupby("DateObj", as_index=False)["Valeur_num"].mean()
                            fig = px.line(agg, x="DateObj", y="Valeur_num", markers=True, template="plotly_dark", title=q)
                        else:
                            agg = sq.groupby(["DateObj", "Joueur"], as_index=False)["Valeur_num"].mean()
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
                st.caption("Aucun RPE cible n'a été défini sur ces séances.")
            fig.update_layout(template="plotly_dark", yaxis=dict(range=[0, 10], title="RPE"), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(aff_df(t_rpe), use_container_width=True, hide_index=True)

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

            rep_ev = {}
            if not d_resp.empty:
                for _, r in d_resp.iterrows():
                    rep_ev.setdefault(r["event_id"], {})[r["Question"]] = r["Valeur"]
            eff = calculer_effectif(evs, rep_ev, noms_by_id)
            if mode == "joueur":
                statut = next((k for k in ("disponible", "absent", "indispo", "sans_reponse") if eff[k]), "sans_reponse")
                lib = {"disponible": "✅ Présent(e) en séance", "absent": "❌ Absent(e)", "indispo": "🩹 Présent(e) en réathlétisation", "sans_reponse": "❓ Présence non renseignée"}[statut]
                raison = eff[statut][0]["raison"] if eff[statut] else ""
                st.markdown(f"**Présence :** {lib}" + (f" — {raison}" if raison and raison != "Absent" else ""))
            else:
                rs = resume_effectif(eff)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("✅ Présents en séance", rs["presents"])
                c2.metric("❌ Absents (dont blessés)", f"{rs['absents']} ({rs['absents_blesses']})")
                c3.metric("🩹 Présents en réathlétisation", rs["rehab"])
                c4.metric("❓ Sans réponse", rs["sans_reponse"])
                with st.expander("Voir la liste des joueurs"):
                    for cle_s, titre_s in [("disponible", "✅ Présents en séance"), ("absent", "❌ Absents"), ("indispo", "🩹 Présents en réathlétisation"), ("sans_reponse", "❓ Sans réponse")]:
                        if eff[cle_s]:
                            st.markdown(f"**{titre_s}** : " + ", ".join(x["nom"] + (f" ({x['raison']})" if x["raison"] and x["raison"] != "Absent" else "") for x in eff[cle_s]))

            t_s = table_rpe_vs_cible(d_resp, events_by_id) if not d_resp.empty else pd.DataFrame()
            cible_s = next((e.get("target_rpe") for e in evs if e.get("target_rpe") is not None), None)
            m1, m2, m3 = st.columns(3)
            reel = t_s["RPE réalisé"].iloc[0] if not t_s.empty else None
            m1.metric("RPE réalisé (moyenne)", f"{reel:g}" if reel is not None else "—")
            m2.metric("🎯 RPE cible", f"{float(cible_s):g}" if cible_s is not None else "—")
            m3.metric("Écart", f"{reel - float(cible_s):+.1f}" if (reel is not None and cible_s is not None) else "—")

            st.markdown("##### 🎯 RPE de chaque joueur vs RPE cible")
            lignes_rj = []
            for e in evs:
                if d_resp is not None and not d_resp.empty:
                    dj = d_resp[(d_resp["event_id"] == e["id"]) & d_resp["Question"].str.lower().str.contains("rpe") & d_resp["Valeur_num"].notna()]
                else:
                    dj = pd.DataFrame(columns=["Valeur_num"])
                lignes_rj.append({"Joueur": noms_by_id.get(e.get("athlete_id"), "?"),
                                  "RPE": round(float(dj["Valeur_num"].mean()), 2) if len(dj) else None,
                                  "RPE cible": float(e["target_rpe"]) if e.get("target_rpe") is not None else None})
            df_rj = pd.DataFrame(lignes_rj).sort_values("Joueur")
            if df_rj["RPE"].notna().any():
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_rj["Joueur"], y=df_rj["RPE"], name="RPE du joueur", marker_color="#ff5a1f"))
                if df_rj["RPE cible"].notna().any():
                    fig.add_trace(go.Scatter(x=df_rj["Joueur"], y=df_rj["RPE cible"], name="RPE cible", mode="lines+markers", line=dict(color="#22d3ee", width=3)))
                fig.update_layout(template="plotly_dark", yaxis=dict(range=[0, 10], title="RPE"), legend_title_text="")
                st.plotly_chart(fig, use_container_width=True)
                df_rj["Écart"] = (df_rj["RPE"] - df_rj["RPE cible"]).round(2)
                st.dataframe(df_rj, use_container_width=True, hide_index=True)
            else:
                st.info("Aucun RPE renseigné pour cette séance.")

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

            st.markdown("##### 📋 Données brutes de la séance")
            if d_resp is None or d_resp.empty:
                st.info("Aucune réponse pour cette séance.")
            else:
                st.dataframe(aff_df(d_resp)[["Joueur", "Date", "Question", "Valeur"]], use_container_width=True, hide_index=True)

    with tab_gps:
        st.markdown("### 🛰️ Données & Rapports GPS")
        if df_gps is None or df_gps.empty:
            st.info("Aucun rapport GPS sur cette période.")
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
                st.dataframe(tableau, use_container_width=True, hide_index=True)
                export = tableau
            else:
                d = df_gps.sort_values("DateObj").copy()
                d["Séance (date)"] = d["Séance"] + " — " + d["Date"]
                fig = px.bar(d, x="Séance (date)", y=metrique, color="Joueur", barmode="group", template="plotly_dark", title=metrique)
                st.plotly_chart(fig, use_container_width=True)
                export = aff_df(d.drop(columns=["Séance (date)"])).round(2)
                st.dataframe(export, use_container_width=True, hide_index=True)
            st.download_button("📥 Exporter les données GPS (CSV)", data=export.to_csv(index=False).encode("utf-8"), file_name="donnees_gps.csv", mime="text/csv", key=f"{prefix}_dl_gps")

    with tab_brut:
        st.markdown("### 📋 Données brutes")
        if df_resp is not None and not df_resp.empty:
            brut = aff_df(df_resp.sort_values("DateObj", ascending=False))[["Date", "Joueur", "Séance", "Question", "Valeur"]]
            st.dataframe(brut, use_container_width=True, hide_index=True)
            st.download_button("📥 Exporter les réponses (CSV)", data=brut.to_csv(index=False).encode("utf-8"), file_name="reponses_brutes.csv", mime="text/csv", key=f"{prefix}_dl_brut")


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


if role_connecte == "coach" and not st.session_state.get("_auto_q_ok"):
    obtenir_ou_creer_rpe_auto()
    obtenir_ou_creer_presence_auto()
    st.session_state["_auto_q_ok"] = True

if st.session_state.get("_menu_courant") != menu:
    for _k in [k for k in st.session_state if str(k).startswith(("eff_src_", "eff_ver_", "eff_ids_"))]:
        del st.session_state[_k]
    st.session_state["_menu_courant"] = menu

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

    athletes_list = mes_athletes()
    dict_athletes = {a.get("full_name", f"Athlète {a['id']}"): a["id"] for a in athletes_list if a.get("full_name")}
    noms_by_id = {v: k for k, v in dict_athletes.items()}

    teams_list_all = mes_equipes()
    dict_teams_all = {t["name"]: t["id"] for t in teams_list_all}

    statuts = get_statuts_disponibilite()
    ids_blesses = {aid for aid, s in statuts.items() if s["statut"] == "blesse"}
    st.markdown("---")
    tab_nouvelle, tab_existantes = st.tabs(["🆕 Planifier une nouvelle séance", "📋 Séances planifiées (modifier / supprimer)"])

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
            exclure_blesses = st.checkbox("🚑 Exclure automatiquement les joueurs en réathlétisation", value=True, key="plan_excl")
            location = st.text_input("Lieu", key="plan_lieu")
            definir_rpe = st.checkbox("🎯 Définir un RPE cible pour cette séance", value=True, key="plan_def_rpe")
            rpe_cible = st.number_input("RPE cible (1-10)", min_value=1.0, max_value=10.0, value=7.0, step=0.5, key="plan_rpe_cible") if definir_rpe else None

        with col_b:
            event_date = date_fr("Date de la séance", datetime.now(), key="plan_date")
            start_time = st.time_input("Heure de début", datetime.strptime("10:00", "%H:%M").time(), key="plan_h1")
            end_time = st.time_input("Heure de fin", datetime.strptime("11:30", "%H:%M").time(), key="plan_h2")

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
                        flash_succes(f"Séance « {title} » planifiée : {len(dates_to_schedule)} date(s) × {len(target_ids)} joueur(s).")
                        st.session_state.pop("_cache_alertes", None)
                        st.rerun()

    with tab_existantes:
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
            now_loc = maintenant_local()
            def _fin_seance(k):
                return parse_dt(k[2]) or parse_dt(k[1]) or now_loc
            a_venir_k = sorted([k for k in groupes if _fin_seance(k) >= now_loc], key=lambda k: k[1])

            st.markdown("#### 🔜 Prochaine séance")
            if not a_venir_k:
                st.info("Aucune séance à venir.")
            else:
                k0 = a_venir_k[0]
                grp0 = groupes[k0]
                d_debut, d_fin = parse_dt(k0[1]), parse_dt(k0[2])
                lieu0 = grp0[0].get("location") or "Lieu non précisé"
                horaire0 = d_debut.strftime("%H:%M") + (f" → {d_fin.strftime('%H:%M')}" if d_fin else "") if d_debut else ""
                st.markdown(f"### {'⚔️' if grp0[0].get('event_type') == 'match' else '🏋️'} {k0[0]}")
                st.markdown(f"📅 **{fmt_date_fr(k0[1])}** · 🕒 **{horaire0}** · 📍 **{lieu0}**")
                eff0 = calculer_effectif(grp0, reponses_events, noms_by_id)
                rs0 = resume_effectif(eff0)
                n1, n2, n3, n4 = st.columns(4)
                n1.metric("✅ Présents en séance", rs0["presents"])
                n2.metric("❌ Absents (dont blessés)", f"{rs0['absents']} ({rs0['absents_blesses']})")
                n3.metric("🩹 Présents en réathlétisation", rs0["rehab"])
                n4.metric("❓ Sans réponse", rs0["sans_reponse"])

            st.markdown("---")
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
                        if c.button(f"{emoji_type} {k[0][:9]}{suffixe}", key=f"cal_btn_{hid('||'.join(k))}", use_container_width=True):
                            st.session_state.cal_seance_sel = "||".join(k)
                            st.rerun()

            cle_sel = st.session_state.cal_seance_sel
            grp_sel = groupes_par_cle.get(cle_sel) if cle_sel else None

            if grp_sel:
                ev_sel = grp_sel[0]
                ids_groupe = [e["id"] for e in grp_sel]
                gid = hid(cle_sel)
                st.subheader(f"✏️ {ev_sel.get('title')} — {fmt_date_fr(ev_sel.get('start_time'), True)}")
                if st.button("❌ Supprimer cette séance", type="primary", key=f"del_ev_{gid}"):
                    supabase.table("events").delete().in_("id", ids_groupe).execute()
                    st.session_state.cal_seance_sel = None
                    flash_succes("Séance supprimée.")
                    st.rerun()

# =====================================================================
# PAGE : ALERTES
# =====================================================================
elif menu == "🔔 Alertes":
    st.header("🔔 Alertes")
    afficher_flash()
    toutes = get_alertes_coach()
    if not toutes:
        st.success("Aucune alerte à afficher. 👌")
    else:
        for a in toutes:
            st.warning(f"**{a['athlete']}** — {a['seance']} ({a['date']})\n\n{a['message']}")

# =====================================================================
# PAGE : EFFECTIF
# =====================================================================
elif menu == "👥 Effectif":
    st.header("👥 Effectif")
    afficher_flash()
    teams_eff = mes_equipes()
    if not teams_eff:
        st.info("Aucune équipe. Créez-en une dans « ⚙️ Gestion des profils ».")
    else:
        dict_teams_eff = {t["name"]: t["id"] for t in teams_eff}
        eq_nom = st.selectbox("🛡️ Équipe :", sorted(dict_teams_eff.keys()), key="eff_equipe_sel")
        eq_id = dict_teams_eff[eq_nom]
        joueurs = [p for p in mes_athletes() if p.get("team_id") == eq_id]
        if joueurs:
            df = pd.DataFrame([{"Nom": p.get("full_name"), "Poste": p.get("position", "")} for p in joueurs])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun joueur dans cette équipe.")

# =====================================================================
# PAGE : FICHIERS & RAPPORTS GPS
# =====================================================================
elif menu == "📁 Fichiers & Rapports GPS":
    st.header("📁 Fichiers & Rapports GPS")
    afficher_flash()
    st.info("Utilisez les onglets natifs ou la section dédiée pour importer vos fichiers GPS ou lier des PDF.")

# =====================================================================
# PAGE : QUESTIONNAIRES
# =====================================================================
elif menu == "📝 Questionnaires":
    st.header("📝 Questionnaires")
    afficher_flash()
    st.info("Gérez vos modèles de questionnaires et leur assignation ici.")

# =====================================================================
# PAGE (ATHLÈTE) : SÉANCES À VENIR
# =====================================================================
elif menu == "📅 Séances à venir":
    st.header("📅 Mes séances")
    afficher_flash()
    events_mine = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
    if not events_mine:
        st.info("Aucune séance planifiée pour le moment.")
    else:
        for ev in events_mine:
            st.markdown(f"**{ev.get('title')}** — {fmt_date_fr(ev.get('start_time'), True)}")

# =====================================================================
# PAGE (ATHLÈTE) : CALENDRIER
# =====================================================================
elif menu == "📆 Calendrier":
    st.header("📆 Calendrier")
    afficher_flash()
    st.info("Retrouvez ici le calendrier de vos séances.")

# =====================================================================
# PAGE (ATHLÈTE) : MES DONNÉES
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
    profiles = mes_athletes()
    dict_profiles = {p["id"]: p.get("full_name", "") for p in profiles}
    dict_athletes = {p.get("full_name"): p["id"] for p in profiles if p.get("role") == "athlete" and p.get("full_name")}
    
    if dict_athletes:
        noms_sel = st.multiselect("Joueur(s) :", list(dict_athletes.keys()), default=list(dict_athletes.keys())[:1])
        scope_ids = [dict_athletes[n] for n in noms_sel]
        if scope_ids:
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
            render_analytique(df_resp_an, df_gps_an, events_by_id_an, noms_scope, "joueur" if len(noms_sel) == 1 else "multi", noms_sel[0] if len(noms_sel) == 1 else "Sélection", "an")
    else:
        st.info("Aucun athlète disponible.")

# =====================================================================
# PAGE : GESTION DES PROFILS
# =====================================================================
elif menu == "⚙️ Gestion des profils":
    st.header("⚙️ Gestion des profils")
    afficher_flash()
    tab_ath, tab_teams, tab_comptes = st.tabs(["👤 Athlètes & Tests", "🛡️ Équipes", "🔑 Comptes"])

    with tab_ath:
        ath_data = mes_athletes()
        dict_ath_lookup = {a.get("full_name", f"Athlète {a['id']}"): a for a in ath_data}
        if dict_ath_lookup:
            selected_ath_name = st.selectbox("Sélectionner un athlète :", list(dict_ath_lookup.keys()), key="sel_ath_mgt_prof")
            selected_ath = dict_ath_lookup[selected_ath_name]
            st.write(f"Nom : {selected_ath.get('full_name')}")
        else:
            st.info("Aucun athlète.")

    with tab_teams:
        teams_list = mes_equipes()
        new_t = st.text_input("Nom de la nouvelle équipe", key="input_create_team_mgt")
        if st.button("Créer l'équipe", type="primary"):
            if new_t:
                creer_equipe(new_t, created_by=mon_id)
                flash_succes("Équipe créée !")
                st.rerun()

    with tab_comptes:
        st.subheader("🔑 Créer un compte athlète")
        with st.form("form_creer_compte_mgt"):
            c1, c2 = st.columns(2)
            with c1:
                new_email = st.text_input("E-mail")
                new_password = st.text_input("Mot de passe", type="password")
            with c2:
                new_full_name = st.text_input("Nom complet")
            if st.form_submit_button("🚀 Créer le compte", type="primary"):
                if new_email and new_password and new_full_name:
                    ok, msg = creer_compte(new_email, new_password, new_full_name, "athlete", None, created_by=mon_id)
                    if ok:
                        flash_succes(msg)
                        st.rerun()
                    else:
                        st.error(msg)

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
    st.write("Créez sur-mesure des bandes sonores rythmées par des bips haute intensité.")
