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

    /* Ajustement bouton ouverture barre latérale (plus bas sur mobile/écran) */
    [data-testid="collapsedControl"] {
        top: 1.5rem !important;
        left: 1rem !important;
        background-color: var(--bg-panel) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }

    /* Masquer les boutons superflus en haut à droite (GitHub, share, etc.) */
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

    .badge-dispo {
        background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.4);
        padding: 3px 12px; border-radius: 999px; font-size: 0.85em; font-weight: 600;
    }
    .badge-blesse {
        background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.4);
        padding: 3px 12px; border-radius: 999px; font-size: 0.85em; font-weight: 600;
    }

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
# PAGE : PLANNING & SÉANCES
# =====================================================================
if menu == "📅 Planning & Séances":
    st.header("📅 Planning & Séances")

    res_athletes = supabase.table("profiles").select("id, full_name, team_id").eq("role", "athlete").execute()
    athletes_list = res_athletes.data if res_athletes.data else []
    dict_athletes = {a.get("full_name", f"Athlète {a['id']}"): a["id"] for a in athletes_list if a.get("full_name")}
    
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

    # Section Alertes Coach (douleurs musculaires, wellness extrême, écart RPE cible)
    st.markdown("---")
    st.subheader("🚨 Alertes & Remontées Joueurs")
    toutes_reponses_alertes = obtenir_reponses_avec_definitions()
    alertes_count = 0
    for resp in toutes_reponses_alertes[:15]:
        ans = resp.get("answers", {})
        if isinstance(ans, str):
            try: ans = json.loads(ans)
            except: ans = {}
        for qk, qv in ans.items():
            if str(qv).strip().lower() in ["oui", "yes", "1"] or ("douleur" in qk.lower() and str(qv).strip().lower() not in ["non", "rien", "0", ""]):
                alertes_count += 1
                nom_j = next((k for k, v in dict_athletes.items() if v == resp.get("athlete_id")), "Un joueur")
                st.warning(f"⚠️ **Alerte Douleur / Wellness** — {nom_j} a répondu : *{qk} : {qv}*")
    if alertes_count == 0:
        st.success("Aucune alerte musculaire ou wellness critique récente.")

    st.markdown("---")
    tab_nouvelle, tab_existantes = st.tabs(["🆕 Planifier une nouvelle séance", "📋 Séances planifiées (modifier / supprimer)"])

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
            exclure_blesses = st.checkbox(
                "🚑 Exclure automatiquement les joueurs en réathlétisation de '-- Tous les athlètes --'",
                value=True
            )
            location = st.text_input("Lieu")
            rpe_cible = st.number_input("🎯 RPE Cible (1-10)", min_value=1.0, max_value=10.0, value=7.0, step=0.5)

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
                    st.warning("Aucun joueur disponible à programmer.")
                else:
                    try:
                        res_inserted = supabase.table("events").insert(events_to_insert).execute()
                        # Création automatique du questionnaire RPE (1 à 10) par défaut pour ces séances
                        q_exist = supabase.table("questionnaires").select("id").eq("title", "RPE Post-Séance (Auto)").execute().data
                        if q_exist:
                            q_auto_id = q_exist[0]["id"]
                        else:
                            q_ins = supabase.table("questionnaires").insert({
                                "title": "RPE Post-Séance (Auto)",
                                "type": "post_event",
                                "questions": [{"label": "Score RPE global de la séance", "format": "scale", "scale_max": 10}]
                            }).execute().data
                            q_auto_id = q_ins[0]["id"] if q_ins else None

                        if q_auto_id and res_inserted.data:
                            for ev_ins in res_inserted.data:
                                assigner_questionnaire(q_auto_id, ev_ins["athlete_id"], ev_ins["id"])

                        st.success(f"✅ Séance(s) planifiée(s) avec RPE cible et questionnaire auto !")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erreur Supabase : {ex}")

    with tab_existantes:
        import calendar as _calendar

        # Filtre de vue Planning pour le coach (Son planning, Équipe, ou Joueur)
        st.markdown("#### 👁️ Affichage du planning")
        vue_planning = st.selectbox("Voir le planning de :", ["Mon planning global (toutes mes séances)", "Une équipe spécifique", "Un joueur spécifique"])
        tous_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []

        if vue_planning == "Une équipe spécifique" and dict_teams_all:
            eq_choisie_p = st.selectbox("Choisir l'équipe :", list(dict_teams_all.keys()))
            eq_id_p = dict_teams_all[eq_choisie_p]
            ids_eq_athletes = {a["id"] for a in athletes_list if a.get("team_id") == eq_id_p}
            tous_events = [e for e in tous_events if e.get("athlete_id") in ids_eq_athletes]
        elif vue_planning == "Un joueur spécifique" and dict_athletes:
            joueur_choisi_p = st.selectbox("Choisir le joueur :", list(dict_athletes.keys()))
            j_id_p = dict_athletes[joueur_choisi_p]
            tous_events = [e for e in tous_events if e.get("athlete_id") == j_id_p]

        dict_athletes_inv = {v: k for k, v in dict_athletes.items()}

        if not tous_events:
            st.info("Aucune séance planifiée pour cette sélection.")
        else:
            events_par_jour = {}
            for ev in tous_events:
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

            st.markdown("---")
            ev_id_sel = st.session_state.cal_event_selectionne
            ev_sel = next((e for e in tous_events if e["id"] == ev_id_sel), None) if ev_id_sel else None

            if ev_sel:
                st.subheader(f"✏️ Modifier : {ev_sel.get('title')}")
                ev_id = ev_sel["id"]
                try:
                    dt_start_existing = datetime.fromisoformat(ev_sel.get("start_time").replace("Z", "+00:00"))
                    dt_end_existing = datetime.fromisoformat(ev_sel.get("end_time").replace("Z", "+00:00"))
                except:
                    dt_start_existing, dt_end_existing = datetime.now(), datetime.now()

                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    edit_title = st.text_input("Titre", value=ev_sel.get("title", ""), key=f"edit_title_{ev_id}")
                    edit_type = st.selectbox("Type", ["training", "match"], index=0 if ev_sel.get("event_type") != "match" else 1, key=f"edit_type_{ev_id}")
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
                    if st.button("💾 Enregistrer", type="primary", key=f"save_ev_{ev_id}"):
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
                    if st.button("❌ Supprimer", type="primary", key=f"del_ev_{ev_id}"):
                        supabase.table("events").delete().eq("id", ev_id).execute()
                        st.session_state.cal_event_selectionne = None
                        st.success("Séance supprimée !")
                        st.rerun()
                with c_b3:
                    if st.button("✖ Fermer", key=f"close_ev_{ev_id}"):
                        st.session_state.cal_event_selectionne = None
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
    dict_events_info = {}
    for ev in res_events:
        ev_id = ev["id"]
        ev_title = ev.get("title") or "Séance"
        ev_start = ev.get("start_time", "")
        ev_ath_id = ev.get("athlete_id")
        date_str = ev_start[:16].replace("T", " ") if ev_start else ""
        ath_name = next((name for name, aid in dict_athletes.items() if aid == ev_ath_id), "Tous")
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
            st.warning("Aucune séance planifiée.")
        else:
            selected_event_label = st.selectbox("📌 Choisir la séance :", list(dict_events.keys()))
            selected_event = dict_events[selected_event_label]
            session_title = st.text_input("Nom du document / Titre du PDF :", value=selected_event.get("title", ""))
            description = st.text_area("Instructions :")
            uploaded_file = st.file_uploader("Fichier PDF ou Image", type=["pdf", "png", "jpg", "jpeg"])

            if st.button("🚀 Publier sur la séance", type="primary"):
                if not session_title or not uploaded_file:
                    st.error("Renseignez un nom et un fichier.")
                else:
                    file_bytes = uploaded_file.read()
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    mime_type = uploaded_file.type or "application/octet-stream"
                    storage_path = f"{int(datetime.now().timestamp())}_{uploaded_file.name}"
                    try:
                        file_url = upload_file_direct_http("session-files", storage_path, file_bytes, mime_type)
                    except:
                        file_url = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode('utf-8')}"

                    record = {
                        "title": session_title, "description": description,
                        "file_name": uploaded_file.name, "file_url": file_url,
                        "file_type": file_ext, "athlete_id": selected_event.get("athlete_id"),
                        "event_id": selected_event.get("id"), "created_at": datetime.now().isoformat()
                    }
                    supabase.table("session_files").insert([record]).execute()
                    st.success("✅ Fichier associé avec succès !")
                    st.rerun()

    with tab_list:
        files_db = supabase.table("session_files").select("*").order("created_at", desc=True).execute().data or []
        for f in (files_db or []):
            with st.expander(f"📄 {f.get('title')}"):
                if st.button("❌ Supprimer", key=f"del_f_{f['id']}"):
                    supabase.table("session_files").delete().eq("id", f["id"]).execute()
                    st.rerun()

    with tab_gps:
        st.subheader("🛰️ Importer un rapport GPS (fichier Excel / CSV)")
        if not dict_events:
            st.warning("Créez d'abord une séance.")
        else:
            gps_event_label = st.selectbox("📌 Séance concernée :", list(dict_events.keys()), key="gps_event_sel")
            gps_file = st.file_uploader("Fichier GPS", type=["csv", "xlsx", "xls"], key="gps_file_uploader")

            if gps_file:
                try:
                    lignes = lire_fichier_gps(gps_file.read(), nom_fichier=gps_file.name)
                except Exception as ex:
                    lignes = []
                    st.error(f"Erreur lecture fichier : {ex}")

                if lignes:
                    st.write(f"**Aperçu ({len(lignes)} joueur(s) détecté(s)) :**")
                    st.dataframe(pd.DataFrame(lignes), use_container_width=True)

                    if st.button("💾 Importer ce rapport GPS", type="primary"):
                        selected_event = dict_events[gps_event_label]
                        n_inseres, non_trouves = enregistrer_rapport_gps(selected_event["id"], lignes, dict_athletes)
                        st.success(f"✅ {n_inseres} ligne(s) GPS importée(s).")
                        if non_trouves:
                            st.warning(f"Noms non reconnus (vérifiez l'orthographe par rapport aux profils athlètes) : {', '.join(non_trouves)}")
                        st.rerun()

# =====================================================================
# PAGE : QUESTIONNAIRES
# =====================================================================
elif menu == "📝 Questionnaires":
    st.header("📝 Questionnaires")
    tab_creer, tab_envoyer, tab_repondre = st.tabs(["🆕 Créer", "📩 Assigner", "✍️ Saisie manuelle"])

    with tab_creer:
        q_title = st.text_input("Titre du questionnaire")
        q_type = "pre_event" if "Pre" in st.selectbox("Type", ["Pre-Event (Wellness)", "Post-Event (RPE)"]) else "post_event"
        if "questions_draft" not in st.session_state:
            st.session_state.questions_draft = []

        new_q_label = st.text_input("Intitulé de la question")
        q_format = st.selectbox("Format", ["Échelle numérique", "Texte libre", "Nombre libre", "🚑 Oui/Non (blessure)"])
        scale_max = st.number_input("Max", 2, 10, 5) if "Échelle" in q_format else None

        if st.button("+ Ajouter la question"):
            if new_q_label:
                fmt = FORMAT_BLESSURE if "blessure" in q_format.lower() else ("scale" if "Échelle" in q_format else ("number" if "Nombre" in q_format else "text"))
                st.session_state.questions_draft.append({"label": new_q_label, "format": fmt, "scale_max": scale_max})
                st.rerun()

        for idx, q in enumerate(st.session_state.questions_draft):
            st.info(f"Q{idx+1}: {q['label']} ({q['format']})")

        if st.button("💾 Enregistrer le modèle", type="primary"):
            if q_title and st.session_state.questions_draft:
                supabase.table("questionnaires").insert({"title": q_title, "type": q_type, "questions": st.session_state.questions_draft}).execute()
                st.session_state.questions_draft = []
                st.success("Modèle enregistré !")
                st.rerun()

    with tab_envoyer:
        q_data = supabase.table("questionnaires").select("*").execute().data or []
        a_data = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
        if q_data and a_data:
            dict_q_obj = {q["title"]: q for q in q_data}
            dict_a = {a["full_name"]: a["id"] for a in a_data if a.get("full_name")}
            sel_q_title = st.selectbox("Questionnaire :", list(dict_q_obj.keys()))
            q_obj_sel = dict_q_obj[sel_q_title]
            sel_a = st.multiselect("Athlète(s) :", list(dict_a.keys()))
            if st.button("Attribuer", type="primary"):
                for name in sel_a:
                    assigner_questionnaire(q_obj_sel["id"], dict_a[name], None)
                st.success("Assigné !")
                st.rerun()

    with tab_repondre:
        athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
        dict_athletes = {a.get("full_name"): a["id"] for a in athletes if a.get("full_name")}
        if dict_athletes:
            sel_athlete_name = st.selectbox("Athlète :", list(dict_athletes.keys()))
            selected_athlete_id = dict_athletes[sel_athlete_name]
            events_ath = supabase.table("events").select("id, title, start_time").eq("athlete_id", selected_athlete_id).execute().data or []
            dict_events_rep = {f"{ev.get('title')} — {ev.get('start_time','')[:16]}": ev["id"] for ev in events_ath}
            q_list = supabase.table("questionnaires").select("*").execute().data or []
            if dict_events_rep and q_list:
                sel_event_label = st.selectbox("Séance :", list(dict_events_rep.keys()))
                selected_event_id = dict_events_rep[sel_event_label]
                sel_q_title = st.selectbox("Questionnaire :", [q["title"] for q in q_list])
                q_obj = next(q for q in q_list if q["title"] == sel_q_title)
                rep = obtenir_reponse_evenement(selected_athlete_id, selected_event_id)
                rendre_formulaire_questionnaire(q_obj, selected_event_id, f"manuel_{selected_athlete_id}", (rep.get("answers") or {}) if rep else {}, athlete_id=selected_athlete_id)

# =====================================================================
# PAGE (ATHLÈTE) : SÉANCES À VENIR
# =====================================================================
elif menu == "📅 Séances à venir":
    st.header("📅 Mes séances à venir")
    maintenant = datetime.now()
    events_mine_raw = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
    a_venir = [e for e in events_mine_raw if _parser_datetime_event(e) and _parser_datetime_event(e).date() >= maintenant.date()]
    a_venir.sort(key=lambda e: e["start_time"])

    q_all = supabase.table("questionnaires").select("*").execute().data or []
    q_pre = [q for q in q_all if q.get("type") == "pre_event"]
    q_post = [q for q in q_all if q.get("type") != "pre_event"]
    assignations = obtenir_assignations()

    if not a_venir:
        st.info("Aucune séance à venir.")
    else:
        for i, ev in enumerate(a_venir):
            dt_start = _parser_datetime_event(ev)
            with st.expander(f"🏋️ {ev.get('title')} — {dt_start.strftime('%d/%m/%Y à %H:%M')}", expanded=(i == 0)):
                afficher_fichiers_evenement(ev["id"], key_prefix=f"av_{ev['id']}")
                rep = obtenir_reponse_evenement(mon_id, ev["id"])
                reponses_deja = (rep.get("answers") or {}) if rep else {}

                st.markdown("##### 🌅 Avant la séance")
                for q in q_pre:
                    if questionnaire_disponible_pour(q["id"], mon_id, ev["id"], assignations):
                        rendre_formulaire_questionnaire(q, ev["id"], f"pre_{ev['id']}_{q['id']}", reponses_deja)

                st.markdown("##### 🌙 Après la séance (RPE)")
                for q in q_post:
                    rendre_formulaire_questionnaire(q, ev["id"], f"post_{ev['id']}_{q['id']}", reponses_deja)

# =====================================================================
# PAGE (ATHLÈTE) : CALENDRIER
# =====================================================================
elif menu == "📆 Calendrier":
    st.header("📆 Calendrier")
    events_mine_raw = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
    for ev in events_mine_raw:
        st.write(f"• **{ev.get('title')}** ({ev.get('start_time','')[:10]})")

# =====================================================================
# PAGE (ATHLÈTE) : MES DONNÉES
# =====================================================================
elif menu == "📊 Mes données":
    st.header("📊 Mes données")
    res_resp = supabase.table("questionnaire_responses").select("*").eq("athlete_id", mon_id).execute().data or []
    records_flat = []
    for r in res_resp:
        ans = r.get("answers", {})
        if isinstance(ans, str):
            try: ans = json.loads(ans)
            except: ans = {}
        for k, v in ans.items():
            records_flat.append({"Question": k, "Valeur": v, "Date": r.get("submitted_at","")[:10]})
    if records_flat:
        st.dataframe(pd.DataFrame(records_flat), use_container_width=True)
    else:
        st.info("Aucune donnée.")

# =====================================================================
# PAGE : ANALYTIQUE (avec moyenne équipe et onglets épurés)
# =====================================================================
elif menu == "📊 Analytique":
    st.header("📊 Analytique")

    profiles = supabase.table("profiles").select("*").execute().data or []
    dict_profiles = {p["id"]: p.get("full_name", "") for p in profiles}
    dict_athletes = {p.get("full_name"): p["id"] for p in profiles if p.get("role") == "athlete"}
    teams_all = supabase.table("teams").select("*").execute().data or []
    dict_teams_an = {t["name"]: t["id"] for t in teams_all}

    mode_analyse = st.radio("Analyser :", ["👤 Un joueur", "👥 Une équipe", "🆚 Comparaison"], horizontal=True)
    scope_joueurs = []
    is_team_mode = False

    if mode_analyse == "👤 Un joueur":
        j = st.selectbox("Joueur :", sorted(dict_athletes.keys()))
        scope_joueurs = [j] if j else []
    elif mode_analyse == "👥 Une équipe":
        eq = st.selectbox("Équipe :", sorted(dict_teams_an.keys()))
        if eq:
            tid = dict_teams_an[eq]
            scope_joueurs = [p.get("full_name") for p in profiles if p.get("team_id") == tid and p.get("full_name")]
            is_team_mode = True
    else:
        scope_joueurs = st.multiselect("Joueurs :", sorted(dict_athletes.keys()))

    if not scope_joueurs:
        st.info("Sélectionnez des joueurs ou une équipe.")
        st.stop()

    res_resp = supabase.table("questionnaire_responses").select("*").execute().data or []
    records_flat = []
    for r in res_resp:
        nom = dict_profiles.get(r.get("athlete_id"), "")
        ans = r.get("answers", {})
        if isinstance(ans, str):
            try: ans = json.loads(ans)
            except: ans = {}
        for k, v in ans.items():
            try: val_c = float(v)
            except: val_c = v
            records_flat.append({"Joueur": nom, "Question": k, "Valeur": val_c, "Date": r.get("submitted_at","")[:10]})

    df_flat = pd.DataFrame(records_flat) if records_flat else pd.DataFrame()
    if not df_flat.empty:
        df_flat = df_flat[df_flat["Joueur"].isin(scope_joueurs)]

    # Les 5 onglets demandés
    tab_q, tab_g, tab_comp, tab_gps, tab_brut = st.tabs([
        "Réponses par question", "Graphique", "Comparaison joueur", "Les données GPS", "Données brutes"
    ])

    with tab_q:
        if not df_flat.empty:
            if is_team_mode:
                st.markdown("### 👥 Moyenne de l'équipe par question")
                df_num = df_flat[df_flat["Valeur"].apply(lambda x: isinstance(x, (int, float)))]
                moy_eq = df_num.groupby("Question")["Valeur"].mean().reset_index()
                st.dataframe(moy_eq, use_container_width=True)
            else:
                st.dataframe(df_flat, use_container_width=True)
        else:
            st.info("Aucune donnée.")

    with tab_g:
        if not df_flat.empty:
            df_num = df_flat[df_flat["Valeur"].apply(lambda x: isinstance(x, (int, float)))]
            if not df_num.empty:
                q_sel = st.selectbox("Variable :", df_num["Question"].unique())
                fig = px.line(df_num[df_num["Question"] == q_sel], x="Date", y="Valeur", color="Joueur" if not is_team_mode else None, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

    with tab_comp:
        st.markdown("### 🆚 Comparaison inter-joueurs")
        if not df_flat.empty:
            df_num = df_flat[df_flat["Valeur"].apply(lambda x: isinstance(x, (int, float)))]
            if not df_num.empty:
                q_sel = st.selectbox("Variable à comparer :", df_num["Question"].unique(), key="cmp_q")
                fig_bar = px.bar(df_num[df_num["Question"] == q_sel], x="Joueur", y="Valeur", color="Joueur", template="plotly_dark")
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab_gps:
        st.markdown("### 🛰️ Données GPS")
        gps_all = obtenir_rapports_gps()
        gps_rows = [{ "Joueur": dict_profiles.get(g.get("athlete_id")), **{m: g.get(m) for m in COLONNES_GPS_NUMERIQUES} } for g in gps_all]
        df_gps_all = pd.DataFrame(gps_rows) if gps_rows else pd.DataFrame()
        if not df_gps_all.empty and "Joueur" in df_gps_all.columns:
            df_gps_all = df_gps_all[df_gps_all["Joueur"].isin(scope_joueurs)]
            if is_team_mode:
                st.markdown("#### Moyenne GPS de l'équipe")
                st.dataframe(df_gps_all.mean(numeric_only=True).reset_index(), use_container_width=True)
            else:
                st.dataframe(df_gps_all, use_container_width=True)
        else:
            st.info("Aucune donnée GPS.")

    with tab_brut:
        if not df_flat.empty:
            st.dataframe(df_flat, use_container_width=True)

# =====================================================================
# PAGE : GESTION DES PROFILS
# =====================================================================
elif menu == "⚙️ Gestion des profils":
    st.header("⚙️ Gestion des Profils, Équipes & Comptes")
    tab_ath, tab_teams, tab_comptes = st.tabs(["👤 Athlètes & Tests", "🛡️ Équipes", "🔑 Comptes"])

    with tab_teams:
        st.subheader("Créer une équipe")
        new_t = st.text_input("Nom de l'équipe")
        if st.button("Créer"):
            if new_t:
                creer_equipe(new_t)
                st.success("Équipe créée !")
                st.rerun()

    with tab_comptes:
        st.subheader("Créer un compte")
        with st.form("fc"):
            em = st.text_input("E-mail")
            pw = st.text_input("Mot de passe", type="password")
            fn = st.text_input("Nom complet")
            rl = st.selectbox("Rôle", ["athlete", "coach"])
            if st.form_submit_button("Créer"):
                ok, msg = creer_compte(em, pw, fn, rl)
                if ok: st.success(msg); st.rerun()
                else: st.error(msg)

# =====================================================================
# PAGE : GÉNÉRATEUR DE BIPS AUDIO
# =====================================================================
elif menu == "🔊 Générateur de Bips Audio":
    st.header("🔊 Générateur de Bips Audio")
    st.write("Outil de génération de bandes sonores pour tests VMA.")
