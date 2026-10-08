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
# CONFIGURATION ET STYLE (Suppression des boutons du haut + Sidebar abaissée)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Performance",
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

    /* Masquer les liens GitHub, share, edit, etc. en haut à droite mais garder le menu 3 points */
    #MainMenu {visibility: visible;}
    footer {visibility: hidden;}
    header {visibility: visible;}
    .stDeployButton {display:none;}
    div[data-testid="stDecoration"] {display: none;}
    
    /* Abaisser le bouton d'ouverture de la barre latérale sur mobile pour éviter les conflits */
    [data-testid="collapsedControl"] {
        top: 3.5rem !important;
        left: 1rem !important;
        z-index: 999999;
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
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border-soft); }
    hr { border-color: var(--border-soft) !important; }

    .badge-dispo { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.4); padding: 3px 12px; border-radius: 999px; font-size: 0.85em; font-weight: 600; }
    .badge-blesse { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.4); padding: 3px 12px; border-radius: 999px; font-size: 0.85em; font-weight: 600; }

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
# AUTHENTIFICATION
# =====================================================================
if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

def ecran_connexion():
    st.markdown("""
    <div style="text-align:center; padding: 40px 0 10px 0;">
        <div class="brand-kicker" style="font-size:2.4em;">⚡ PERFORMANCE</div>
        <div class="brand-tagline" style="font-size:1em;">Plateforme de suivi de performance</div>
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
                st.success(f"Bienvenue {profile.get('full_name', '')} !")
                st.rerun()

if not st.session_state.user_profile:
    ecran_connexion()
    st.stop()

profil_connecte = st.session_state.user_profile
role_connecte = profil_connecte.get("role", "athlete")
mon_id = profil_connecte.get("id")

# -------------------------------------------------------------------
# BARRE LATÉRALE
# -------------------------------------------------------------------
st.sidebar.markdown("""
<div class="brand-kicker">⚡ PERFORMANCE</div>
<div class="brand-tagline">Suivi & Performance</div>
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
    <span style="font-family:'Sora',sans-serif; font-weight:800; font-size:2.1em;">⚡ Performance</span>
    <span style="color:var(--text-dim); font-size:1em;">Suivi global</span>
</div>
""", unsafe_allow_html=True)

if role_connecte == "coach":
    menu_options = [
        "📅 Planning & Séances",
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

if "local_tests_store" not in st.session_state:
    st.session_state.local_tests_store = {}

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
# PAGE : PLANNING & SÉANCES (avec choix de vue : personnel, équipe, joueur)
# =====================================================================
if menu == "📅 Planning & Séances":
    st.header("📅 Planning & Séances")

    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute()
    athletes_list = res_athletes.data if res_athletes.data else []
    dict_athletes = {a.get("full_name", f"Athlète {a['id']}"): a["id"] for a in athletes_list if a.get("full_name")}

    teams_data = supabase.table("teams").select("*").execute().data or []
    dict_teams = {t["name"]: t["id"] for t in teams_data}

    # Sélection du filtre de planning pour le coach (par défaut sur son planning global)
    st.markdown("#### 👁️ Vue du Planning")
    vue_planning = st.selectbox(
        "Afficher le planning de :",
        ["Mon planning (Toutes mes séances)", "Planning d'une équipe", "Planning d'un joueur"]
    )
    
    filtre_id_cible = None
    if vue_planning == "Planning d'une équipe" and dict_teams:
        eq_choisie = st.selectbox("Choisir l'équipe :", list(dict_teams.keys()))
        eq_id = dict_teams[eq_choisie]
        mems = supabase.table("profiles").select("id").eq("team_id", eq_id).execute().data or []
        ids_equipe = [m["id"] for m in mems]
        # On filtrera par ces IDs
    elif vue_planning == "Planning d'un joueur" and dict_athletes:
        ath_choisi = st.selectbox("Choisir le joueur :", sorted(dict_athletes.keys()))
        filtre_id_cible = dict_athletes[ath_choisi]

    statuts = get_statuts_disponibilite()
    ids_blesses = {aid for aid, s in statuts.items() if s["statut"] == "blesse"}
    n_blesses = len(ids_blesses)
    n_dispo = len(dict_athletes) - n_blesses

    with st.expander("🩹 Voir l'état de disponibilité de l'effectif", expanded=False):
        if dict_athletes:
            for nom, aid in sorted(dict_athletes.items()):
                s = statuts.get(aid, {"statut": "disponible", "depuis": None})
                if s["statut"] == "blesse":
                    st.markdown(f"🚑 **{nom}** — <span class='badge-blesse'>En réathlétisation</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"🟢 **{nom}** — <span class='badge-dispo'>Disponible</span>", unsafe_allow_html=True)

    st.markdown("---")
    tab_nouvelle, tab_existantes = st.tabs(["🆕 Planifier une séance", "📋 Séances planifiées"])

    with tab_nouvelle:
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
            exclure_blesses = st.checkbox("🚑 Exclure les joueurs blessés de '-- Tous les athlètes --'", value=True)
            location = st.text_input("Lieu")
            
            # Option questionnaire RPE automatique par défaut
            creer_rpe_auto = st.checkbox("🤖 Créer automatiquement un questionnaire RPE (1-10) pour cette séance", value=True)

        with col_b:
            event_date = st.date_input("Date de la séance", datetime.now())
            start_time = st.time_input("Heure de début", datetime.strptime("10:00", "%H:%M").time())
            end_time = st.time_input("Heure de fin", datetime.strptime("11:30", "%H:%M").time())
            rpe_cible = st.number_input("🎯 RPE cible estimé (Optionnel)", min_value=1.0, max_value=10.0, value=7.0, step=0.5)

        if st.button("🚀 Planifier la séance", type="primary"):
            if not title:
                st.error("Veuillez saisir un titre.")
            else:
                if athlete_sel_label == "-- Tous les athlètes --":
                    target_ids = [aid for nom, aid in dict_athletes.items() if not (exclure_blesses and aid in ids_blesses)]
                else:
                    target_ids = [dict_athletes[labels_affiches[athlete_sel_label]]]

                dt_start = datetime.combine(event_date, start_time)
                dt_end = datetime.combine(event_date, end_time)

                events_to_insert = []
                for a_id in target_ids:
                    events_to_insert.append({
                        "title": title,
                        "event_type": event_type,
                        "start_time": dt_start.isoformat(),
                        "end_time": dt_end.isoformat(),
                        "location": location or "Non spécifié",
                        "athlete_id": a_id,
                        "target_rpe": rpe_cible
                    })

                if events_to_insert:
                    try:
                        res_ins = supabase.table("events").insert(events_to_insert).execute()
                        st.success(f"✅ Séance planifiée pour {len(target_ids)} joueur(s) !")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erreur Supabase : {ex}")

    with tab_existantes:
        tous_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []
        
        # Filtrage selon la vue choisie
        if vue_planning == "Planning d'un joueur" and filtre_id_cible:
            tous_events = [e for e in tous_events if e.get("athlete_id") == filtre_id_cible]
        elif vue_planning == "Planning d'une équipe" and 'ids_equipe' in locals():
            tous_events = [e for e in tous_events if e.get("athlete_id") in ids_equipe]

        if not tous_events:
            st.info("Aucune séance trouvée pour cette vue.")
        else:
            dict_athletes_inv = {v: k for k, v in dict_athletes.items()}
            for ev in tous_events[:20]:
                nom_ath = dict_athletes_inv.get(ev.get("athlete_id"), "Athlète")
                d_str = (ev.get("start_time") or "")[:16].replace("T", " ")
                with st.expander(f"📌 {ev.get('title')} ({d_str}) — {nom_ath}"):
                    st.write(f"**Lieu :** {ev.get('location', 'N/A')} | **Type :** {ev.get('event_type')}")
                    if st.button("❌ Supprimer cette séance", key=f"del_ev_q_{ev['id']}"):
                        supabase.table("events").delete().eq("id", ev["id"]).execute()
                        st.success("Séance supprimée.")
                        st.rerun()

# =====================================================================
# PAGE : FICHIERS & RAPPORTS GPS
# =====================================================================
elif menu == "📁 Fichiers & Rapports GPS":
    st.header("📁 Fichiers de Séances & Rapports GPS")

    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
    dict_athletes = {a.get("full_name"): a["id"] for a in res_athletes if a.get("full_name")}
    res_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []

    dict_events = {}
    for ev in res_events:
        ev_id = ev["id"]
        ev_title = ev.get("title") or "Séance"
        date_str = (ev.get("start_time") or "")[:16].replace("T", " ")
        dict_events[f"{ev_title} ({date_str})"] = ev

    tab_upload, tab_gps = st.tabs(["📤 Joindre un PDF", "🛰️ Importer un rapport GPS (xlsx/csv)"])

    with tab_upload:
        if dict_events:
            selected_event_label = st.selectbox("Séance concernée :", list(dict_events.keys()))
            selected_event = dict_events[selected_event_label]
            session_title = st.text_input("Titre du document :", value=selected_event.get("title", ""))
            uploaded_file = st.file_uploader("Fichier PDF ou Image", type=["pdf", "png", "jpg"])

            if st.button("Publier le document", type="primary"):
                if uploaded_file:
                    file_bytes = uploaded_file.read()
                    mime_type = uploaded_file.type or "application/octet-stream"
                    storage_path = f"{int(datetime.now().timestamp())}_{uploaded_file.name}"
                    try:
                        file_url = upload_file_direct_http("session-files", storage_path, file_bytes, mime_type)
                    except Exception:
                        file_url = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode('utf-8')}"
                    
                    supabase.table("session_files").insert({
                        "title": session_title,
                        "file_name": uploaded_file.name,
                        "file_url": file_url,
                        "event_id": selected_event.get("id"),
                        "athlete_id": selected_event.get("athlete_id")
                    }).execute()
                    st.success("Document publié avec succès !")
                    st.rerun()

    with tab_gps:
        st.subheader("🛰️ Import de rapport GPS")
        if dict_events:
            gps_event_label = st.selectbox("Séance GPS :", list(dict_events.keys()), key="gps_ev_sel")
            gps_file = st.file_uploader("Fichier GPS (.csv, .xlsx)", type=["csv", "xlsx", "xls"])

            if gps_file:
                try:
                    lignes = lire_fichier_gps(gps_file.read(), nom_fichier=gps_file.name)
                except Exception as ex:
                    lignes = []
                    st.error(fErreur de lecture du GPS : {ex})

                if lignes:
                    st.dataframe(pd.DataFrame(lignes), use_container_width=True)
                    if st.button("💾 Importer dans la base", type="primary"):
                        selected_event = dict_events[gps_event_label]
                        n_ins, non_trouves = enregistrer_rapport_gps(selected_event["id"], lignes, dict_athletes)
                        st.success(f"✅ {n_ins} lignes GPS importées avec succès !")
                        if non_trouves:
                            st.warning(f"Joueurs non reconnus (vérifiez l'orthographe exacte) : {', '.join(non_trouves)}")

# =====================================================================
# PAGE : QUESTIONNAIRES & ALERTES COACH
# =====================================================================
elif menu == "📝 Questionnaires":
    st.header("📝 Questionnaires & Alertes")
    
    # Affichage des alertes en haut de page pour le coach
    st.subheader("🚨 Alertes & Vigilance effectif")
    st.info("Les alertes s'affichent ici si un athlète signale une douleur musculaire (wellness) ou si les valeurs d'effort s'écartent des objectifs.")

    tab_creer, tab_envoyer = st.tabs(["🆕 Créer un questionnaire", "📩 Assigner"])
    with tab_creer:
        q_title = st.text_input("Titre du questionnaire")
        q_type = st.selectbox("Type", ["Pre-Event (Wellness)", "Post-Event (RPE)"])
        if st.button("Créer"):
            if q_title:
                supabase.table("questionnaires").insert({"title": q_title, "type": "pre_event" if "Pre" in q_type else "post_event", "questions": []}).execute()
                st.success("Questionnaire créé !")
                st.rerun()
    with tab_envoyer:
        st.write("Assignez vos questionnaires aux athlètes ou séances.")

# =====================================================================
# PAGE : ANALYTIQUE (Moyenne d'équipe & 4 onglets épurés)
# =====================================================================
elif menu == "📊 Analytique":
    st.header("📊 Analytique — Performance & GPS")

    profiles = supabase.table("profiles").select("*").execute().data or []
    dict_profiles = {p["id"]: p.get("full_name", "Inconnu") for p in profiles}
    dict_athletes = {p.get("full_name"): p["id"] for p in profiles if p.get("role") == "athlete"}
    teams_all = supabase.table("teams").select("*").execute().data or []
    dict_teams_an = {t["name"]: t["id"] for t in teams_all}

    if not dict_athletes:
        st.info("Aucun athlète enregistré.")
        st.stop()

    mode_analyse = st.radio("Analyser :", ["👤 Un joueur", "👥 Une équipe entière"], horizontal=True)

    scope_joueurs = []
    is_team_mode = False
    if mode_analyse == "👤 Un joueur":
        j = st.selectbox("Choisir le joueur :", sorted(dict_athletes.keys()))
        scope_joueurs = [j] if j else []
    else:
        eq = st.selectbox("Choisir l'équipe :", sorted(dict_teams_an.keys()))
        t_id = dict_teams_an[eq]
        scope_joueurs = [p.get("full_name") for p in profiles if p.get("team_id") == t_id and p.get("full_name")]
        is_team_mode = True

    if not scope_joueurs:
        st.warning("Aucun joueur dans cette sélection.")
        st.stop()

    res_resp = supabase.table("questionnaire_responses").select("*").execute().data or []
    records_flat = []
    for r in res_resp:
        u_id = r.get("athlete_id") or r.get("user_id")
        j_nom = dict_profiles.get(u_id, "Inconnu")
        date_str = str(r.get("submitted_at", r.get("created_at", "")))[:10]
        
        if r.get("rpe_score") is not None:
            records_flat.append({"Joueur": j_nom, "Date": date_str, "Question": "RPE", "Valeur": float(r.get("rpe_score"))})
        
        ans = r.get("answers", {})
        if isinstance(ans, str):
            try: ans = json.loads(ans)
            except: ans = {}
        if isinstance(ans, dict):
            for k, v in ans.items():
                try: val = float(v)
                except: val = str(v)
                records_flat.append({"Joueur": j_nom, "Date": date_str, "Question": str(k).strip(), "Valeur": val})

    df_flat = pd.DataFrame(records_flat) if records_flat else pd.DataFrame()
    if not df_flat.empty:
        df_flat = df_flat[df_flat["Joueur"].isin(scope_joueurs)]

    # 4 onglets demandés
    tab_graph, tab_comp, tab_gps, tab_brut = st.tabs([
        "Graphique",
        "Comparaison joueur",
        "Données GPS",
        "Données brutes"
    ])

    with tab_graph:
        st.subheader("📈 Graphiques & Moyennes")
        if is_team_mode:
            st.info("💡 Affichage de la **moyenne globale de l'équipe** pour les métriques sélectionnées.")
        if not df_flat.empty:
            q_num = df_flat[df_flat["Valeur"].apply(lambda x: isinstance(x, (int, float)))]
            if not q_num.empty:
                q_sel = st.selectbox("Métrique / Question :", sorted(q_num["Question"].unique().tolist()))
                df_q = q_num[q_num["Question"] == q_sel]
                if is_team_mode:
                    df_agg = df_q.groupby("Date")["Valeur"].mean().reset_index()
                    fig = px.line(df_agg, x="Date", y="Valeur", markers=True, title=f"Moyenne Équipe — {q_sel}", template="plotly_dark")
                else:
                    fig = px.line(df_q, x="Date", y="Valeur", color="Joueur", markers=True, title=q_sel, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas assez de données pour afficher les graphiques.")

    with tab_comp:
        st.subheader("🆚 Comparaison joueur")
        if not df_flat.empty:
            q_num = df_flat[df_flat["Valeur"].apply(lambda x: isinstance(x, (int, float)))]
            if not q_num.empty:
                q_cmp = st.selectbox("Indicateur à comparer :", sorted(q_num["Question"].unique().tolist()), key="cmp_q")
                df_c = q_num[q_num["Question"] == q_cmp]
                fig_bar = px.bar(df_c.groupby("Joueur")["Valeur"].mean().reset_index(), x="Joueur", y="Valeur", template="plotly_dark", title=f"Comparaison moyenne : {q_cmp}")
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab_gps:
        st.subheader("🛰️ Données GPS")
        gps_all = obtenir_rapports_gps()
        gps_rows = []
        for g in gps_all:
            nom = dict_profiles.get(g.get("athlete_id"), "Inconnu")
            ev = g.get("events") or {}
            for m in COLONNES_GPS_NUMERIQUES:
                val = g.get(m)
                if val is not None:
                    gps_rows.append({"Joueur": nom, "Séance": ev.get("title", "Séance"), "Métrique": m, "Valeur": val})
        df_gps = pd.DataFrame(gps_rows) if gps_rows else pd.DataFrame()
        if not df_gps.empty:
            df_gps = df_gps[df_gps["Joueur"].isin(scope_joueurs)]
            metrique_gps = st.selectbox("Métrique GPS :", sorted(df_gps["Métrique"].unique().tolist()), format_func=lambda x: NOMS_METRIQUES_GPS.get(x, x))
            df_mg = df_gps[df_gps["Métrique"] == metrique_gps]
            if is_team_mode:
                fig_gps = px.bar(df_mg.groupby("Séance")["Valeur"].mean().reset_index(), x="Séance", y="Valeur", template="plotly_dark", title=f"Moyenne Équipe — {NOMS_METRIQUES_GPS.get(metrique_gps, metrique_gps)}")
            else:
                fig_gps = px.bar(df_mg, x="Séance", y="Valeur", color="Joueur", barmode="group", template="plotly_dark")
            st.plotly_chart(fig_gps, use_container_width=True)
        else:
            st.info("Aucun rapport GPS disponible.")

    with tab_brut:
        st.subheader("📋 Données brutes")
        if not df_flat.empty:
            st.dataframe(df_flat, use_container_width=True)

# =====================================================================
# PAGE : GESTION DES PROFILS (Titre raccourci)
# =====================================================================
elif menu == "⚙️ Gestion des profils":
    st.header("⚙️ Gestion des Profils, Équipes & Comptes")
    tab_ath, tab_teams, tab_comptes = st.tabs(["👤 Athlètes", "🛡️ Équipes", "🔑 Comptes"])

    with tab_ath:
        st.subheader("Modifier ou supprimer un athlète")
        ath_data = supabase.table("profiles").select("*").eq("role", "athlete").execute().data or []
        if ath_data:
            dict_ath = {a["full_name"]: a for a in ath_data if a.get("full_name")}
            sel = st.selectbox("Athlète :", list(dict_ath.keys()))
            ath = dict_ath[sel]
            new_name = st.text_input("Nom", value=ath.get("full_name", ""))
            if st.button("Mettre à jour"):
                supabase.table("profiles").update({"full_name": new_name}).eq("id", ath["id"]).execute()
                st.success("Mis à jour !")
                st.rerun()

    with tab_teams:
        st.subheader("Gestion des équipes")
        new_t = st.text_input("Nom de la nouvelle équipe")
        if st.button("Créer l'équipe"):
            if new_t:
                supabase.table("teams").insert({"name": new_t}).execute()
                st.success("Équipe créée !")
                st.rerun()

    with tab_comptes:
        st.subheader("Créer un compte")
        with st.form("form_cpt"):
            email = st.text_input("E-mail")
            pwd = st.text_input("Mot de passe", type="password")
            nom = st.text_input("Nom complet")
            role = st.selectbox("Rôle", ["athlete", "coach"])
            if st.form_submit_button("Créer"):
                if email and pwd and nom:
                    ok, msg = creer_compte(email, pwd, nom, role)
                    if ok: st.success(msg); st.rerun()
                    else: st.error(msg)

# =====================================================================
# PAGE : GÉNÉRATEUR DE BIPS AUDIO
# =====================================================================
elif menu == "🔊 Générateur de Bips Audio":
    st.header("🔊 Générateur de Bips Audio")
    st.info("Utilisez cet outil pour générer vos bandes sonores de test de terrain.")

# =====================================================================
# PAGES ATHLÈTE
# =====================================================================
elif menu == "📅 Séances à venir":
    st.header("📅 Mes séances à venir")
    events_mine = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
    if not events_mine:
        st.info("Aucune séance planifiée.")
    else:
        for ev in events_mine:
            with st.expander(f"🏋️ {ev.get('title')} — {(ev.get('start_time') or '')[:16]}"):
                afficher_fichiers_evenement(ev["id"])

elif menu == "📆 Calendrier":
    st.header("📆 Mon Calendrier")
    st.info("Retrouvez ici l'historique de vos séances.")

elif menu == "📊 Mes données":
    st.header("📊 Mes données personnelles")
    st.info("Vos statistiques personnelles de progression.")
