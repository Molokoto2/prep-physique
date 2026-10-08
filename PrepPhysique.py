import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import requests
import base64

from sports_analytics import (
    supabase,
    SUPABASE_URL,
    SUPABASE_KEY,
    # Auth / comptes
    connexion,
    deconnexion,
    creer_compte,
    modifier_compte,
    supprimer_compte,
    lister_comptes,
    # Profils / équipes
    ajouter_athlete_manual,
    modifier_athlete,
    supprimer_profil_athlete,
    creer_equipe,
    supprimer_equipe,
    # Blessures / disponibilité
    FORMAT_BLESSURE,
    obtenir_reponses_avec_definitions,
    calculer_statut_disponibilite,
    enregistrer_reponse_evenement,
    obtenir_reponse_evenement,
    # Questionnaires : assignation par séance / portée
    definir_minutes_avant,
    definir_minutes_apres,
    definir_type_questionnaire,
    assigner_questionnaire,
    obtenir_assignations,
    questionnaire_disponible_pour,
    obtenir_fichiers_evenement,
    # GPS
    lire_fichier_gps,
    matcher_nom_athlete,
    enregistrer_rapport_gps,
    obtenir_rapports_gps,
    COLONNES_GPS_NUMERIQUES,
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

# -------------------------------------------------------------------
# CONFIGURATION ET STYLE
# -------------------------------------------------------------------
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

    /* ---------- Typographie ---------- */
    h1, h2, h3, h4, h5 {
        font-family: 'Sora', sans-serif !important;
        color: var(--text-main) !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }
    h1 { font-weight: 800 !important; }
    p, span, label, .stMarkdown, .stCaption { font-family: 'Inter', sans-serif; }
    [data-testid="stCaptionContainer"] { color: var(--text-dim) !important; }

    /* ---------- Sidebar ---------- */
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

    /* ---------- Boutons ---------- */
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

    /* ---------- Cartes / formulaires / expanders ---------- */
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

    /* ---------- Métriques ---------- */
    div[data-testid="stMetric"] {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-left: 3px solid var(--accent);
        border-radius: 12px;
        padding: 14px 18px;
    }
    div[data-testid="stMetricLabel"] { color: var(--text-dim) !important; }
    div[data-testid="stMetricValue"] { font-family: 'Sora', sans-serif; color: var(--text-main) !important; }

    /* ---------- Onglets ---------- */
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

    /* ---------- Champs de saisie ---------- */
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

    /* ---------- Tableaux ---------- */
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border-soft); }

    hr { border-color: var(--border-soft) !important; }

    /* ---------- Badges de statut ---------- */
    .badge-dispo {
        background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.4);
        padding: 3px 12px; border-radius: 999px; font-size: 0.85em; font-weight: 600;
    }
    .badge-blesse {
        background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.4);
        padding: 3px 12px; border-radius: 999px; font-size: 0.85em; font-weight: 600;
    }

    /* ---------- Bandeau de marque (sidebar) ---------- */
    .brand-kicker {
        font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.35em;
        background: linear-gradient(90deg, var(--accent) 0%, var(--accent-2) 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        letter-spacing: -0.02em; margin-bottom: 0;
    }
    .brand-tagline { color: var(--text-dim); font-size: 0.8em; margin-top: -6px; margin-bottom: 14px; }
</style>
""", unsafe_allow_html=True)

LABEL_QUESTION_BLESSURE = "Blessure / douleur empêchant de s'entraîner ?"

# =====================================================================
# AUTHENTIFICATION (obligatoire pour lancer le logiciel)
# =====================================================================
if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

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
        st.caption("Un compte est requis pour accéder au logiciel. Contactez votre coach/administrateur si vous n'en avez pas.")

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
                st.success(f"Bienvenue {profile.get('full_name', '')} !")
                st.rerun()

if not st.session_state.user_profile:
    ecran_connexion()
    st.stop()

profil_connecte = st.session_state.user_profile
role_connecte = profil_connecte.get("role", "athlete")
mon_id = profil_connecte.get("id")

# -------------------------------------------------------------------
# BARRE LATÉRALE : identité + navigation
# -------------------------------------------------------------------
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
    <span style="color:var(--text-dim); font-size:1em;">Prép. physique & suivi de performance</span>
</div>
""", unsafe_allow_html=True)

if role_connecte == "coach":
    menu_options = [
        "📅 Planning & Séances",
        "📁 Fichiers & Rapports GPS",
        "📝 Questionnaires",
        "📊 Analytique",
        "⚙️ Gestion Profils, Équipes & Comptes",
        "🔊 Générateur de Bips Audio",
    ]
else:
    # Un athlète connecté au logiciel n'a accès qu'à ses propres données.
    menu_options = [
        "📅 Séances à venir",
        "📆 Calendrier",
        "📊 Mes données",
    ]


def rendre_formulaire_questionnaire(q_obj, event_id, key_suffix, reponses_deja=None, athlete_id=None):
    """
    Affiche le formulaire d'un questionnaire pour une séance donnée, pré-rempli
    si une réponse existe déjà, et enregistre en fusionnant avec les réponses
    existantes de cette séance (une séance peut avoir un Wellness ET un RPE).
    Par défaut, enregistre pour l'utilisateur connecté (athlète) ; le coach peut
    passer athlete_id explicitement pour saisir à la place d'un joueur.
    """
    cible_id = athlete_id or mon_id
    reponses_deja = reponses_deja or {}
    answers_dict = {}
    rpe_val = None
    with st.form(f"form_{key_suffix}"):
        for idx, q in enumerate(q_obj.get("questions", [])):
            lbl = q.get("label", f"Question {idx + 1}")
            fmt = q.get("format")
            valeur_existante = reponses_deja.get(lbl)

            if fmt == "scale":
                scale_max = int(q.get("scale_max", 5))
                options = list(range(1, scale_max + 1))
                try:
                    idx_defaut = options.index(int(float(valeur_existante))) if valeur_existante not in (None, "") else 0
                except (ValueError, TypeError):
                    idx_defaut = 0
                ans = st.selectbox(f"{lbl} (1-{scale_max})", options, index=idx_defaut, key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = float(ans)
                if "rpe" in lbl.lower():
                    rpe_val = float(ans)
            elif fmt == "number":
                try:
                    val_defaut = float(valeur_existante) if valeur_existante not in (None, "") else 0.0
                except (ValueError, TypeError):
                    val_defaut = 0.0
                ans = st.number_input(lbl, value=val_defaut, key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = float(ans)
            elif fmt == FORMAT_BLESSURE:
                idx_defaut = 1 if str(valeur_existante).strip().lower() == "oui" else 0
                ans = st.selectbox(f"🚑 {lbl}", ["Non", "Oui"], index=idx_defaut, key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = ans
            else:
                ans = st.text_input(lbl, value=str(valeur_existante) if valeur_existante is not None else "", key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = ans

        libelle_bouton = "💾 Mettre à jour" if reponses_deja else "🚀 Envoyer"
        if st.form_submit_button(libelle_bouton, type="primary"):
            ok, err = enregistrer_reponse_evenement(cible_id, event_id, q_obj["id"], answers_dict, rpe_val)
            if ok:
                st.session_state.pop("cache_statuts_dispo", None)
                st.success("Réponses enregistrées !")
                st.rerun()
            else:
                st.error(f"Erreur lors de l'enregistrement : {err}")


def _parser_datetime_event(ev, champ="start_time"):
    try:
        return datetime.fromisoformat((ev.get(champ) or "").replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def afficher_fichiers_evenement(event_id, key_prefix=""):
    """Affiche (et permet de télécharger) les documents publiés pour une séance."""
    fichiers = obtenir_fichiers_evenement(event_id)
    if not fichiers:
        return
    st.markdown("##### 📎 Documents de la séance")
    for f in fichiers:
        f_url = f.get("file_url", "")
        if f_url.startswith("data:"):
            try:
                st.download_button(
                    f"💾 {f.get('title', 'Document')}",
                    data=base64.b64decode(f_url.split(",")[1]),
                    file_name=f.get("file_name", "document.pdf"),
                    key=f"{key_prefix}_dl_{f['id']}"
                )
            except Exception:
                st.caption(f"⚠️ {f.get('title', 'Document')} (fichier indisponible)")
        else:
            st.markdown(f"📄 [{f.get('title', 'Document')}]({f_url})")
        if f.get("description"):
            st.caption(f.get("description"))

menu = st.sidebar.radio("Navigation", menu_options)

# -------------------------------------------------------------------
# STORES LOCAUX & FONCTIONS SUPABASE DIRECTES
# -------------------------------------------------------------------
if "local_tests_store" not in st.session_state:
    st.session_state.local_tests_store = {}

def get_athlete_tests(athlete_id):
    return st.session_state.local_tests_store.get(athlete_id, {})

def save_athlete_test(athlete_id, test_name, value, unit):
    if athlete_id not in st.session_state.local_tests_store:
        st.session_state.local_tests_store[athlete_id] = {}
    st.session_state.local_tests_store[athlete_id][test_name] = {
        "valeur": value,
        "unite": unit,
        "date": datetime.now().strftime("%d/%m/%Y")
    }

def upload_file_direct_http(bucket_name, storage_path, file_bytes, mime_type):
    """Contourne l'erreur WinError 10035 / Socket en utilisant REST direct."""
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
    """Petit cache mémoire (session) pour éviter de recalculer 10x par run."""
    if "cache_statuts_dispo" not in st.session_state:
        profiles_all = supabase.table("profiles").select("*").execute().data or []
        responses_def = obtenir_reponses_avec_definitions()
        st.session_state.cache_statuts_dispo = calculer_statut_disponibilite(profiles_all, responses_def)
    return st.session_state.cache_statuts_dispo


# =====================================================================
# PAGE : PLANNING & SÉANCES (avec disponibilité / blessures)
# =====================================================================
if menu == "📅 Planning & Séances":
    st.header("📅 Planning & Séances")

    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute()
    athletes_list = res_athletes.data if res_athletes.data else []
    dict_athletes = {a.get("full_name", f"Athlète {a['id']}"): a["id"] for a in athletes_list if a.get("full_name")}

    statuts = get_statuts_disponibilite()
    ids_blesses = {aid for aid, s in statuts.items() if s["statut"] == "blesse"}
    n_blesses = len(ids_blesses)
    n_dispo = len(dict_athletes) - n_blesses

    st.markdown("#### 🩹 Disponibilité de l'effectif")
    c_stat1, c_stat2, c_stat3 = st.columns(3)
    c_stat1.metric("👥 Effectif total", len(dict_athletes))
    c_stat2.metric("✅ Disponibles", n_dispo)
    c_stat3.metric("🚑 En réathlétisation", n_blesses)

    with st.expander("Voir le détail par joueur", expanded=(n_blesses > 0)):
        if dict_athletes:
            for nom, aid in sorted(dict_athletes.items()):
                s = statuts.get(aid, {"statut": "disponible", "depuis": None})
                if s["statut"] == "blesse":
                    depuis = f" — depuis le {s['depuis']}" if s.get("depuis") else ""
                    st.markdown(f"🚑 **{nom}** — <span class='badge-blesse'>En réathlétisation</span>{depuis}", unsafe_allow_html=True)
                else:
                    st.markdown(f"🟢 **{nom}** — <span class='badge-dispo'>Disponible</span>", unsafe_allow_html=True)
        else:
            st.caption("Aucun athlète enregistré.")

    st.markdown("---")

    tab_nouvelle, tab_existantes = st.tabs(["🆕 Planifier une nouvelle séance", "📋 Séances planifiées (modifier / supprimer)"])

    with tab_nouvelle:
        # Libellés d'affichage avec marqueur de blessure dans le sélecteur d'athlète
        def label_avec_statut(nom):
            aid = dict_athletes[nom]
            return f"🚑 {nom} (réathlétisation)" if aid in ids_blesses else nom

        noms_tries = sorted(dict_athletes.keys())
        labels_affiches = {label_avec_statut(n): n for n in noms_tries}

        col_a, col_b = st.columns(2)
        with col_a:
            title = st.text_input("Titre de la séance")
            event_type = st.selectbox("Type d'événement", ["training", "match"])
            athlete_sel_label = st.selectbox("Athlète concerné", ["-- Tous les athlètes --"] + list(labels_affiches.keys()))
            exclure_blesses = st.checkbox(
                "🚑 Exclure automatiquement les joueurs en réathlétisation de '-- Tous les athlètes --'",
                value=True
            )
            location = st.text_input("Lieu")

        with col_b:
            event_date = st.date_input("Date de la séance", datetime.now())
            start_time = st.time_input("Heure de début", datetime.strptime("10:00", "%H:%M").time())
            end_time = st.time_input("Heure de fin", datetime.strptime("11:30", "%H:%M").time())

        st.markdown("---")
        is_recurring = st.checkbox("🔄 Activer la répétition hebdomadaire", value=False)
        until_date = st.date_input("Date de fin de la répétition", event_date + timedelta(days=60)) if is_recurring else None

        if st.button("🚀 Planifier la/les séance(s)", type="primary"):
            if not title:
                st.error("Veuillez saisir un titre.")
            else:
                if athlete_sel_label == "-- Tous les athlètes --":
                    target_ids = [
                        aid for nom, aid in dict_athletes.items()
                        if not (exclure_blesses and aid in ids_blesses)
                    ]
                else:
                    target_ids = [dict_athletes[labels_affiches[athlete_sel_label]]]

                res_coach = supabase.table("profiles").select("id").eq("role", "coach").limit(1).execute()
                coach_uuid = res_coach.data[0]["id"] if res_coach.data else None

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
                            "title": title,
                            "event_type": event_type,
                            "start_time": dt_start.isoformat(),
                            "end_time": dt_end.isoformat(),
                            "location": location or "Non spécifié",
                            "athlete_id": a_id
                        }
                        if coach_uuid:
                            e_data["coach_id"] = coach_uuid
                        events_to_insert.append(e_data)

                if not events_to_insert:
                    st.warning("Aucun joueur disponible à programmer (tous en réathlétisation ?).")
                else:
                    try:
                        supabase.table("events").insert(events_to_insert).execute()
                        st.success(f"✅ Séance(s) planifiée(s) pour {len(target_ids)} joueur(s) !")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erreur Supabase : {ex}")

    with tab_existantes:
        import calendar as _calendar

        dict_athletes_inv = {v: k for k, v in dict_athletes.items()}
        tous_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []

        if not tous_events:
            st.info("Aucune séance planifiée pour le moment.")
        else:
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                filtre_athlete = st.selectbox(
                    "Filtrer par athlète :", ["-- Tous --"] + sorted(dict_athletes.keys()), key="filtre_seance_athlete"
                )
            with c_f2:
                filtre_type = st.selectbox("Filtrer par type :", ["-- Tous --", "training", "match"], key="filtre_seance_type")

            events_filtres = tous_events
            if filtre_athlete != "-- Tous --":
                events_filtres = [e for e in events_filtres if e.get("athlete_id") == dict_athletes.get(filtre_athlete)]
            if filtre_type != "-- Tous --":
                events_filtres = [e for e in events_filtres if e.get("event_type") == filtre_type]

            # Indexe les séances par jour (YYYY-MM-DD)
            events_par_jour = {}
            for ev in events_filtres:
                try:
                    d = datetime.fromisoformat((ev.get("start_time") or "").replace("Z", "+00:00")).date()
                except Exception:
                    continue
                events_par_jour.setdefault(d, []).append(ev)

            if "cal_mois_ref" not in st.session_state:
                st.session_state.cal_mois_ref = datetime.now().date().replace(day=1)
            if "cal_event_selectionne" not in st.session_state:
                st.session_state.cal_event_selectionne = None

            c_nav1, c_nav2, c_nav3 = st.columns([1, 3, 1])
            with c_nav1:
                if st.button("◀ Mois précédent", use_container_width=True):
                    ref = st.session_state.cal_mois_ref
                    st.session_state.cal_mois_ref = (ref.replace(day=1) - timedelta(days=1)).replace(day=1)
                    st.rerun()
            with c_nav2:
                st.markdown(f"<h4 style='text-align:center;'>📅 {st.session_state.cal_mois_ref.strftime('%B %Y').capitalize()}</h4>", unsafe_allow_html=True)
            with c_nav3:
                if st.button("Mois suivant ▶", use_container_width=True):
                    ref = st.session_state.cal_mois_ref
                    mois_suivant = (ref.replace(day=28) + timedelta(days=4)).replace(day=1)
                    st.session_state.cal_mois_ref = mois_suivant
                    st.rerun()

            annee, mois = st.session_state.cal_mois_ref.year, st.session_state.cal_mois_ref.month
            semaines = _calendar.monthcalendar(annee, mois)
            jours_labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

            cols_header = st.columns(7)
            for c, jl in zip(cols_header, jours_labels):
                c.markdown(f"<div style='text-align:center; color:#94a3b8; font-weight:600;'>{jl}</div>", unsafe_allow_html=True)

            for semaine in semaines:
                cols_semaine = st.columns(7)
                for c, jour_num in zip(cols_semaine, semaine):
                    if jour_num == 0:
                        c.markdown("&nbsp;", unsafe_allow_html=True)
                        continue
                    date_cell = datetime(annee, mois, jour_num).date()
                    est_aujourdhui = date_cell == datetime.now().date()
                    style_jour = "color:#38bdf8; font-weight:800;" if est_aujourdhui else "color:#f1f5f9; font-weight:600;"
                    c.markdown(f"<div style='{style_jour}'>{jour_num}</div>", unsafe_allow_html=True)

                    evs_du_jour = events_par_jour.get(date_cell, [])
                    for ev in evs_du_jour[:4]:
                        nom = dict_athletes_inv.get(ev.get("athlete_id"), "?")
                        emoji_type = "⚔️" if ev.get("event_type") == "match" else "🏋️"
                        libelle_court = f"{emoji_type} {ev.get('title', 'Séance')[:10]}"
                        if c.button(libelle_court, key=f"cal_btn_{ev['id']}", help=f"{ev.get('title')} — {nom}", use_container_width=True):
                            st.session_state.cal_event_selectionne = ev["id"]
                            st.rerun()
                    if len(evs_du_jour) > 4:
                        c.caption(f"+{len(evs_du_jour) - 4} autre(s)")

            st.markdown("---")

            ev_id_sel = st.session_state.cal_event_selectionne
            ev_sel = next((e for e in tous_events if e["id"] == ev_id_sel), None) if ev_id_sel else None

            if not ev_sel:
                st.info("👆 Cliquez sur une séance dans le calendrier ci-dessus pour la modifier ou l'annuler.")
            else:
                st.subheader(f"✏️ Modifier : {ev_sel.get('title')}")
                ev_id = ev_sel["id"]

                try:
                    dt_start_existing = datetime.fromisoformat(ev_sel.get("start_time").replace("Z", "+00:00"))
                    dt_end_existing = datetime.fromisoformat(ev_sel.get("end_time").replace("Z", "+00:00"))
                except Exception:
                    dt_start_existing = datetime.now()
                    dt_end_existing = datetime.now() + timedelta(hours=1)

                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    edit_title = st.text_input("Titre", value=ev_sel.get("title", ""), key=f"edit_title_{ev_id}")
                    edit_type = st.selectbox(
                        "Type", ["training", "match"],
                        index=0 if ev_sel.get("event_type") != "match" else 1,
                        key=f"edit_type_{ev_id}"
                    )
                    nom_actuel = dict_athletes_inv.get(ev_sel.get("athlete_id"))
                    liste_noms = sorted(dict_athletes.keys())
                    idx_ath = liste_noms.index(nom_actuel) if nom_actuel in liste_noms else 0
                    edit_athlete_nom = st.selectbox("Athlète concerné", liste_noms, index=idx_ath, key=f"edit_ath_{ev_id}")
                    edit_location = st.text_input("Lieu", value=ev_sel.get("location", ""), key=f"edit_loc_{ev_id}")
                with c_e2:
                    edit_date = st.date_input("Date", value=dt_start_existing.date(), key=f"edit_date_{ev_id}")
                    edit_start = st.time_input("Heure de début", value=dt_start_existing.time(), key=f"edit_start_{ev_id}")
                    edit_end = st.time_input("Heure de fin", value=dt_end_existing.time(), key=f"edit_end_{ev_id}")

                c_b1, c_b2, c_b3 = st.columns(3)
                with c_b1:
                    if st.button("💾 Enregistrer les modifications", type="primary", key=f"save_ev_{ev_id}"):
                        maj = {
                            "title": edit_title,
                            "event_type": edit_type,
                            "athlete_id": dict_athletes[edit_athlete_nom],
                            "location": edit_location or "Non spécifié",
                            "start_time": datetime.combine(edit_date, edit_start).isoformat(),
                            "end_time": datetime.combine(edit_date, edit_end).isoformat(),
                        }
                        supabase.table("events").update(maj).eq("id", ev_id).execute()
                        st.success("Séance mise à jour !")
                        st.rerun()
                with c_b2:
                    if st.button("❌ Annuler / Supprimer cette séance", type="primary", key=f"del_ev_{ev_id}"):
                        supabase.table("events").delete().eq("id", ev_id).execute()
                        st.session_state.cal_event_selectionne = None
                        st.success("Séance supprimée !")
                        st.rerun()
                with c_b3:
                    if st.button("✖ Fermer", key=f"close_ev_{ev_id}"):
                        st.session_state.cal_event_selectionne = None
                        st.rerun()

# =====================================================================
# PAGE : FICHIERS & RAPPORTS GPS (PDF/Images + import Excel GPS)
# =====================================================================
elif menu == "📁 Fichiers & Rapports GPS":
    st.header("📁 Fichiers de Séances & Rapports GPS")

    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
    dict_athletes = {a.get("full_name"): a["id"] for a in res_athletes if a.get("full_name")}

    # Récupération des séances planifiées
    res_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []

    dict_events = {}
    dict_events_info = {}
    for ev in res_events:
        ev_id = ev["id"]
        ev_title = ev.get("title") or ev.get("name") or "Séance sans titre"
        ev_start = ev.get("start_time", "")
        ev_ath_id = ev.get("athlete_id")

        date_str = ""
        if ev_start:
            try:
                dt = datetime.fromisoformat(ev_start.replace('Z', '+00:00'))
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                date_str = str(ev_start)[:16]

        ath_name = "Tous / Inconnu"
        for name, aid in dict_athletes.items():
            if aid == ev_ath_id:
                ath_name = name
                break

        label = f"{ev_title} ({date_str}) - Athlète : {ath_name}"
        dict_events[label] = ev
        dict_events_info[ev_id] = {"title": ev_title, "date": date_str, "athlete": ath_name}

    tab_upload, tab_list, tab_gps = st.tabs([
        "📤 Joindre un PDF à une séance",
        "📚 Documents publiés",
        "🛰️ Importer un rapport GPS (xlsx)",
    ])

    with tab_upload:
        if not dict_events:
            st.warning("Aucune séance n'est planifiée. Veuillez créer une séance dans l'onglet '📅 Planning & Séances'.")
        else:
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                selected_event_label = st.selectbox("📌 Choisir la séance concernée :", list(dict_events.keys()))
                selected_event = dict_events[selected_event_label]

                default_name = selected_event.get("title") or selected_event.get("name") or "Séance PDF"
                session_title = st.text_input("Nom du document / Titre du PDF :", value=default_name)
                description = st.text_area("Instructions ou remarques complémentaires :")

            with col_u2:
                uploaded_file = st.file_uploader("Choisir le fichier PDF ou Image", type=["pdf", "png", "jpg", "jpeg"])

            if st.button("🚀 Attribuer et publier le PDF sur la séance", type="primary"):
                if not session_title or not uploaded_file:
                    st.error("Veuillez donner un nom et joindre un fichier.")
                else:
                    file_bytes = uploaded_file.read()
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    mime_type = uploaded_file.type or "application/octet-stream"

                    clean_filename = "".join(c for c in uploaded_file.name if c.isalnum() or c in "._-")
                    storage_path = f"{int(datetime.now().timestamp())}_{clean_filename}"

                    try:
                        file_url = upload_file_direct_http("session-files", storage_path, file_bytes, mime_type)
                    except Exception:
                        b64_data = base64.b64encode(file_bytes).decode('utf-8')
                        file_url = f"data:{mime_type};base64,{b64_data}"

                    record = {
                        "title": session_title,
                        "description": description,
                        "file_name": uploaded_file.name,
                        "file_url": file_url,
                        "file_type": file_ext,
                        "athlete_id": selected_event.get("athlete_id"),
                        "created_at": datetime.now().isoformat()
                    }

                    if selected_event.get("id"):
                        record["event_id"] = selected_event.get("id")

                    try:
                        supabase.table("session_files").insert([record]).execute()
                        st.success("✅ Fichier PDF associé avec succès à la séance !")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erreur Supabase lors de la sauvegarde : {ex}")

    with tab_list:
        files_db = supabase.table("session_files").select("*").order("created_at", desc=True).execute().data or []
        dict_ath_inv = {v: k for k, v in dict_athletes.items()}

        if files_db:
            for f in files_db:
                f_id = f.get("id")
                f_ath = dict_ath_inv.get(f.get("athlete_id"), "Athlète inconnu")
                ev_id = f.get("event_id")
                ev_info = dict_events_info.get(ev_id, {})
                ev_title_display = ev_info.get("title", "Séance globale")
                ev_date_display = ev_info.get("date", "")

                with st.expander(f"📄 {f.get('title')} — Séance : {ev_title_display} ({ev_date_display}) — Pour : {f_ath}"):
                    st.write(f"**Fichier :** `{f.get('file_name')}`")
                    if f.get("description"):
                        st.write(f"**Instructions :** {f.get('description')}")
                    f_url = f.get("file_url", "")
                    if f_url.startswith("data:"):
                        st.download_button("💾 Télécharger", data=base64.b64decode(f_url.split(",")[1]), file_name=f.get('file_name', 'document.pdf'), key=f"dl_{f_id}")
                    else:
                        st.markdown(f"[🔗 Consulter / Télécharger]({f_url})")
                    if st.button("❌ Supprimer", key=f"del_f_{f_id}"):
                        supabase.table("session_files").delete().eq("id", f_id).execute()
                        st.rerun()

    with tab_gps:
        st.subheader("🛰️ Importer un rapport GPS (fichier Excel)")
        st.caption(
            "Le format fixe du club (export CSV type Catapult/Titan) est reconnu automatiquement : seules les lignes "
            "de la période « Session » sont importées, avec les colonnes Accelerations, Décélérations, Durée, Distance, "
            "Vmax, Distance/min, Distance sprint, Distance HI et Distance haute vitesse."
        )
        if not dict_events:
            st.warning("Aucune séance n'est planifiée. Créez d'abord une séance dans '📅 Planning & Séances'.")
        else:
            gps_event_label = st.selectbox("📌 Séance concernée par ce rapport GPS :", list(dict_events.keys()), key="gps_event_sel")
            gps_file = st.file_uploader("Fichier GPS (.csv, .xlsx ou .xls)", type=["csv", "xlsx", "xls"], key="gps_file_uploader")

            if gps_file:
                try:
                    lignes = lire_fichier_gps(gps_file.read(), nom_fichier=gps_file.name)
                except Exception as ex:
                    lignes = []
                    st.error(f"Impossible de lire le fichier : {ex}")

                if lignes:
                    df_preview = pd.DataFrame(lignes)
                    st.write(f"**Aperçu ({len(lignes)} joueur(s) détecté(s), période 'Session' uniquement) :**")
                    st.dataframe(df_preview, use_container_width=True)

                    noms_reconnus, noms_inconnus = [], []
                    for l in lignes:
                        nom = l.get("nom_joueur", "")
                        if matcher_nom_athlete(nom, dict_athletes):
                            noms_reconnus.append(nom)
                        else:
                            noms_inconnus.append(nom)
                    if noms_inconnus:
                        st.warning(f"⚠️ Noms non reconnus dans le logiciel (vérifiez l'orthographe du profil athlète) : {', '.join(noms_inconnus)}")

                    if st.button("💾 Importer ce rapport GPS", type="primary", disabled=(len(noms_reconnus) == 0)):
                        selected_event = dict_events[gps_event_label]
                        n_inseres, non_trouves = enregistrer_rapport_gps(selected_event["id"], lignes, dict_athletes)
                        st.success(f"✅ {n_inseres} ligne(s) GPS importée(s) et rattachée(s) à la séance.")
                        if non_trouves:
                            st.warning(f"Non importés (nom non reconnu) : {', '.join(non_trouves)}")
                        st.rerun()
                else:
                    st.info("Aucune ligne exploitable trouvée dans ce fichier (vérifiez qu'il contient bien une période 'Session').")

# =====================================================================
# PAGE : QUESTIONNAIRES (Création + Envoi + Réponse, fusionnés)
# =====================================================================
elif menu == "📝 Questionnaires":
    st.header("📝 Questionnaires")
    tab_creer, tab_envoyer, tab_repondre = st.tabs([
        "🆕 Créer un modèle",
        "📩 Assigner à des athlètes",
        "✍️ Répondre (saisie manuelle)",
    ])

    # --- Onglet Création ---
    with tab_creer:
        q_title = st.text_input("Titre du questionnaire")
        q_type = "pre_event" if "Pre" in st.selectbox("Type", ["Pre-Event (Wellness)", "Post-Event (RPE)"]) else "post_event"

        if "questions_draft" not in st.session_state:
            st.session_state.questions_draft = []

        c1, c2, c3 = st.columns([4, 3, 2])
        with c1:
            new_q_label = st.text_input("Intitulé de la question")
        with c2:
            q_format = st.selectbox(
                "Format",
                ["Échelle numérique (Note)", "Texte libre", "Nombre libre", "🚑 Oui/Non (marque une blessure)"]
            )
        with c3:
            scale_max = st.number_input("Max", min_value=2, max_value=10, value=5) if "Échelle" in q_format else None

        if "blessure" in q_format.lower():
            st.caption("La dernière réponse 'Oui' à cette question place le joueur en réathlétisation jusqu'à une réponse 'Non'.")

        if st.button("+ Ajouter la question"):
            if new_q_label:
                if "blessure" in q_format.lower():
                    fmt = FORMAT_BLESSURE
                elif "Échelle" in q_format:
                    fmt = "scale"
                elif "Nombre" in q_format:
                    fmt = "number"
                else:
                    fmt = "text"
                st.session_state.questions_draft.append({
                    "label": new_q_label,
                    "format": fmt,
                    "scale_max": scale_max
                })
                st.rerun()

        for idx, q in enumerate(st.session_state.questions_draft):
            marqueur = " 🚑" if q["format"] == FORMAT_BLESSURE else ""
            st.info(f"Q{idx+1}: {q['label']} ({q['format']}){marqueur}")

        if st.button("💾 Enregistrer le questionnaire complet", type="primary"):
            if q_title and st.session_state.questions_draft:
                supabase.table("questionnaires").insert({"title": q_title, "type": q_type, "questions": st.session_state.questions_draft}).execute()
                st.session_state.questions_draft = []
                st.success("Enregistré !")
                st.rerun()

    # --- Onglet Envoi / Assignation ---
    with tab_envoyer:
        q_data = supabase.table("questionnaires").select("*").execute().data or []
        a_data = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []

        if q_data and a_data:
            dict_q_obj = {q["title"]: q for q in q_data}
            dict_a = {a["full_name"]: a["id"] for a in a_data if a.get("full_name")}

            sel_q_title = st.selectbox("Questionnaire :", list(dict_q_obj.keys()), key="envoi_q_sel")
            q_obj_sel = dict_q_obj[sel_q_title]
            type_actuel = q_obj_sel.get("type")
            direction = st.radio(
                "Ce questionnaire doit s'ouvrir :",
                ["🌅 Avant la séance (ex : Wellness)", "🌙 Après la séance (ex : RPE)"],
                index=0 if type_actuel == "pre_event" else 1,
                key="envoi_direction",
                horizontal=True
            )
            est_pre_event = direction.startswith("🌅")

            minutes_avant = None
            minutes_apres = None
            if est_pre_event:
                minutes_avant = st.number_input(
                    "⏰ Ouvrir ce questionnaire combien de minutes AVANT chaque séance ?",
                    min_value=5, max_value=1440, step=5,
                    value=int(q_obj_sel.get("trigger_minutes") or 60),
                    key="envoi_minutes"
                )
                st.caption("Le questionnaire se ferme automatiquement au début de la séance.")
            else:
                minutes_apres = st.number_input(
                    "⏰ Rester ouvert combien de minutes APRÈS la fin de chaque séance ?",
                    min_value=5, max_value=1440, step=5,
                    value=int(q_obj_sel.get("post_window_minutes") or 180),
                    key="envoi_minutes_apres"
                )
                st.info("Un questionnaire réglé « après la séance » est proposé à TOUS les athlètes une fois leur séance terminée, dans la fenêtre de temps ci-dessus (l'assignation ci-dessous reste possible pour le restreindre à certains joueurs).")

            sel_a = st.multiselect("Athlète(s) concerné(s) :", list(dict_a.keys()), key="envoi_a_sel")

            portee = st.radio(
                "Portée de l'assignation :",
                ["Toutes les séances de ce(s) athlète(s)", "Une séance précise"],
                key="envoi_portee"
            )

            event_id_choisi = None
            if portee == "Une séance précise":
                if not sel_a:
                    st.caption("Choisissez d'abord au moins un athlète pour lister ses séances.")
                else:
                    ids_ath_sel = [dict_a[n] for n in sel_a]
                    events_possibles = supabase.table("events").select(
                        "id, title, start_time, athlete_id"
                    ).in_("athlete_id", ids_ath_sel).order("start_time").execute().data or []
                    dict_ath_inv_envoi = {v: k for k, v in dict_a.items()}
                    dict_events_possibles = {}
                    for ev in events_possibles:
                        dstr = (ev.get("start_time") or "")[:16].replace("T", " ")
                        nom_ath = dict_ath_inv_envoi.get(ev.get("athlete_id"), "?")
                        dict_events_possibles[f"{ev.get('title', 'Séance')} — {nom_ath} — {dstr}"] = ev["id"]
                    if dict_events_possibles:
                        sel_event_label = st.selectbox("Séance concernée :", list(dict_events_possibles.keys()), key="envoi_event_sel")
                        event_id_choisi = dict_events_possibles[sel_event_label]
                    else:
                        st.warning("Aucune séance planifiée pour ce(s) athlète(s).")

            if st.button("Attribuer", type="primary", key="envoi_btn"):
                if not sel_a:
                    st.error("Sélectionnez au moins un athlète.")
                elif portee == "Une séance précise" and not event_id_choisi:
                    st.error("Sélectionnez une séance.")
                else:
                    definir_type_questionnaire(q_obj_sel["id"], "pre_event" if est_pre_event else "post_event")
                    if minutes_avant is not None:
                        definir_minutes_avant(q_obj_sel["id"], int(minutes_avant))
                    if minutes_apres is not None:
                        definir_minutes_apres(q_obj_sel["id"], int(minutes_apres))
                    for name in sel_a:
                        assigner_questionnaire(q_obj_sel["id"], dict_a[name], event_id_choisi)
                    st.success("Questionnaire assigné !")
                    st.rerun()
        else:
            st.info("Créez d'abord un questionnaire et/ou un athlète.")

    # --- Onglet Réponse manuelle (le coach saisit pour un joueur) ---
    with tab_repondre:
        athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
        dict_athletes = {a.get("full_name"): a["id"] for a in athletes if a.get("full_name")}

        if dict_athletes:
            sel_athlete_name = st.selectbox("Choisir l'athlète :", list(dict_athletes.keys()), key="rep_ath_sel")
            selected_athlete_id = dict_athletes[sel_athlete_name]

            events_ath = supabase.table("events").select("id, title, start_time").eq(
                "athlete_id", selected_athlete_id
            ).order("start_time", desc=True).limit(50).execute().data or []
            dict_events_rep = {}
            for ev in events_ath:
                dstr = (ev.get("start_time") or "")[:16].replace("T", " ")
                dict_events_rep[f"{ev.get('title', 'Séance')} — {dstr}"] = ev["id"]

            q_list = supabase.table("questionnaires").select("*").execute().data or []
            if not dict_events_rep:
                st.warning("Aucune séance planifiée pour cet athlète. Créez d'abord une séance dans '📅 Planning & Séances' avant de saisir une réponse.")
            elif q_list:
                sel_event_label = st.selectbox("Séance concernée :", list(dict_events_rep.keys()), key="rep_event_sel")
                selected_event_id = dict_events_rep[sel_event_label]

                dict_q = {q["title"]: q for q in q_list}
                sel_q_title = st.selectbox("Questionnaire :", list(dict_q.keys()), key="rep_q_sel")
                q_obj = dict_q[sel_q_title]

                reponse_existante = obtenir_reponse_evenement(selected_athlete_id, selected_event_id)
                reponses_deja = (reponse_existante.get("answers") or {}) if reponse_existante else {}

                rendre_formulaire_questionnaire(
                    q_obj, selected_event_id, f"coach_manuel_{selected_athlete_id}_{selected_event_id}_{q_obj['id']}",
                    reponses_deja, athlete_id=selected_athlete_id
                )
            else:
                st.info("Aucun questionnaire créé pour le moment.")
        else:
            st.info("Aucun athlète enregistré.")

# =====================================================================
# PAGE (ATHLÈTE) : SÉANCES À VENIR — répondre le jour même (Wellness avant / RPE après)
# =====================================================================
elif menu == "📅 Séances à venir":
    st.header("📅 Mes séances à venir")
    st.caption("La séance la plus proche est en haut. Wellness s'ouvre avant la séance (selon le délai fixé par le coach), RPE après.")

    maintenant = datetime.now()
    events_mine_raw = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []

    a_venir = [
        e for e in events_mine_raw
        if _parser_datetime_event(e) and _parser_datetime_event(e).date() >= maintenant.date()
    ]
    a_venir.sort(key=lambda e: e["start_time"])

    q_all = supabase.table("questionnaires").select("*").execute().data or []
    q_pre = [q for q in q_all if q.get("type") == "pre_event"]
    q_post = [q for q in q_all if q.get("type") != "pre_event"]
    assignations = obtenir_assignations()

    if not a_venir:
        st.info("Aucune séance à venir pour le moment. Revenez une fois qu'une séance aura été planifiée par votre coach.")
    else:
        for i, ev in enumerate(a_venir):
            dt_start = _parser_datetime_event(ev)
            est_aujourdhui = dt_start.date() == maintenant.date()
            emoji = "⚔️" if ev.get("event_type") == "match" else "🏋️"
            titre = f"{emoji} {ev.get('title', 'Séance')} — {dt_start.strftime('%d/%m/%Y à %H:%M')}"
            if est_aujourdhui:
                titre += "  🔴 Aujourd'hui"

            with st.expander(titre, expanded=(i == 0)):
                if ev.get("location"):
                    st.caption(f"📍 {ev['location']}")

                afficher_fichiers_evenement(ev["id"], key_prefix=f"avenir_{ev['id']}")

                reponse_existante = obtenir_reponse_evenement(mon_id, ev["id"])
                reponses_deja = (reponse_existante.get("answers") or {}) if reponse_existante else {}

                # --- Wellness : ouvre X minutes avant la séance, uniquement si assigné ---
                q_pre_dispo = [q for q in q_pre if questionnaire_disponible_pour(q["id"], mon_id, ev["id"], assignations)]
                st.markdown("##### 🌅 Avant la séance — Wellness")
                if not q_pre_dispo:
                    st.caption("Aucun questionnaire Wellness assigné pour cette séance.")
                else:
                    for q in q_pre_dispo:
                        minutes_avant = int(q.get("trigger_minutes") or 60)
                        ouverture = dt_start - timedelta(minutes=minutes_avant)
                        if maintenant < ouverture:
                            st.caption(f"« {q.get('title')} » s'ouvrira à {ouverture.strftime('%d/%m %H:%M')} ({minutes_avant} min avant la séance).")
                        elif maintenant >= dt_start:
                            st.caption(f"« {q.get('title')} » : fenêtre de réponse terminée (la séance a commencé).")
                        else:
                            rendre_formulaire_questionnaire(q, ev["id"], f"avenir_pre_{ev['id']}_{q['id']}", reponses_deja)

                # --- RPE : ouvert à tous, dans la fenêtre définie par le coach après la séance ---
                dt_end = _parser_datetime_event(ev, "end_time") or dt_start
                st.markdown("##### 🌙 Après la séance — RPE")
                if not q_post:
                    st.caption("Aucun questionnaire de type RPE (Post-Event) n'a été créé par votre coach.")
                else:
                    for q in q_post:
                        minutes_apres = int(q.get("post_window_minutes") or 180)
                        fermeture = dt_end + timedelta(minutes=minutes_apres)
                        if maintenant < dt_end:
                            st.caption(f"« {q.get('title')} » s'ouvrira à la fin de la séance ({dt_end.strftime('%d/%m %H:%M')}).")
                        elif maintenant > fermeture:
                            st.caption(f"« {q.get('title')} » : fenêtre de réponse terminée (clôturée à {fermeture.strftime('%d/%m %H:%M')}).")
                        else:
                            rendre_formulaire_questionnaire(q, ev["id"], f"avenir_post_{ev['id']}_{q['id']}", reponses_deja)

# =====================================================================
# PAGE (ATHLÈTE) : MES SÉANCES (calendrier, accès à toutes les séances passées)
# =====================================================================
elif menu == "📆 Calendrier":
    import calendar as _calendar

    st.header("📆 Calendrier")
    st.caption("Vue d'ensemble de toutes tes séances. Pour répondre à un questionnaire, va dans l'onglet '📅 Séances à venir' au moment prévu.")

    events_mine_raw = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
    events_par_jour = {}
    for ev in events_mine_raw:
        d = _parser_datetime_event(ev)
        if d:
            events_par_jour.setdefault(d.date(), []).append(ev)

    if "cal_ath_mois_ref" not in st.session_state:
        st.session_state.cal_ath_mois_ref = datetime.now().date().replace(day=1)
    if "cal_ath_event_selectionne" not in st.session_state:
        st.session_state.cal_ath_event_selectionne = None

    c_nav1, c_nav2, c_nav3 = st.columns([1, 3, 1])
    with c_nav1:
        if st.button("◀ Mois précédent", use_container_width=True, key="ath_cal_prev"):
            ref = st.session_state.cal_ath_mois_ref
            st.session_state.cal_ath_mois_ref = (ref.replace(day=1) - timedelta(days=1)).replace(day=1)
            st.rerun()
    with c_nav2:
        st.markdown(f"<h4 style='text-align:center;'>📅 {st.session_state.cal_ath_mois_ref.strftime('%B %Y').capitalize()}</h4>", unsafe_allow_html=True)
    with c_nav3:
        if st.button("Mois suivant ▶", use_container_width=True, key="ath_cal_next"):
            ref = st.session_state.cal_ath_mois_ref
            st.session_state.cal_ath_mois_ref = (ref.replace(day=28) + timedelta(days=4)).replace(day=1)
            st.rerun()

    annee, mois = st.session_state.cal_ath_mois_ref.year, st.session_state.cal_ath_mois_ref.month
    semaines = _calendar.monthcalendar(annee, mois)
    jours_labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    cols_header = st.columns(7)
    for c, jl in zip(cols_header, jours_labels):
        c.markdown(f"<div style='text-align:center; color:#94a3b8; font-weight:600;'>{jl}</div>", unsafe_allow_html=True)

    for semaine in semaines:
        cols_semaine = st.columns(7)
        for c, jour_num in zip(cols_semaine, semaine):
            if jour_num == 0:
                c.markdown("&nbsp;", unsafe_allow_html=True)
                continue
            date_cell = datetime(annee, mois, jour_num).date()
            est_aujourdhui = date_cell == datetime.now().date()
            style_jour = "color:#38bdf8; font-weight:800;" if est_aujourdhui else "color:#f1f5f9; font-weight:600;"
            c.markdown(f"<div style='{style_jour}'>{jour_num}</div>", unsafe_allow_html=True)

            for ev in events_par_jour.get(date_cell, [])[:4]:
                emoji_type = "⚔️" if ev.get("event_type") == "match" else "🏋️"
                libelle_court = f"{emoji_type} {ev.get('title', 'Séance')[:10]}"
                if c.button(libelle_court, key=f"ath_cal_btn_{ev['id']}", use_container_width=True):
                    st.session_state.cal_ath_event_selectionne = ev["id"]
                    st.rerun()

    st.markdown("---")

    ev_id_sel = st.session_state.cal_ath_event_selectionne
    ev_sel = next((e for e in events_mine_raw if e["id"] == ev_id_sel), None) if ev_id_sel else None

    if not ev_sel:
        st.info("👆 Cliquez sur une séance dans le calendrier ci-dessus pour voir son détail.")
    else:
        dt_start_sel = _parser_datetime_event(ev_sel)
        st.subheader(f"{ev_sel.get('title', 'Séance')} — {dt_start_sel.strftime('%d/%m/%Y à %H:%M') if dt_start_sel else ''}")
        if ev_sel.get("location"):
            st.caption(f"📍 {ev_sel['location']}")

        afficher_fichiers_evenement(ev_sel["id"], key_prefix=f"cal_{ev_sel['id']}")

        reponse_existante = obtenir_reponse_evenement(mon_id, ev_sel["id"])
        reponses_deja = (reponse_existante.get("answers") or {}) if reponse_existante else {}

        st.markdown("##### 📝 Réponses déjà données pour cette séance")
        if reponses_deja:
            cols_rep = st.columns(min(len(reponses_deja), 4) or 1)
            for idx, (question, valeur) in enumerate(reponses_deja.items()):
                with cols_rep[idx % 4]:
                    st.metric(label=question, value=str(valeur))
        else:
            st.caption("Aucune réponse donnée pour cette séance pour le moment.")

        gps_ev = obtenir_rapports_gps(athlete_id=mon_id, event_id=ev_sel["id"])
        if gps_ev:
            st.markdown("---")
            st.markdown("##### 🛰️ Mon rapport GPS pour cette séance")
            g = gps_ev[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Distance totale", f"{g.get('distance_totale_m', '—')} m")
            c2.metric("Vmax", f"{g.get('vmax_kmh', '—')} km/h")
            c3.metric("Distance HI", f"{g.get('distance_haute_intensite_m', '—')} m")

        if st.button("✖ Fermer le détail", key="ath_cal_close"):
            st.session_state.cal_ath_event_selectionne = None
            st.rerun()

# =====================================================================
# PAGE (ATHLÈTE) : MES DONNÉES (RPE / Wellness / GPS personnels)
# =====================================================================
elif menu == "📊 Mes données":
    st.header("📊 Mes données")
    st.caption("Toutes tes réponses aux questionnaires (Wellness, RPE...) et tes rapports GPS, séance par séance.")

    res_resp = supabase.table("questionnaire_responses").select("*").eq("athlete_id", mon_id).execute()
    responses = res_resp.data if res_resp.data else []

    records_flat = []
    for r in responses:
        date_raw = r.get("submitted_at", r.get("created_at", ""))
        date_obj = pd.to_datetime(date_raw) if date_raw else pd.NaT
        date_str = str(date_raw)[:10]

        answers_raw = r.get("answers", {})
        if isinstance(answers_raw, str):
            try:
                answers_raw = json.loads(answers_raw)
            except Exception:
                answers_raw = {}

        if r.get("rpe_score") is not None:
            try:
                records_flat.append({"Date": date_obj, "Date_Str": date_str, "Question": "RPE (Score Global)", "Valeur": float(r.get("rpe_score"))})
            except (ValueError, TypeError):
                pass

        if isinstance(answers_raw, dict):
            for q_title, q_val in answers_raw.items():
                try:
                    val_clean = float(q_val)
                except (ValueError, TypeError):
                    val_clean = str(q_val)
                records_flat.append({"Date": date_obj, "Date_Str": date_str, "Question": str(q_title).strip(), "Valeur": val_clean})

    df_flat = pd.DataFrame(records_flat) if records_flat else pd.DataFrame()

    gps_data = obtenir_rapports_gps(athlete_id=mon_id)
    gps_rows = []
    for g in gps_data:
        ev = g.get("events") or {}
        for metrique in COLONNES_GPS_NUMERIQUES:
            val = g.get(metrique)
            if val is not None:
                gps_rows.append({
                    "Séance": ev.get("title", "Séance"),
                    "Date": (ev.get("start_time") or "")[:10],
                    "Métrique": metrique,
                    "Valeur": val
                })
    df_gps_mine = pd.DataFrame(gps_rows) if gps_rows else pd.DataFrame()

    tab_q_ath, tab_g_ath, tab_gps_ath, tab_brut_ath = st.tabs([
        "📝 Mes réponses", "📈 Graphique", "🛰️ Mon GPS", "📋 Données brutes"
    ])

    with tab_q_ath:
        if not df_flat.empty:
            liste_questions = sorted(df_flat["Question"].unique().tolist())
            sel_q_filter = st.selectbox("Filtrer une question :", ["-- Toutes les questions --"] + liste_questions, key="mesd_q_filter")
            questions_affichage = liste_questions if sel_q_filter == "-- Toutes les questions --" else [sel_q_filter]

            for question_titre in questions_affichage:
                st.markdown(f"### ❓ {question_titre}")
                df_single_q = df_flat[df_flat["Question"] == question_titre].sort_values("Date", ascending=False)
                cols = st.columns(min(len(df_single_q), 4) or 1)
                for idx, (_, row) in enumerate(df_single_q.iterrows()):
                    with cols[idx % 4]:
                        st.metric(label=f"📅 {row['Date_Str']}", value=f"{row['Valeur']}")
                st.write("---")
        else:
            st.info("Aucune réponse enregistrée pour le moment.")

    with tab_g_ath:
        if not df_flat.empty:
            df_num = df_flat[df_flat["Valeur"].apply(lambda x: isinstance(x, (int, float)))]
            unique_q_num = sorted(df_num["Question"].unique().tolist())
            if unique_q_num:
                sel_q_graph = st.selectbox("Choisir la question à analyser :", unique_q_num, key="mesd_q_graph")
                df_target = df_num[df_num["Question"] == sel_q_graph].sort_values("Date")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_target["Date"], y=df_target["Valeur"], mode="lines+markers",
                    name=sel_q_graph, line=dict(width=3), marker=dict(size=10)
                ))
                fig.update_layout(
                    title=f"Évolution : {sel_q_graph}", template="plotly_dark",
                    hovermode="x unified", xaxis_title="Date", yaxis_title="Valeur / Score"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune question numérique exploitable en graphique pour le moment.")
        else:
            st.info("Aucune donnée disponible.")

    with tab_gps_ath:
        if not df_gps_mine.empty:
            metriques_dispo = sorted(df_gps_mine["Métrique"].unique().tolist())
            sel_metrique = st.selectbox(
                "Métrique GPS :", metriques_dispo,
                format_func=lambda m: NOMS_METRIQUES_GPS.get(m, m), key="mesd_gps_metrique"
            )
            df_m = df_gps_mine[df_gps_mine["Métrique"] == sel_metrique].sort_values("Date")
            fig_gps = px.line(
                df_m, x="Séance", y="Valeur", markers=True, template="plotly_dark",
                title=NOMS_METRIQUES_GPS.get(sel_metrique, sel_metrique)
            )
            st.plotly_chart(fig_gps, use_container_width=True)
            st.dataframe(df_m[["Séance", "Date", "Valeur"]], use_container_width=True)
        else:
            st.info("Aucun rapport GPS disponible pour le moment.")

    with tab_brut_ath:
        if not df_flat.empty:
            st.markdown("**Mes réponses aux questionnaires**")
            st.dataframe(df_flat, use_container_width=True)
        if not df_gps_mine.empty:
            st.markdown("**Mes données GPS**")
            st.dataframe(df_gps_mine, use_container_width=True)
        if df_flat.empty and df_gps_mine.empty:
            st.info("Aucune donnée disponible pour le moment.")

# =====================================================================
# PAGE : ANALYTIQUE (RPE/Wellness + comparaisons + GPS)
# =====================================================================
elif menu == "📊 Analytique":
    st.header("📊 Analytique — RPE, Wellness & GPS")

    profiles = supabase.table("profiles").select("*").execute().data or []
    dict_profiles = {p["id"]: p.get("full_name", f"ID-{p['id'][:4]}") for p in profiles}
    dict_athletes = {p.get("full_name"): p["id"] for p in profiles if p.get("full_name") and p.get("role") == "athlete"}
    teams_all = supabase.table("teams").select("*").execute().data or []
    dict_teams_an = {t["name"]: t["id"] for t in teams_all}

    if not dict_athletes:
        st.info("Aucun athlète enregistré pour le moment.")
        st.stop()

    st.markdown("#### 🎯 Choisissez ce que vous voulez analyser")
    mode_analyse = st.radio(
        "Analyser :", ["👤 Un joueur", "👥 Une équipe", "🆚 Plusieurs joueurs (comparaison libre)"],
        horizontal=True, key="analytique_mode"
    )

    scope_joueurs = []
    if mode_analyse == "👤 Un joueur":
        joueur_unique = st.selectbox("Choisir le joueur :", sorted(dict_athletes.keys()), key="analytique_joueur_unique")
        scope_joueurs = [joueur_unique] if joueur_unique else []
    elif mode_analyse == "👥 Une équipe":
        if not dict_teams_an:
            st.warning("Aucune équipe créée. Créez-en une dans '⚙️ Gestion Profils, Équipes & Comptes'.")
        else:
            equipe_choisie = st.selectbox("Choisir l'équipe :", sorted(dict_teams_an.keys()), key="analytique_equipe")
            team_id_choisie = dict_teams_an.get(equipe_choisie)
            scope_joueurs = sorted([
                p.get("full_name") for p in profiles
                if p.get("role") == "athlete" and p.get("team_id") == team_id_choisie and p.get("full_name")
            ])
            if not scope_joueurs:
                st.warning("Cette équipe ne contient aucun joueur pour le moment.")
    else:
        scope_joueurs = st.multiselect(
            "Choisir les joueurs à comparer :", sorted(dict_athletes.keys()), key="analytique_multi_joueurs"
        )

    if not scope_joueurs:
        st.info("👆 Sélectionnez au moins un joueur (ou une équipe) pour afficher les données.")
        st.stop()

    st.markdown("---")

    res_resp = supabase.table("questionnaire_responses").select("*").execute()
    responses = res_resp.data if res_resp.data else []

    records_flat = []
    for r in responses:
        u_id = r.get("athlete_id") or r.get("user_id") or r.get("profile_id")
        joueur_nom = dict_profiles.get(u_id, "Athlète Inconnu")
        date_raw = r.get("submitted_at", r.get("created_at", ""))
        date_obj = pd.to_datetime(date_raw)
        date_str = str(date_raw)[:10]

        answers_raw = r.get("answers", {})
        if isinstance(answers_raw, str):
            try:
                answers_raw = json.loads(answers_raw)
            except Exception:
                answers_raw = {}

        if r.get("rpe_score") is not None:
            try:
                records_flat.append({
                    "Joueur": joueur_nom, "Date": date_obj, "Date_Str": date_str,
                    "Question": "RPE (Score Global)", "Valeur": float(r.get("rpe_score"))
                })
            except (ValueError, TypeError):
                pass

        if isinstance(answers_raw, dict):
            for q_title, q_val in answers_raw.items():
                try:
                    val_clean = float(q_val)
                except (ValueError, TypeError):
                    val_clean = str(q_val)
                records_flat.append({
                    "Joueur": joueur_nom, "Date": date_obj, "Date_Str": date_str,
                    "Question": str(q_title).strip(), "Valeur": val_clean
                })

    df_flat = pd.DataFrame(records_flat) if records_flat else pd.DataFrame()
    if not df_flat.empty:
        df_flat = df_flat[df_flat["Joueur"].isin(scope_joueurs)]

    # ---- Données GPS à plat ----
    gps_all = obtenir_rapports_gps()
    gps_rows = []
    for g in gps_all:
        ev = g.get("events") or {}
        nom = dict_profiles.get(g.get("athlete_id"), "Athlète Inconnu")
        for metrique in COLONNES_GPS_NUMERIQUES:
            val = g.get(metrique)
            if val is not None:
                gps_rows.append({
                    "Joueur": nom,
                    "Séance": ev.get("title", "Séance"),
                    "Date": (ev.get("start_time") or "")[:10],
                    "Métrique": metrique,
                    "Valeur": val
                })
    df_gps = pd.DataFrame(gps_rows) if gps_rows else pd.DataFrame()
    if not df_gps.empty:
        df_gps = df_gps[df_gps["Joueur"].isin(scope_joueurs)]

    tab_questions, tab_graph, tab_compare, tab_gps, tab_brut = st.tabs([
        "📝 Réponses par Question",
        "📈 Graphique d'une Question",
        "🆚 Comparaison Joueurs",
        "🛰️ Données GPS",
        "📋 Données Brutes",
    ])

    with tab_questions:
        if not df_flat.empty:
            if len(scope_joueurs) == 1:
                sel_ath_q = scope_joueurs[0]
            else:
                sel_ath_q = st.selectbox("Joueur (parmi la sélection ci-dessus) :", scope_joueurs, key="q_ath_select")

            df_ath = df_flat[df_flat["Joueur"] == sel_ath_q].sort_values("Date", ascending=False)

            if not df_ath.empty:
                liste_questions = sorted(df_ath["Question"].unique().tolist())
                sel_q_filter = st.selectbox("Filtrer une question :", ["-- Toutes les questions --"] + liste_questions, key="q_filter_select")

                st.write("---")
                questions_affichage = liste_questions if sel_q_filter == "-- Toutes les questions --" else [sel_q_filter]

                for question_titre in questions_affichage:
                    st.markdown(f"### ❓ {question_titre}")
                    df_single_q = df_ath[df_ath["Question"] == question_titre]
                    cols = st.columns(min(len(df_single_q), 4) or 1)
                    for idx, (_, row) in enumerate(df_single_q.iterrows()):
                        with cols[idx % 4]:
                            st.metric(label=f"📅 {row['Date_Str']}", value=f"{row['Valeur']}")
                    st.write("---")
            else:
                st.info(f"Aucune donnée enregistrée pour {sel_ath_q}.")
        else:
            st.info("Aucune donnée disponible pour cette sélection.")

    with tab_graph:
        if not df_flat.empty:
            if len(scope_joueurs) == 1:
                sel_ath_g = scope_joueurs[0]
            else:
                sel_ath_g = st.selectbox("Joueur (parmi la sélection ci-dessus) :", scope_joueurs, key="g_ath_select")

            df_g_ath = df_flat[df_flat["Joueur"] == sel_ath_g].sort_values("Date")

            if not df_g_ath.empty:
                questions_num = df_g_ath[df_g_ath["Valeur"].apply(lambda x: isinstance(x, (int, float)))]
                unique_q_num = sorted(questions_num["Question"].unique().tolist())

                sel_q_graph = st.selectbox("Choisir la question à analyser :", unique_q_num if unique_q_num else ["Aucune question numérique"])

                if sel_q_graph and sel_q_graph in unique_q_num:
                    df_target = df_g_ath[df_g_ath["Question"] == sel_q_graph]
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_target["Date"], y=df_target["Valeur"], mode="lines+markers",
                        name=sel_q_graph, line=dict(width=3), marker=dict(size=10)
                    ))
                    fig.update_layout(
                        title=f"Évolution : {sel_q_graph} — {sel_ath_g}", template="plotly_dark",
                        hovermode="x unified", xaxis_title="Date", yaxis_title="Valeur / Score"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Cette question ne contient pas de valeurs numériques exploitables en graphique.")
            else:
                st.info("Pas de données pour cet athlète.")
        else:
            st.info("Aucune donnée disponible pour cette sélection.")

    with tab_compare:
        st.caption("Comparez les variables entre plusieurs joueurs et plusieurs séances en un coup d'œil.")
        if not df_flat.empty:
            df_num = df_flat[df_flat["Valeur"].apply(lambda x: isinstance(x, (int, float)))].copy()
            if not df_num.empty:
                questions_dispo = sorted(df_num["Question"].unique().tolist())
                sel_q_cmp = st.selectbox("Variable à comparer :", questions_dispo, key="cmp_q_select")
                df_q = df_num[df_num["Question"] == sel_q_cmp]

                joueurs_dispo = sorted(df_q["Joueur"].unique().tolist())
                defaut_cmp = [j for j in scope_joueurs if j in joueurs_dispo] or joueurs_dispo[:6]
                sel_joueurs_cmp = st.multiselect("Joueurs à comparer :", joueurs_dispo, default=defaut_cmp, key="cmp_joueurs_select")

                if sel_joueurs_cmp:
                    df_sel = df_q[df_q["Joueur"].isin(sel_joueurs_cmp)]

                    st.markdown("##### 📈 Évolution comparée dans le temps")
                    fig_cmp = px.line(
                        df_sel.sort_values("Date"), x="Date", y="Valeur", color="Joueur",
                        markers=True, template="plotly_dark", title=f"{sel_q_cmp} — comparaison entre joueurs"
                    )
                    st.plotly_chart(fig_cmp, use_container_width=True)

                    st.markdown("##### 🌡️ Carte de chaleur (Joueur × Date)")
                    pivot = df_sel.pivot_table(index="Joueur", columns="Date_Str", values="Valeur", aggfunc="mean")
                    if not pivot.empty:
                        fig_heat = px.imshow(
                            pivot, aspect="auto", color_continuous_scale="RdYlGn_r",
                            labels=dict(x="Date", y="Joueur", color=sel_q_cmp), template="plotly_dark"
                        )
                        st.plotly_chart(fig_heat, use_container_width=True)

                    st.markdown("##### 📊 Moyenne par joueur")
                    moyennes = df_sel.groupby("Joueur")["Valeur"].mean().sort_values(ascending=False).reset_index()
                    fig_bar = px.bar(
                        moyennes, x="Joueur", y="Valeur", template="plotly_dark",
                        title=f"Moyenne de « {sel_q_cmp} » par joueur", text_auto=".2f"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Sélectionnez au moins un joueur.")
            else:
                st.info("Aucune variable numérique à comparer.")
        else:
            st.info("Aucune donnée disponible.")

    with tab_gps:
        st.caption("Distance totale, haute intensité, sprints, accélérations, décélérations, Vmax — importés depuis vos fichiers GPS.")
        if not df_gps.empty:
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                metriques_dispo = sorted(df_gps["Métrique"].unique().tolist())
                sel_metrique = st.selectbox(
                    "Métrique GPS :", metriques_dispo,
                    format_func=lambda m: NOMS_METRIQUES_GPS.get(m, m), key="gps_metrique_select"
                )
            df_m = df_gps[df_gps["Métrique"] == sel_metrique]

            with c_g2:
                joueurs_gps = sorted(df_m["Joueur"].unique().tolist())
                sel_joueurs_gps = st.multiselect("Joueurs :", joueurs_gps, default=joueurs_gps, key="gps_joueurs_select")

            df_m_sel = df_m[df_m["Joueur"].isin(sel_joueurs_gps)] if sel_joueurs_gps else df_m

            st.markdown(f"##### 📊 {NOMS_METRIQUES_GPS.get(sel_metrique, sel_metrique)} — comparaison par joueur et par séance")
            if not df_m_sel.empty:
                fig_gps_bar = px.bar(
                    df_m_sel, x="Séance", y="Valeur", color="Joueur", barmode="group",
                    template="plotly_dark", title=NOMS_METRIQUES_GPS.get(sel_metrique, sel_metrique)
                )
                st.plotly_chart(fig_gps_bar, use_container_width=True)

                st.markdown("##### 📈 Évolution moyenne par séance (équipe)")
                moy_par_seance = df_m_sel.groupby(["Séance", "Date"])["Valeur"].mean().reset_index().sort_values("Date")
                fig_gps_line = px.line(
                    moy_par_seance, x="Séance", y="Valeur", markers=True,
                    template="plotly_dark", title="Moyenne équipe"
                )
                st.plotly_chart(fig_gps_line, use_container_width=True)
            else:
                st.info("Aucune donnée pour cette sélection.")
        else:
            st.info("Aucun rapport GPS importé pour le moment. Rendez-vous dans '📁 Fichiers & Rapports GPS' pour en importer un.")

    with tab_brut:
        if not df_flat.empty:
            st.markdown("**Réponses aux questionnaires**")
            st.dataframe(df_flat, use_container_width=True)
        if not df_gps.empty:
            st.markdown("**Données GPS**")
            st.dataframe(df_gps, use_container_width=True)

# =====================================================================
# PAGE : GESTION PROFILS, ÉQUIPES, TESTS & COMPTES
# =====================================================================
elif menu == "⚙️ Gestion Profils, Équipes & Comptes":
    st.header("⚙️ Gestion des Profils, Équipes & Comptes")
    tab_ath, tab_teams, tab_comptes = st.tabs(["👤 Athlètes & Tests Physiques", "🛡️ Équipes", "🔑 Comptes de connexion"])

    with tab_ath:
        teams_data = supabase.table("teams").select("*").execute().data or []
        dict_teams_add = {t["name"]: t["id"] for t in teams_data}

        st.info(
            "👉 Pour **créer** un nouvel athlète, rends-toi dans l'onglet **🔑 Comptes de connexion** : "
            "cela crée en une seule fois son compte de connexion (indispensable pour se connecter) et son profil. "
            "Cet onglet-ci sert à modifier un profil existant, gérer ses tests physiques, ou le supprimer."
        )

        st.markdown("---")
        st.subheader("✏️ Modifier / Supprimer un athlète existant")

        ath_data = supabase.table("profiles").select("*").eq("role", "athlete").execute().data or []
        dict_ath_lookup = {a.get("full_name", f"Athlète {a['id']}"): a for a in ath_data}

        if dict_ath_lookup:
            selected_ath_name = st.selectbox("Sélectionner un athlète :", list(dict_ath_lookup.keys()))
            selected_ath = dict_ath_lookup[selected_ath_name]
            ath_id = selected_ath["id"]

            c_mod1, c_mod2 = st.columns(2)
            with c_mod1:
                upd_name = st.text_input("Nom & Prénom", value=selected_ath.get("full_name", ""), key=f"ath_name_{ath_id}")
            with c_mod2:
                current_team_id = selected_ath.get("team_id")
                current_team_name = "Aucune"
                for tname, tid in dict_teams_add.items():
                    if tid == current_team_id:
                        current_team_name = tname
                team_idx = (["Aucune"] + list(dict_teams_add.keys())).index(current_team_name) if current_team_name in dict_teams_add else 0
                upd_team = st.selectbox("Changer d'équipe", ["Aucune"] + list(dict_teams_add.keys()), index=team_idx, key=f"ath_team_select_{ath_id}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Mettre à jour le profil", key=f"upd_p_{ath_id}"):
                    new_t_id = dict_teams_add[upd_team] if upd_team != "Aucune" else None
                    supabase.table("profiles").update({"full_name": upd_name, "team_id": new_t_id}).eq("id", ath_id).execute()
                    st.success("Profil mis à jour !")
                    st.rerun()
            with c2:
                if st.button("❌ Supprimer définitivement l'athlète (profil + compte)", type="primary", key=f"del_p_{ath_id}"):
                    ok, msg = supprimer_compte(ath_id)
                    if ok:
                        st.success("Athlète et son compte de connexion supprimés !")
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")
            st.subheader(f"🏃 Tests Physiques de {upd_name}")

            tests_db = supabase.table("physical_tests").select("*").eq("athlete_id", ath_id).order("created_at", desc=True).execute().data or []

            if tests_db:
                st.write("**Tests enregistrés (Modifiables / Supprimables) :**")
                for t in tests_db:
                    t_id = t["id"]
                    col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns([3, 2, 2, 2, 2])
                    with col_t1:
                        new_t_name = st.text_input("Test", value=t.get("test_name", ""), key=f"t_name_{t_id}")
                    with col_t2:
                        new_t_val = st.number_input("Valeur", value=float(t.get("test_value", 0.0)), key=f"t_val_{t_id}")
                    with col_t3:
                        new_t_unit = st.text_input("Unité", value=t.get("unit", ""), key=f"t_unit_{t_id}")
                    with col_t4:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("💾 Modifier", key=f"save_t_{t_id}"):
                            supabase.table("physical_tests").update({"test_name": new_t_name, "test_value": new_t_val, "unit": new_t_unit}).eq("id", t_id).execute()
                            st.success("Test modifié !")
                            st.rerun()
                    with col_t5:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("❌ Supprimer", key=f"del_t_{t_id}"):
                            supabase.table("physical_tests").delete().eq("id", t_id).execute()
                            st.success("Test supprimé !")
                            st.rerun()
            else:
                st.info("Aucun test physique enregistré.")

            st.markdown("#### ➕ Ajouter un nouveau test physique")
            col_add1, col_add2, col_add3 = st.columns(3)
            with col_add1:
                t_name = st.text_input("Nom du test (ex: VMA, 1RM Squat)", key=f"add_tn_{ath_id}")
            with col_add2:
                t_val = st.number_input("Résultat", value=0.0, key=f"add_tv_{ath_id}")
            with col_add3:
                t_unit = st.text_input("Unité", value="km/h", key=f"add_tu_{ath_id}")

            if st.button("🚀 Enregistrer le test", key=f"btn_add_t_{ath_id}", type="primary"):
                if t_name:
                    supabase.table("physical_tests").insert({"athlete_id": ath_id, "test_name": t_name, "test_value": t_val, "unit": t_unit}).execute()
                    st.success("Test enregistré !")
                    st.rerun()
        else:
            st.info("Aucun athlète disponible dans la base.")

    with tab_teams:
        st.subheader("➕ Créer une nouvelle équipe")
        col_t_new1, col_t_new2 = st.columns([4, 2])
        with col_t_new1:
            new_t = st.text_input("Nom de la nouvelle équipe", key="input_create_team")
        with col_t_new2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Créer l'équipe", type="primary", use_container_width=True):
                if new_t:
                    supabase.table("teams").insert({"name": new_t}).execute()
                    st.success("Équipe créée !")
                    st.rerun()

        st.markdown("---")
        st.subheader("⚙️ Gérer, Modifier ou Supprimer une Équipe")

        teams_list = supabase.table("teams").select("*").execute().data or []
        if teams_list:
            dict_teams_mgt = {t["name"]: t for t in teams_list}
            selected_team_mgt_name = st.selectbox("Sélectionnez l'équipe à gérer :", list(dict_teams_mgt.keys()))
            selected_team = dict_teams_mgt[selected_team_mgt_name]
            team_id = selected_team["id"]

            col_eq1, col_eq2, col_eq3 = st.columns([3, 2, 2])
            with col_eq1:
                renamed_team_name = st.text_input("Nom de l'équipe", value=selected_team["name"], key=f"rename_t_{team_id}")
            with col_eq2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Renommer", key=f"btn_ren_{team_id}"):
                    supabase.table("teams").update({"name": renamed_team_name}).eq("id", team_id).execute()
                    st.success("Équipe renommée !")
                    st.rerun()
            with col_eq3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("❌ Supprimer l'équipe", type="primary", key=f"btn_del_team_{team_id}"):
                    supabase.table("teams").delete().eq("id", team_id).execute()
                    st.success("Équipe supprimée !")
                    st.rerun()

            st.markdown("#### 👥 Joueurs dans cette équipe")
            members = supabase.table("profiles").select("*").eq("team_id", team_id).execute().data or []
            if members:
                for m in members:
                    c_m1, c_m2 = st.columns([4, 2])
                    with c_m1:
                        st.write(f"• **{m.get('full_name', 'Athlète')}**")
                    with c_m2:
                        if st.button("Retirer de l'équipe", key=f"remove_mem_{m['id']}"):
                            supabase.table("profiles").update({"team_id": None}).eq("id", m["id"]).execute()
                            st.success(f"Retiré de l'équipe !")
                            st.rerun()
            else:
                st.info("Aucun joueur actuellement assigné à cette équipe.")

            st.markdown("##### ➕ Ajouter un athlète existant à l'équipe")
            free_athletes = supabase.table("profiles").select("*").eq("role", "athlete").is_("team_id", None).execute().data or []
            if free_athletes:
                dict_free = {fa.get("full_name", f"Athlète {fa['id']}"): fa["id"] for fa in free_athletes}
                c_add_m1, c_add_m2 = st.columns([3, 2])
                with c_add_m1:
                    ath_to_add = st.selectbox("Athlètes sans équipe :", list(dict_free.keys()))
                with c_add_m2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Ajouter à l'équipe", key=f"add_mem_btn_{team_id}"):
                        supabase.table("profiles").update({"team_id": team_id}).eq("id", dict_free[ath_to_add]).execute()
                        st.success("Joueur ajouté à l'équipe !")
                        st.rerun()
            else:
                st.caption("Tous les athlètes enregistrés sont déjà affectés à une équipe.")

    with tab_comptes:
        st.subheader("🔑 Créer un compte de connexion (logiciel + application)")
        st.caption("Un compte est indispensable pour qu'un coach ou un athlète puisse se connecter.")

        teams_data = supabase.table("teams").select("*").execute().data or []
        dict_teams_cpt = {t["name"]: t["id"] for t in teams_data}
        tous_profils = supabase.table("profiles").select("id, full_name, role").execute().data or []
        profils_sans_compte = [p for p in tous_profils]  # info affichée, pas de distinction stricte possible sans lister auth.users

        with st.form("form_creer_compte"):
            c1, c2 = st.columns(2)
            with c1:
                new_email = st.text_input("E-mail de connexion")
                new_password = st.text_input("Mot de passe", type="password")
                new_role = st.selectbox("Rôle", ["athlete", "coach"], format_func=lambda r: "🏃 Athlète" if r == "athlete" else "🏋️ Coach")
            with c2:
                new_full_name = st.text_input("Nom complet")
                new_team = st.selectbox("Équipe (si athlète)", ["Aucune"] + list(dict_teams_cpt.keys()))

            if st.form_submit_button("🚀 Créer le compte", type="primary"):
                if not (new_email and new_password and new_full_name):
                    st.error("E-mail, mot de passe et nom complet sont obligatoires.")
                else:
                    t_id = dict_teams_cpt.get(new_team) if new_role == "athlete" else None
                    ok, msg = creer_compte(new_email, new_password, new_full_name, new_role, t_id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("---")
        st.subheader("✏️ Modifier / Supprimer un compte existant")

        comptes = lister_comptes()
        if comptes:
            dict_comptes = {f"{c.get('full_name', 'Sans nom')} ({'Coach' if c.get('role') == 'coach' else 'Athlète'})": c for c in comptes}
            sel_compte_label = st.selectbox("Sélectionner un compte :", list(dict_comptes.keys()))
            compte_sel = dict_comptes[sel_compte_label]
            compte_id = compte_sel["id"]

            c_e1, c_e2 = st.columns(2)
            with c_e1:
                edit_name = st.text_input("Nom complet", value=compte_sel.get("full_name", ""), key=f"cpt_name_{compte_id}")
                edit_role = st.selectbox(
                    "Rôle", ["athlete", "coach"],
                    index=0 if compte_sel.get("role") != "coach" else 1,
                    format_func=lambda r: "🏃 Athlète" if r == "athlete" else "🏋️ Coach",
                    key=f"cpt_role_{compte_id}"
                )
            with c_e2:
                edit_email = st.text_input("Nouvel e-mail (laisser vide pour ne pas changer)", key=f"cpt_email_{compte_id}")
                edit_password = st.text_input("Nouveau mot de passe (laisser vide pour ne pas changer)", type="password", key=f"cpt_pwd_{compte_id}")

            c_b1, c_b2 = st.columns(2)
            with c_b1:
                if st.button("💾 Mettre à jour ce compte", key=f"upd_cpt_{compte_id}"):
                    ok, msg = modifier_compte(
                        compte_id, full_name=edit_name, role=edit_role,
                        new_password=edit_password or None, new_email=edit_email or None
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with c_b2:
                if compte_id == mon_id:
                    st.caption("⚠️ Vous ne pouvez pas supprimer votre propre compte connecté.")
                else:
                    if st.button("❌ Supprimer définitivement ce compte", type="primary", key=f"del_cpt_{compte_id}"):
                        ok, msg = supprimer_compte(compte_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            st.info("Aucun compte enregistré pour le moment.")

# =====================================================================
# PAGE : GÉNÉRATEUR DE BIPS AUDIO
# =====================================================================
elif menu == "🔊 Générateur de Bips Audio":
    import wave
    import math
    import struct
    import io

    st.header("🔊 Générateur de Bips Audio (Tests VMA & Pacing)")
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
                if i < fade_len:
                    envelope = i / fade_len
                elif i > num_samples - fade_len:
                    envelope = (num_samples - i) / fade_len

                sin_val = math.sin(2 * math.pi * freq * i / sample_rate)

                if "Carrée" in w_type:
                    raw_signal = 1.0 if sin_val >= 0 else -1.0
                else:
                    raw_signal = sin_val

                value = int(32767 * 0.98 * envelope * raw_signal)
                frames.extend(struct.pack('<h', value))
            return frames

        def create_silence(duration_sec):
            num_samples = int(sample_rate * duration_sec)
            return bytearray(struct.pack('<h', 0) * num_samples)

        current_interval = float(base_interval)
        elapsed_time = 0.0

        for b in range(1, total_beps + 1):
            is_accel_step = False
            if interval_mode == "Progressif / Accéléré" and b > 1:
                if accel_trigger == "Tous les X bips" and (b - 1) % int(accel_value) == 0:
                    is_accel_step = True
                elif accel_trigger == "Toutes les X secondes" and elapsed_time >= accel_value:
                    is_accel_step = True
                    elapsed_time = 0.0

                if is_accel_step:
                    current_interval = max(float(min_interval), current_interval - float(step_decrement))

            if is_accel_step:
                beep_wave = (
                    create_wave(2400, bip_duration * 0.6, wave_type)
                    + create_silence(0.04)
                    + create_wave(2400, bip_duration, wave_type)
                )
                used_bip_dur = (bip_duration * 1.6) + 0.04
            else:
                beep_wave = create_wave(bip_freq, bip_duration, wave_type)
                used_bip_dur = bip_duration

            silence_duration = max(0.0, current_interval - used_bip_dur)
            silence_wave = create_silence(silence_duration)

            audio_frames.extend(beep_wave)
            audio_frames.extend(silence_wave)

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
        mode = st.radio("Type de test :", ["Constant (Intervalle fixe)", "Progressif / Accéléré"], key="audio_mode")
        base_int = st.number_input("Intervalle de départ entre chaque bip (secondes) :", min_value=0.5, max_value=120.0, value=5.0, step=0.5)
        total_beps = st.number_input("Nombre total de bips à générer :", min_value=2, max_value=500, value=30, step=1)

    with col_cfg2:
        st.subheader("🔊 Timbre & Puissance du Bip")
        wave_type = st.selectbox(
            "Type de son :",
            ["Carrée (Buzzer Puissant / VMEVAL)", "Sinusoïdale (Bip classique)"],
            help="L'onde carrée produit un son très fort, agressif et strident, idéal pour être diffusé sur enceinte en extérieur."
        )
        bip_duration = st.slider("Durée du bip sonore (secondes) :", min_value=0.05, max_value=2.0, value=0.25, step=0.05)
        bip_freq = st.slider("Hauteur du son / Fréquence (Hz) :", min_value=600, max_value=3500, value=2000, step=100, help="2000 Hz est la fréquence la plus perçante pour l'oreille humaine à grande distance.")

    st.markdown("---")

    if mode == "Progressif / Accéléré":
        st.subheader("🚀 Paramètres d'accélération")
        ca1, ca2, ca3, ca4 = st.columns(4)
        with ca1:
            accel_trigger = st.selectbox("Déclencher l'accélération :", ["Tous les X bips", "Toutes les X secondes"])
        with ca2:
            if accel_trigger == "Tous les X bips":
                accel_val = st.number_input("Tous les N bips :", min_value=1, max_value=50, value=5)
            else:
                accel_val = st.number_input("Toutes les N secondes :", min_value=5.0, max_value=600.0, value=60.0, step=5.0)
        with ca3:
            step_decrement = st.number_input("Réduction de l'intervalle (sec) :", min_value=0.1, max_value=10.0, value=0.5, step=0.1)
        with ca4:
            min_int = st.number_input("Intervalle minimum limite (sec) :", min_value=0.2, max_value=30.0, value=1.0, step=0.1)
    else:
        accel_trigger = "Tous les X bips"
        accel_val = 1
        step_decrement = 0.0
        min_int = base_int

    st.markdown("---")

    if st.button("🎵 Générer la bande sonore", type="primary", use_container_width=True):
        with st.spinner("Génération du son haute intensité en cours..."):
            audio_data = generate_beep_audio(
                interval_mode=mode,
                base_interval=base_int,
                min_interval=min_int,
                total_beps=total_beps,
                accel_trigger=accel_trigger,
                accel_value=accel_val,
                step_decrement=step_decrement,
                bip_freq=bip_freq,
                bip_duration=bip_duration,
                wave_type=wave_type
            )

            st.success("✅ Fichier sonore haute intensité généré !")
            st.audio(audio_data, format="audio/wav")
            st.download_button(
                label="💾 Télécharger le fichier audio (.WAV)",
                data=audio_data,
                file_name=f"test_bips_vmeval_{mode.split()[0].lower()}.wav",
                mime="audio/wav",
                use_container_width=True
            )
