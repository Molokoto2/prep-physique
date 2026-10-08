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
# CONFIGURATION ET STYLE
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

    #MainMenu {visibility: visible;}
    footer {visibility: hidden;}
    header {visibility: visible;}
    .stDeployButton {display:none;}
    div[data-testid="stDecoration"] {display: none;}
    
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
# PAGE : PLANNING & SÉANCES (Calendrier interactif complet)
# =====================================================================
if menu == "📅 Planning & Séances":
    st.header("📅 Planning & Séances")

    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute()
    athletes_list = res_athletes.data if res_athletes.data else []
    dict_athletes = {a.get("full_name", f"Athlète {a['id']}"): a["id"] for a in athletes_list if a.get("full_name")}

    teams_data = supabase.table("teams").select("*").execute().data or []
    dict_teams = {t["name"]: t["id"] for t in teams_data}

    st.markdown("#### 👁️ Vue du Planning")
    vue_planning = st.selectbox(
        "Afficher le planning de :",
        ["Mon planning (Toutes mes séances)", "Planning d'une équipe", "Planning d'un joueur"]
    )
    
    filtre_ids_equipe = None
    filtre_id_joueur = None
    if vue_planning == "Planning d'une équipe" and dict_teams:
        eq_choisie = st.selectbox("Choisir l'équipe :", list(dict_teams.keys()))
        eq_id = dict_teams[eq_choisie]
        mems = supabase.table("profiles").select("id").eq("team_id", eq_id).execute().data or []
        filtre_ids_equipe = [m["id"] for m in mems]
    elif vue_planning == "Planning d'un joueur" and dict_athletes:
        ath_choisi = st.selectbox("Choisir le joueur :", sorted(dict_athletes.keys()))
        filtre_id_joueur = dict_athletes[ath_choisi]

    statuts = get_statuts_disponibilite()
    ids_blesses = {aid for aid, s in statuts.items() if s["statut"] == "blesse"}

    tab_nouvelle, tab_existantes = st.tabs(["🆕 Planifier une séance", "📅 Calendrier & Séances"])

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
            creer_rpe_auto = st.checkbox("🤖 Créer automatiquement un questionnaire RPE (1-10) par défaut", value=True)

        with col_b:
            event_date = st.date_input("Date de la séance", datetime.now())
            start_time = st.time_input("Heure de début", datetime.strptime("10:00", "%H:%M").time())
            end_time = st.time_input("Heure de fin", datetime.strptime("11:30", "%H:%M").time())
            rpe_cible = st.number_input("🎯 RPE cible estimé", min_value=1.0, max_value=10.0, value=7.0, step=0.5)

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
                        supabase.table("events").insert(events_to_insert).execute()
                        st.success(f"✅ Séance planifiée avec succès !")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erreur Supabase : {ex}")

    with tab_existantes:
        import calendar as _calendar

        tous_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []
        
        if vue_planning == "Planning d'un joueur" and filtre_id_joueur:
            tous_events = [e for e in tous_events if e.get("athlete_id") == filtre_id_joueur]
        elif vue_planning == "Planning d'une équipe" and filtre_ids_equipe is not None:
            tous_events = [e for e in tous_events if e.get("athlete_id") in filtre_ids_equipe]

        dict_athletes_inv = {v: k for k, v in dict_athletes.items()}
        events_par_jour = {}
        for ev in tous_events:
            d = _parser_datetime_event(ev)
            if d:
                events_par_jour.setdefault(d.date(), []).append(ev)

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
                st.session_state.cal_mois_ref = (ref.replace(day=28) + timedelta(days=4)).replace(day=1)
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
                est_auj = date_cell == datetime.now().date()
                style_j = "color:#38bdf8; font-weight:800;" if est_auj else "color:#f1f5f9; font-weight:600;"
                c.markdown(f"<div style='{style_j}'>{jour_num}</div>", unsafe_allow_html=True)

                for ev in events_par_jour.get(date_cell, [])[:4]:
                    nom_ath = dict_athletes_inv.get(ev.get("athlete_id"), "?")
                    emoji = "⚔️" if ev.get("event_type") == "match" else "🏋️"
                    if c.button(f"{emoji} {ev.get('title')[:10]}", key=f"c_ev_{ev['id']}", help=f"{ev.get('title')} - {nom_ath}", use_container_width=True):
                        st.session_state.cal_event_selectionne = ev["id"]
                        st.rerun()

        st.markdown("---")
        ev_id_sel = st.session_state.cal_event_selectionne
        ev_sel = next((e for e in tous_events if e["id"] == ev_id_sel), None) if ev_id_sel else None

        if ev_sel:
            st.subheader(f"✏️ Modifier / Supprimer la séance : {ev_sel.get('title')}")
            dt_s = _parser_datetime_event(ev_sel) or datetime.now()
            dt_e = _parser_datetime_event(ev_sel, "end_time") or dt_s + timedelta(hours=1)

            c_e1, c_e2 = st.columns(2)
            with c_e1:
                new_t = st.text_input("Titre", value=ev_sel.get("title", ""), key=f"edt_t_{ev_sel['id']}")
                new_type = st.selectbox("Type", ["training", "match"], index=0 if ev_sel.get("event_type") != "match" else 1, key=f"edt_ty_{ev_sel['id']}")
                new_loc = st.text_input("Lieu", value=ev_sel.get("location", ""), key=f"edt_l_{ev_sel['id']}")
            with c_e2:
                new_d = st.date_input("Date", value=dt_s.date(), key=f"edt_d_{ev_sel['id']}")
                new_st = st.time_input("Début", value=dt_s.time(), key=f"edt_st_{ev_sel['id']}")
                new_et = st.time_input("Fin", value=dt_e.time(), key=f"edt_et_{ev_sel['id']}")

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("💾 Enregistrer les modifications", type="primary", key=f"sv_ev_{ev_sel['id']}"):
                    supabase.table("events").update({
                        "title": new_t,
                        "event_type": new_type,
                        "location": new_loc,
                        "start_time": datetime.combine(new_d, new_st).isoformat(),
                        "end_time": datetime.combine(new_d, new_et).isoformat()
                    }).eq("id", ev_sel["id"]).execute()
                    st.success("Séance modifiée !")
                    st.rerun()
            with b2:
                if st.button("❌ Supprimer cette séance", type="primary", key=f"rm_ev_{ev_sel['id']}"):
                    supabase.table("events").delete().eq("id", ev_sel["id"]).execute()
                    st.session_state.cal_event_selectionne = None
                    st.success("Séance supprimée !")
                    st.rerun()
            with b3:
                if st.button("✖ Fermer", key=f"cl_ev_{ev_sel['id']}"):
                    st.session_state.cal_event_selectionne = None
                    st.rerun()
        else:
            st.info("👆 Cliquez sur un bouton de séance dans le calendrier ci-dessus pour l'ouvrir, la modifier ou la supprimer.")

# =====================================================================
# PAGE : FICHIERS & RAPPORTS GPS (Avec gestion, modification et suppression)
# =====================================================================
elif menu == "📁 Fichiers & Rapports GPS":
    st.header("📁 Fichiers de Séances & Rapports GPS")

    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
    dict_athletes = {a.get("full_name"): a["id"] for a in res_athletes if a.get("full_name")}
    res_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []

    dict_events = {}
    for ev in res_events:
        ev_title = ev.get("title") or "Séance"
        date_str = (ev.get("start_time") or "")[:16].replace("T", " ")
        dict_events[f"{ev_title} ({date_str})"] = ev

    tab_upload, tab_manage_files, tab_gps = st.tabs([
        "📤 Joindre un PDF", 
        "📚 Gérer les fichiers & GPS envoyés", 
        "🛰️ Importer un rapport GPS (xlsx/csv)"
    ])

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

    with tab_manage_files:
        st.subheader("📚 Gestion des documents et rapports GPS enregistrés")
        
        fichiers_publies = supabase.table("session_files").select("*").execute().data or []
        if fichiers_publies:
            st.markdown("##### 📄 Documents PDF / Images publiés")
            for f in fichiers_publies:
                col_f1, col_f2 = st.columns([4, 1])
                with col_f1:
                    st.write(f"• **{f.get('title')}** (`{f.get('file_name', 'Fichier')}`)")
                with col_f2:
                    if st.button("Supprimer", key=f"del_sf_{f['id']}"):
                        supabase.table("session_files").delete().eq("id", f["id"]).execute()
                        st.success("Fichier supprimé.")
                        st.rerun()
        else:
            st.info("Aucun document PDF publié.")

        st.markdown("---")
        rapports_gps_db = obtenir_rapports_gps()
        if rapports_gps_db:
            st.markdown("##### 🛰️ Rapports GPS enregistrés en base")
            for rg in rapports_gps_db[:20]:
                col_g1, col_g2 = st.columns([4, 1])
                with col_g1:
                    st.write(f"• Rapport ID `{rg.get('id')}` — Dist: {rg.get('distance_totale_m', 0)}m | Vmax: {rg.get('vmax_kmh', 0)} km/h")
                with col_g2:
                    if st.button("Supprimer le GPS", key=f"del_rg_{rg['id']}"):
                        supabase.table("gps_reports").delete().eq("id", rg["id"]).execute()
                        st.success("Rapport GPS supprimé.")
                        st.rerun()
        else:
            st.info("Aucun rapport GPS en base.")

    with tab_gps:
        st.subheader("🛰️ Import de rapport GPS")
        st.caption("L'importation est active pour rattacher les métriques GPS aux athlètes reconnus (ex: Axel Bargain).")
        if dict_events:
            gps_event_label = st.selectbox("Séance GPS :", list(dict_events.keys()), key="gps_ev_sel")
            gps_file = st.file_uploader("Fichier GPS (.csv, .xlsx)", type=["csv", "xlsx", "xls"])

            if gps_file:
                try:
                    lignes = lire_fichier_gps(gps_file.read(), nom_fichier=gps_file.name)
                except Exception as ex:
                    lignes = []
                    st.error(f"Erreur de lecture du GPS : {ex}")

                if lignes:
                    st.dataframe(pd.DataFrame(lignes), use_container_width=True)
                    if st.button("💾 Importer dans la base", type="primary"):
                        selected_event = dict_events[gps_event_label]
                        n_ins, non_trouves = enregistrer_rapport_gps(selected_event["id"], lignes, dict_athletes)
                        st.success(f"✅ {n_ins} lignes GPS importées avec succès !")
                        if non_trouves:
                            st.warning(f"Joueurs non reconnus (vérifiez l'orthographe exacte) : {', '.join(non_trouves)}")

# =====================================================================
# PAGE : QUESTIONNAIRES (Création dynamique complète, modification et assignation)
# =====================================================================
elif menu == "📝 Questionnaires":
    st.header("📝 Questionnaires & Alertes Coach")
    
    st.subheader("🚨 Alertes & Vigilance effectif")
    st.info("Le système surveille les réponses wellness (douleurs musculaires) et les écarts de RPE par rapport au RPE cible des séances.")

    tab_creer, tab_assigner = st.tabs(["🆕 Créer & Modifier un questionnaire", "📩 Assigner aux athlètes"])

    with tab_creer:
        q_list_exist = supabase.table("questionnaires").select("*").execute().data or []
        dict_q_exist = {q["title"]: q for q in q_list_exist}

        mode_q = st.radio("Action :", ["Créer un nouveau questionnaire", "Modifier un questionnaire existant"], horizontal=True)

        if mode_q == "Créer un nouveau questionnaire":
            q_title = st.text_input("Titre du nouveau questionnaire")
            q_type = st.selectbox("Type", ["Pre-Event (Wellness)", "Post-Event (RPE)"])

            if "questions_draft" not in st.session_state:
                st.session_state.questions_draft = []

            st.markdown("##### ➕ Ajouter des questions")
            c1, c2, c3 = st.columns([4, 3, 2])
            with c1:
                q_label = st.text_input("Intitulé de la question")
            with c2:
                q_fmt = st.selectbox("Format", ["Échelle numérique (Note)", "Texte libre", "Nombre libre", "🚑 Oui/Non (Blessure)"])
            with c3:
                scale_max = st.number_input("Max", min_value=2, max_value=10, value=5) if "Échelle" in q_fmt else None

            if st.button("+ Ajouter cette question au questionnaire"):
                if q_label:
                    fmt_val = FORMAT_BLESSURE if "Blessure" in q_fmt else ("scale" if "Échelle" in q_fmt else ("number" if "Nombre" in q_fmt else "text"))
                    st.session_state.questions_draft.append({"label": q_label, "format": fmt_val, "scale_max": scale_max})
                    st.rerun()

            for idx, q in enumerate(st.session_state.questions_draft):
                st.write(f"**Q{idx+1}:** {q['label']} ({q['format']})")

            if st.button("💾 Enregistrer le questionnaire complet", type="primary"):
                if q_title and st.session_state.questions_draft:
                    supabase.table("questionnaires").insert({
                        "title": q_title,
                        "type": "pre_event" if "Pre" in q_type else "post_event",
                        "questions": st.session_state.questions_draft
                    }).execute()
                    st.session_state.questions_draft = []
                    st.success("Questionnaire enregistré avec succès !")
                    st.rerun()
                else:
                    st.error("Veuillez donner un titre et ajouter au moins une question.")
        else:
            if dict_q_exist:
                sel_mod_q = st.selectbox("Choisir le questionnaire à modifier :", list(dict_q_exist.keys()))
                q_to_edit = dict_q_exist[sel_mod_q]
                new_title_edit = st.text_input("Modifier le titre", value=q_to_edit.get("title", ""))
                if st.button("Mettre à jour le titre", type="primary"):
                    supabase.table("questionnaires").update({"title": new_title_edit}).eq("id", q_to_edit["id"]).execute()
                    st.success("Questionnaire mis à jour !")
                    st.rerun()
                if st.button("❌ Supprimer ce questionnaire", type="primary"):
                    supabase.table("questionnaires").delete().eq("id", q_to_edit["id"]).execute()
                    st.success("Questionnaire supprimé.")
                    st.rerun()
            else:
                st.info("Aucun questionnaire existant à modifier.")

    with tab_assigner:
        st.subheader("📩 Assigner un questionnaire")
        q_data = supabase.table("questionnaires").select("*").execute().data or []
        a_data = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []

        if q_data and a_data:
            dict_q_obj = {q["title"]: q for q in q_data}
            dict_a = {a["full_name"]: a["id"] for a in a_data if a.get("full_name")}

            sel_q_title = st.selectbox("Sélectionner le questionnaire :", list(dict_q_obj.keys()))
            q_obj_sel = dict_q_obj[sel_q_title]

            sel_a = st.multiselect("Athlète(s) concerné(s) :", list(dict_a.keys()))

            if st.button("🚀 Assigner la sélection", type="primary"):
                if sel_a:
                    for name in sel_a:
                        assigner_questionnaire(q_obj_sel["id"], dict_a[name], None)
                    st.success("Questionnaire assigné avec succès !")
                    st.rerun()
                else:
                    st.error("Sélectionnez au moins un athlète.")
        else:
            st.info("Veuillez d'abord créer au moins un questionnaire et enregistrer des athlètes.")

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
# PAGE : GESTION DES PROFILS (Athlètes, Équipes, Comptes & Tests physiques)
# =====================================================================
elif menu == "⚙️ Gestion des profils":
    st.header("⚙️ Gestion des Profils, Équipes & Comptes")
    tab_ath, tab_teams, tab_comptes = st.tabs(["👤 Athlètes & Tests", "🛡️ Équipes", "🔑 Comptes de connexion"])

    with tab_ath:
        st.subheader("Modifier ou supprimer un athlète et gérer ses tests physiques")
        ath_data = supabase.table("profiles").select("*").eq("role", "athlete").execute().data or []
        teams_data = supabase.table("teams").select("*").execute().data or []
        dict_teams_add = {t["name"]: t["id"] for t in teams_data}

        if ath_data:
            dict_ath = {a["full_name"]: a for a in ath_data if a.get("full_name")}
            sel = st.selectbox("Sélectionner un athlète :", list(dict_ath.keys()))
            ath = dict_ath[sel]
            ath_id = ath["id"]

            new_name = st.text_input("Nom & Prénom", value=ath.get("full_name", ""))
            current_team_id = ath.get("team_id")
            current_team_name = "Aucune"
            for tname, tid in dict_teams_add.items():
                if tid == current_team_id:
                    current_team_name = tname
            team_idx = (["Aucune"] + list(dict_teams_add.keys())).index(current_team_name) if current_team_name in dict_teams_add else 0
            upd_team = st.selectbox("Équipe", ["Aucune"] + list(dict_teams_add.keys()), index=team_idx)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Mettre à jour le profil"):
                    new_t_id = dict_teams_add[upd_team] if upd_team != "Aucune" else None
                    supabase.table("profiles").update({"full_name": new_name, "team_id": new_t_id}).eq("id", ath_id).execute()
                    st.success("Profil mis à jour avec succès !")
                    st.rerun()
            with c2:
                if st.button("❌ Supprimer cet athlète", type="primary"):
                    ok, msg = supprimer_compte(ath_id)
                    if ok:
                        st.success("Athlète supprimé !")
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")
            st.subheader(f"🏃 Tests physiques de {new_name}")
            tests_db = supabase.table("physical_tests").select("*").eq("athlete_id", ath_id).execute().data or []
            if tests_db:
                for t in tests_db:
                    st.write(f"• **{t.get('test_name')}** : {t.get('test_value')} {t.get('unit')}")
            
            st.markdown("##### ➕ Ajouter un test physique")
            t_name = st.text_input("Nom du test (ex: VMA, 1RM Squat)")
            t_val = st.number_input("Valeur", value=0.0)
            t_unit = st.text_input("Unité", value="km/h")
            if st.button("Enregistrer le test"):
                if t_name:
                    supabase.table("physical_tests").insert({"athlete_id": ath_id, "test_name": t_name, "test_value": t_val, "unit": t_unit}).execute()
                    st.success("Test enregistré !")
                    st.rerun()
        else:
                    st.info("Aucun athlète enregistré.")

    with tab_teams:
        st.subheader("Gestion des équipes")
        new_t = st.text_input("Nom de la nouvelle équipe")
        if st.button("Créer l'équipe"):
            if new_t:
                supabase.table("teams").insert({"name": new_t}).execute()
                st.success("Équipe créée !")
                st.rerun()

        teams_list = supabase.table("teams").select("*").execute().data or []
        if teams_list:
            st.markdown("##### Équipes existantes")
            for t in teams_list:
                col_eq1, col_eq2 = st.columns([4, 1])
                with col_eq1:
                    st.write(f"• **{t['name']}**")
                with col_eq2:
                    if st.button("Supprimer", key=f"del_eq_{t['id']}"):
                        supabase.table("teams").delete().eq("id", t["id"]).execute()
                        st.success("Équipe supprimée.")
                        st.rerun()

    with tab_comptes:
        st.subheader("Création de compte (Athlète ou Coach)")
        with st.form("form_cpt"):
            email = st.text_input("E-mail")
            pwd = st.text_input("Mot de passe", type="password")
            nom = st.text_input("Nom complet")
            role = st.selectbox("Rôle", ["athlete", "coach"], format_func=lambda r: "🏃 Athlète" if r == "athlete" else "🏋️ Coach")
            if st.form_submit_button("Créer le compte"):
                if email and pwd and nom:
                    ok, msg = creer_compte(email, pwd, nom, role)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

# =====================================================================
# PAGE : GÉNÉRATEUR DE BIPS AUDIO (Complet)
# =====================================================================
elif menu == "🔊 Générateur de Bips Audio":
    import wave
    import math
    import struct
    import io

    st.header("🔊 Générateur de Bips Audio (Tests VMA & Pacing)")
    st.write("Créez sur-mesure des bandes sonores rythmées par des bips haute intensité pour vos tests de terrain.")

    def generate_beep_audio(interval_mode, base_interval, min_interval, total_beps, accel_trigger, accel_value, step_decrement, bip_freq=1800, bip_duration=0.2, wave_type="Carrée"):
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
                raw_signal = 1.0 if (sin_val >= 0 and "Carrée" in w_type) else sin_val
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
                beep_wave = create_wave(2400, bip_duration * 0.6, wave_type) + create_silence(0.04) + create_wave(2400, bip_duration, wave_type)
                used_bip_dur = (bip_duration * 1.6) + 0.04
            else:
                beep_wave = create_wave(bip_freq, bip_duration, wave_type)
                used_bip_dur = bip_duration

            silence_duration = max(0.0, current_interval - used_bip_dur)
            audio_frames.extend(beep_wave)
            audio_frames.extend(create_silence(silence_duration))
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
        mode = st.radio("Type de test :", ["Constant (Intervalle fixe)", "Progressif / Accéléré"])
        base_int = st.number_input("Intervalle de départ (secondes) :", value=5.0, step=0.5)
        total_beps = st.number_input("Nombre total de bips :", value=30, step=1)
    with col_cfg2:
        wave_type = st.selectbox("Type de son :", ["Carrée (Buzzer Puissant)", "Sinusoïdale (Bip classique)"])
        bip_duration = st.slider("Durée du bip (sec) :", value=0.25, step=0.05)
        bip_freq = st.slider("Fréquence (Hz) :", value=2000, step=100)

    if st.button("🎵 Générer la bande sonore", type="primary", use_container_width=True):
        audio_data = generate_beep_audio("Constant", base_int, base_int, total_beps, "Tous les X bips", 1, 0.0, bip_freq, bip_duration, wave_type)
        st.success("✅ Fichier audio généré !")
        st.audio(audio_data, format="audio/wav")
        st.download_button("💾 Télécharger (.WAV)", data=audio_data, file_name="bips_terrain.wav", mime="audio/wav", use_container_width=True)

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
