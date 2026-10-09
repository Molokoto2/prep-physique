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
    supprimer_assignation,
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
    "duree_secondes": "Durée (minutes)",
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
                st.success("✅ Connexion réussie !")
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
        "👥 Effectif",
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
            if not valeurs_manquantes and ok:
                st.session_state.pop("cache_statuts_dispo", None)
                st.success("✅ [Validé avec succès] Enregistré !")
                st.rerun()
            elif not valeurs_manquantes:
                st.error(f"Erreur lors de l'enregistrement : {err}")

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
JOURS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

def maintenant_local():
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
    fichiers = obtenir_fichiers_evenement(event_id)
    if not fichiers:
        return
    st.markdown("##### 📎 Documents de la séance")
    for f in fichiers:
        f_url = f.get("file_url", "")
        if f_url.startswith("data:"):
            try:
                st.download_button(
                    f"💾 📄 {f.get('title', 'Document')} (PDF)",
                    data=base64.b64decode(f_url.split(",")[1]),
                    file_name=f.get("file_name", "document.pdf"),
                    key=f"{key_prefix}_dl_{f['id']}"
                )
            except Exception:
                st.caption(f"⚠️ {f.get('title', 'Document')} (fichier indisponible)")
        else:
            st.markdown(f"📄 📄 [{f.get('title', 'Document')}]({f_url})")
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
    dict_athletes_inv = {v: k for k, v in dict_athletes.items()}
    
    teams_list_all = supabase.table("teams").select("*").execute().data or []
    dict_teams_all = {t["name"]: t["id"] for t in teams_list_all}

    statuts = get_statuts_disponibilite()
    ids_blesses = {aid for aid, s in statuts.items() if s["statut"] == "blesse"}

    # Séance du jour et du lendemain
    st.markdown("### ⚡ Séances du jour & du lendemain")
    toutes_seances_brutes = supabase.table("events").select("*").order("start_time").execute().data or []
    auj_date = maintenant_local().date()
    lend_date = auj_date + timedelta(days=1)

    seances_proches = []
    for ev in toutes_seances_brutes:
        dt_ev = _parser_datetime_event(ev)
        if dt_ev and dt_ev.date() in [auj_date, lend_date]:
            seances_proches.append((ev, dt_ev))

    if seances_proches:
        for ev, dt_ev in seances_proches:
            titre_ev = ev.get("title", "Séance")
            date_str = dt_ev.strftime("%d/%m/%Y à %H:%M")
            nom_j = dict_athletes_inv.get(ev.get("athlete_id"), "Tous / Équipe")
            
            with st.expander(f"🏋️ {titre_ev} — {date_str} (Athlète/Équipe: {nom_j})"):
                st.write(f"**Lieu :** {ev.get('location', 'Non spécifié')}")
                st.write(f"**Type :** {ev.get('event_type', 'training')}")
                
                # Vérification présence de ce joueur sur cette séance
                rep_ev = obtenir_reponse_evenement(ev.get("athlete_id"), ev["id"]) if ev.get("athlete_id") else None
                statut_p = (rep_ev.get("answers") or {}).get("Présence séance", "Présent") if rep_ev else "Présent"
                st.write(f"**Statut présence joueur :** {statut_p}")
    else:
        st.info("Aucune séance prévue aujourd'hui ou demain.")

    st.markdown("---")
    st.subheader("🚨 Alertes & Remontées Joueurs")
    toutes_reponses_alertes = obtenir_reponses_avec_definitions()
    alertes_count = 0
    try:
        events_list_all = supabase.table("events").select("id, title, rpe_cible").execute().data or []
    except:
        events_list_all = supabase.table("events").select("id, title").execute().data or []
    dict_rpe_cible = {e["id"]: e.get("rpe_cible", 7.0) for e in events_list_all}

    for resp in toutes_reponses_alertes[:30]:
        ans = resp.get("answers", {})
        if isinstance(ans, str):
            try: ans = json.loads(ans)
            except: ans = {}
        nom_j = next((k for k, v in dict_athletes.items() if v == resp.get("athlete_id")), "Un joueur")
        
        for qk, qv in ans.items():
            if ("blessure" in qk.lower() or "douleur" in qk.lower()) and str(qv).strip().lower() in ["oui", "yes", "1"]:
                alertes_count += 1
                st.warning(f"⚠️ **Alerte Blessure/Douleur** — {nom_j} a répondu : *{qk} : {qv}*")
        
        rpe_val = resp.get("rpe")
        ev_id = resp.get("event_id")
        if rpe_val is not None and ev_id in dict_rpe_cible:
            cible = dict_rpe_cible[ev_id]
            if abs(float(rpe_val) - float(cible)) >= 2.0:
                alertes_count += 1
                st.warning(f"⚠️ **Alerte RPE Éloigné** — {nom_j} (RPE: {rpe_val} vs Cible: {cible})")

    if alertes_count == 0:
        st.success("✅ Aucune alerte critique récente.")

    st.markdown("---")
    tab_nouvelle, tab_existantes = st.tabs(["🆕 Planifier une nouvelle séance", "📋 Séances planifiées (modifier / supprimer)"])

    with tab_nouvelle:
        noms_tries = sorted(dict_athletes.keys())
        col_a, col_b = st.columns(2)
        with col_a:
            title = st.text_input("Titre de la séance")
            event_type = st.selectbox("Type d'événement", ["training", "match"])
            athlete_sel_label = st.selectbox("Athlète concerné", ["-- Tous les athlètes --"] + noms_tries)
            location = st.text_input("Lieu")
            rpe_cible = st.number_input("🎯 RPE Cible (1-10)", min_value=1.0, max_value=10.0, value=7.0, step=0.5)

        with col_b:
            event_date = st.date_input("Date de la séance", datetime.now())
            start_time = st.time_input("Heure de début", datetime.strptime("10:00", "%H:%M").time())
            end_time = st.time_input("Heure de fin", datetime.strptime("11:30", "%H:%M").time())

        if st.button("🚀 Planifier la/les séance(s)", type="primary"):
            if not title:
                st.error("Veuillez saisir un titre.")
            else:
                if athlete_sel_label == "-- Tous les athlètes --":
                    target_ids = list(dict_athletes.values())
                else:
                    target_ids = [dict_athletes[athlete_sel_label]]

                events_to_insert = []
                dt_start = datetime.combine(event_date, start_time)
                dt_end = datetime.combine(event_date, end_time)
                for a_id in target_ids:
                    events_to_insert.append({
                        "title": title,
                        "event_type": event_type,
                        "start_time": dt_start.isoformat(),
                        "end_time": dt_end.isoformat(),
                        "location": location or "Non spécifié",
                        "athlete_id": a_id,
                        "rpe_cible": rpe_cible
                    })

                try:
                    supabase.table("events").insert(events_to_insert).execute()
                    st.success("✅ [Séance planifiée] Validé avec succès !")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erreur Supabase : {ex}")

    with tab_existantes:
        import calendar as _calendar

        st.markdown("#### 👁️ Affichage du planning (Format Français JJ/MM/AAAA)")
        tous_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []

        if not tous_events:
            st.info("Aucune séance planifiée.")
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
                st.markdown(f"<h4 style='text-align:center;'>📅 {MOIS_FR[st.session_state.cal_mois_ref.month - 1].capitalize()} {st.session_state.cal_mois_ref.year}</h4>", unsafe_allow_html=True)
            with c_nav3:
                if st.button("Mois suivant ▶", use_container_width=True):
                    ref = st.session_state.cal_mois_ref
                    st.session_state.cal_mois_ref = (ref.replace(day=28) + timedelta(days=4)).replace(day=1)
                    st.rerun()

            annee, mois = st.session_state.cal_mois_ref.year, st.session_state.cal_mois_ref.month
            semaines = _calendar.monthcalendar(annee, mois)

            cols_header = st.columns(7)
            for c, jl in zip(cols_header, JOURS_FR):
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
                    c.markdown(f"<div style='{style_jour}'>{jour_num:02d}/{mois:02d}/{annee}</div>" if est_aujourdhui else f"<div style='{style_jour}'>{jour_num:02d}</div>", unsafe_allow_html=True)

                    evs_du_jour = events_par_jour.get(date_cell, [])
                    for ev in evs_du_jour[:4]:
                        nom = dict_athletes_inv.get(ev.get("athlete_id"), "?")
                        emoji_type = "⚔️" if ev.get("event_type") == "match" else "🏋️"
                        fichiers_ev = obtenir_fichiers_evenement(ev["id"])
                        pdf_icon = " 📄" if fichiers_ev else ""
                        libelle_court = f"{emoji_type}{pdf_icon} {ev.get('title', 'Séance')[:10]}"
                        if c.button(libelle_court, key=f"cal_btn_{ev['id']}", help=f"{ev.get('title')} — {nom}", use_container_width=True):
                            st.session_state.cal_event_selectionne = ev["id"]
                            st.rerun()

            st.markdown("---")
            ev_id_sel = st.session_state.cal_event_selectionne
            ev_sel = next((e for e in tous_events if e["id"] == ev_id_sel), None) if ev_id_sel else None

            if ev_sel:
                st.subheader(f"✏️ Modifier la séance : {ev_sel.get('title')}")
                ev_id = ev_sel["id"]
                
                # AFFICHAGE DE LA LISTE D'EFFECTIFS CONVOQUÉS POUR CETTE SÉANCE
                st.markdown("##### 👥 Effectif convoqué sur cette séance")
                titre_seance_courante = ev_sel.get("title")
                date_seance_courante = ev_sel.get("start_time")
                
                # Retrouver toutes les séances du même groupe (même titre + même horaire)
                memes_seances = [e for e in tous_events if e.get("title") == titre_seance_courante and e.get("start_time") == date_seance_courante]
                
                joueurs_dispos = []
                joueurs_indispos = []
                for ms in memes_seances:
                    aid_ms = ms.get("athlete_id")
                    nom_j_ms = dict_athletes_inv.get(aid_ms, "Inconnu")
                    rep_ms = obtenir_reponse_evenement(aid_ms, ms["id"])
                    ans_ms = (rep_ms.get("answers") or {}) if rep_ms else {}
                    presence_ms = ans_ms.get("Présence séance", "Présent")
                    blessure_ms = ans_ms.get("Blessure / douleur empêchant de s'entraîner ?", "Non")
                    
                    if presence_ms in ["Présent", ""] and str(blessure_ms).lower() not in ["oui", "yes", "1"]:
                        joueurs_dispos.append(nom_j_ms)
                    else:
                        joueurs_indispos.append(f"{nom_j_ms} ({presence_ms} / Blessé: {blessure_ms})")

                col_ef1, col_ef2 = st.columns(2)
                with col_ef1:
                    st.markdown("**✅ Joueurs disponibles :**")
                    if joueurs_dispos:
                        for jd in joueurs_dispos:
                            st.markdown(f"- {jd}")
                    else:
                        st.caption("Aucun joueur disponible.")
                with col_ef2:
                    st.markdown("**🛑 Joueurs indisponibles (absents / blessés) :**")
                    if joueurs_indispos:
                        for ji in joueurs_indispos:
                            st.markdown(f"<span style='color: #93a0bd; text-decoration: line-through;'>- {ji}</span>", unsafe_allow_html=True)
                    else:
                        st.caption("Aucun joueur indisponible.")

                st.markdown("---")
                try:
                    dt_start_existing = datetime.fromisoformat(ev_sel.get("start_time").replace("Z", "+00:00"))
                    dt_end_existing = datetime.fromisoformat(ev_sel.get("end_time").replace("Z", "+00:00"))
                except:
                    dt_start_existing, dt_end_existing = datetime.now(), datetime.now()

                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    edit_title = st.text_input("Titre", value=ev_sel.get("title", ""), key=f"edit_title_{ev_id}")
                    edit_type = st.selectbox("Type", ["training", "match"], index=0 if ev_sel.get("event_type") != "match" else 1, key=f"edit_type_{ev_id}")
                    edit_location = st.text_input("Lieu", value=ev_sel.get("location", ""), key=f"edit_loc_{ev_id}")
                with c_e2:
                    edit_date = st.date_input("Date", value=dt_start_existing.date(), key=f"edit_date_{ev_id}")
                    edit_start = st.time_input("Heure de début", value=dt_start_existing.time(), key=f"edit_start_{ev_id}")
                    edit_end = st.time_input("Heure de fin", value=dt_end_existing.time(), key=f"edit_end_{ev_id}")

                afficher_fichiers_evenement(ev_id, key_prefix=f"coach_ev_{ev_id}")

                c_b1, c_b2, c_b3 = st.columns(3)
                with c_b1:
                    if st.button("💾 Enregistrer", type="primary", key=f"save_ev_{ev_id}"):
                        maj = {
                            "title": edit_title,
                            "event_type": edit_type,
                            "location": edit_location or "Non spécifié",
                            "start_time": datetime.combine(edit_date, edit_start).isoformat(),
                            "end_time": datetime.combine(edit_date, edit_end).isoformat(),
                        }
                        supabase.table("events").update(maj).eq("id", ev_id).execute()
                        st.success("✅ [Séance mise à jour] Validé avec succès !")
                        st.rerun()
                with c_b2:
                    if st.button("❌ Supprimer", type="primary", key=f"del_ev_{ev_id}"):
                        supabase.table("events").delete().eq("id", ev_id).execute()
                        st.session_state.cal_event_selectionne = None
                        st.success("✅ [Séance supprimée] Validé avec succès !")
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
        dt_obj = _parser_datetime_event(ev)
        date_str = dt_obj.strftime("%d/%m/%Y à %H:%M") if dt_obj else ""
        ev_ath_id = ev.get("athlete_id")
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
            selected_event_label = st.selectbox("📌 Choisir la séance :", list(dict_events.keys()), key="sel_evt_pdf_up")
            selected_event = dict_events[selected_event_label]
            session_title = st.text_input("Nom du document / Titre du PDF :", value=selected_event.get("title", ""), key="inp_titre_pdf")
            description = st.text_area("Instructions :", key="inp_desc_pdf")
            uploaded_file = st.file_uploader("Fichier PDF ou Image", type=["pdf", "png", "jpg", "jpeg"], key="up_pdf_file")

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
                    st.success("✅ [PDF envoyé] Validé avec succès !")
                    st.rerun()

    with tab_list:
        st.subheader("📚 Documents déjà publiés sur les séances")
        files_db = supabase.table("session_files").select("*").order("created_at", desc=True).execute().data or []
        if not files_db:
            st.info("Aucun document publié.")
        else:
            for f in files_db:
                f_id = f.get("id")
                ev_id = f.get("event_id")
                ev_info = dict_events_info.get(ev_id, {"title": "Séance globale", "date": ""})
                with st.expander(f"📄 📄 {f.get('title')} — Séance : {ev_info['title']} ({ev_info['date']})"):
                    st.write(f"**Fichier :** `{f.get('file_name')}`")
                    f_url = f.get("file_url", "")
                    if f_url.startswith("data:"):
                        st.download_button("💾 📄 Télécharger / Voir le document (PDF)", data=base64.b64decode(f_url.split(",")[1]), file_name=f.get('file_name', 'document.pdf'), key=f"dl_doc_{f_id}")
                    else:
                        st.markdown(f"[🔗 Ouvrir / Consulter le document]({f_url})")
                    if st.button("❌ Supprimer ce document", key=f"del_doc_btn_{f_id}"):
                        supabase.table("session_files").delete().eq("id", f_id).execute()
                        st.success("✅ Document supprimé.")
                        st.rerun()

    with tab_gps:
        st.subheader("🛰️ Importer un rapport GPS (fichier Excel / CSV)")
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

                    st.dataframe(pd.DataFrame(apercu), use_container_width=True)

                    if st.button("💾 Importer ce rapport GPS", type="primary", key="btn_import_gps", disabled=(len(noms_reconnus) == 0)):
                        selected_event = dict_events[gps_event_label]
                        with st.spinner("Import en cours..."):
                            res = enregistrer_rapport_gps(selected_event["id"], [dict(l) for l in lignes], dict_athletes)

                        if res["inseres"] > 0:
                            st.success("✅ [Rapport GPS envoyé] Validé avec succès !")
                        else:
                            st.error("❌ Erreur lors de l'enregistrement.")

# =====================================================================
# PAGE : QUESTIONNAIRES
# =====================================================================
elif menu == "📝 Questionnaires":
    st.header("📝 Gestion complète des Questionnaires")
    tab_creer, tab_gerer, tab_envoyer, tab_repondre, tab_rpe_obligatoire = st.tabs([
        "🆕 Créer un modèle", "⚙️ Modifier / Supprimer", "📩 Assigner", "✍️ Saisie manuelle", "🚫 RPE obligatoire"
    ])

    with tab_creer:
        q_title = st.text_input("Titre du questionnaire", key="inp_titre_q_new")
        q_type_sel = st.selectbox("Type", ["Pre-Event (Wellness)", "Post-Event (RPE)"], key="sel_type_q_new")
        q_type = "pre_event" if "Pre" in q_type_sel else "post_event"
        if "questions_draft" not in st.session_state:
            st.session_state.questions_draft = []

        new_q_label = st.text_input("Intitulé de la question", key="inp_intitule_q")
        q_format = st.selectbox("Format", ["Échelle numérique", "Texte libre", "Nombre libre", "🚑 Oui/Non (blessure)"], key="sel_fmt_q")
        scale_max = st.number_input("Max", 2, 10, 5, key="num_scale_max_q") if "Échelle" in q_format else None

        if st.button("+ Ajouter la question au modèle", key="btn_add_q_draft"):
            if new_q_label:
                fmt = FORMAT_BLESSURE if "blessure" in q_format.lower() else ("scale" if "Échelle" in q_format else ("number" if "Nombre" in q_format else "text"))
                st.session_state.questions_draft.append({"label": new_q_label, "format": fmt, "scale_max": scale_max})
                st.rerun()

        for idx, q in enumerate(st.session_state.questions_draft):
            st.info(f"Q{idx+1}: {q['label']} ({q['format']}) - Max: {q.get('scale_max', '-')}")

        if st.button("💾 Enregistrer le questionnaire complet", type="primary", key="btn_save_q_model"):
            if q_title and st.session_state.questions_draft:
                supabase.table("questionnaires").insert({"title": q_title, "type": q_type, "questions": st.session_state.questions_draft}).execute()
                st.session_state.questions_draft = []
                st.success("✅ [Questionnaire créé] Validé avec succès !")
                st.rerun()

    with tab_gerer:
        st.subheader("✏️ Modifier ou Supprimer un questionnaire existant (Échelles incluses)")
        q_list_all = supabase.table("questionnaires").select("*").execute().data or []
        if not q_list_all:
            st.info("Aucun questionnaire créé.")
        else:
            dict_q_all = {q["title"]: q for q in q_list_all}
            sel_q_mod = st.selectbox("Sélectionner un questionnaire :", list(dict_q_all.keys()), key="sel_q_modify_tab")
            q_sel_obj = dict_q_all[sel_q_mod]
            q_id = q_sel_obj["id"]

            new_q_title = st.text_input("Modifier le titre :", value=q_sel_obj.get("title", ""), key=f"edit_q_title_{q_id}")
            new_q_type = st.selectbox("Modifier le type :", ["pre_event", "post_event"], index=0 if q_sel_obj.get("type") == "pre_event" else 1, key=f"edit_q_type_{q_id}")

            st.markdown("##### Questions et Échelles actuelles :")
            questions_actuelles = q_sel_obj.get("questions", [])
            updated_questions = []
            for i, q_item in enumerate(questions_actuelles):
                col_q1, col_q2, col_q3 = st.columns([2, 1, 1])
                with col_q1:
                    uq_label = st.text_input(f"Question {i+1}", value=q_item.get("label", ""), key=f"uq_lbl_{q_id}_{i}")
                with col_q2:
                    uq_fmt = st.selectbox(f"Format {i+1}", ["scale", "text", "number", FORMAT_BLESSURE], index=["scale", "text", "number", FORMAT_BLESSURE].index(q_item.get("format", "scale")) if q_item.get("format") in ["scale", "text", "number", FORMAT_BLESSURE] else 0, key=f"uq_fmt_{q_id}_{i}")
                with col_q3:
                    current_max = int(q_item.get("scale_max", 5)) if q_item.get("scale_max") else 5
                    uq_scale_max = st.number_input(f"Échelle Max {i+1}", min_value=2, max_value=10, value=current_max, key=f"uq_scale_{q_id}_{i}") if uq_fmt == "scale" else 5
                
                updated_questions.append({"label": uq_label, "format": uq_fmt, "scale_max": uq_scale_max})

            c_mg1, c_mg2 = st.columns(2)
            with c_mg1:
                if st.button("💾 Mettre à jour ce questionnaire", type="primary", key=f"btn_save_mod_q_{q_id}"):
                    supabase.table("questionnaires").update({"title": new_q_title, "type": new_q_type, "questions": updated_questions}).eq("id", q_id).execute()
                    st.success("✅ [Questionnaire modifié] Validé avec succès !")
                    st.rerun()
            with c_mg2:
                if st.button("❌ Supprimer définitivement ce questionnaire", type="primary", key=f"del_q_btn_{q_id}"):
                    supabase.table("questionnaires").delete().eq("id", q_id).execute()
                    st.success("✅ Questionnaire supprimé.")
                    st.rerun()

    with tab_envoyer:
        st.subheader("📩 Assigner un questionnaire à un joueur ou une équipe")
        q_data = supabase.table("questionnaires").select("*").execute().data or []
        a_data = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
        t_data = supabase.table("teams").select("id, name").execute().data or []
        
        if q_data:
            dict_q_obj = {q["title"]: q for q in q_data}
            dict_a = {a["full_name"]: a["id"] for a in a_data if a.get("full_name")}
            dict_t = {t["name"]: t["id"] for t in t_data if t.get("name")}
            
            sel_q_title = st.selectbox("Choisir le questionnaire :", list(dict_q_obj.keys()), key="sel_q_assign_title")
            q_obj_sel = dict_q_obj[sel_q_title]
            
            cible_assignation = st.radio("Assigner à :", ["👤 Joueurs spécifiques", "👥 Une équipe entière"], key="rad_cible_assign")
            
            sel_a = []
            sel_eq_id = None
            if cible_assignation.startswith("👤"):
                sel_a = st.multiselect("Athlète(s) concerné(s) :", list(dict_a.keys()), key="multisel_athletes_assign")
            else:
                eq_choisie = st.selectbox("Choisir l'équipe :", list(dict_t.keys()), key="sel_eq_assign")
                if eq_choisie:
                    sel_eq_id = dict_t[eq_choisie]

            timing_mode = st.radio("Moment de remplissage :", ["Avant séance", "Après séance"], key="rad_timing_assign")
            est_avant = timing_mode.startswith("Avant")
            
            if est_avant:
                minutes_avant = st.number_input("⏰ Combien de minutes AVANT la séance ?", min_value=5, max_value=1440, value=60, step=5)
                definir_minutes_avant(q_obj_sel["id"], int(minutes_avant))
                definir_type_questionnaire(q_obj_sel["id"], "pre_event")
            else:
                minutes_apres = st.number_input("⏰ Combien de minutes APRÈS la séance ?", min_value=5, max_value=1440, value=60, step=5)
                definir_minutes_apres(q_obj_sel["id"], int(minutes_apres))
                definir_type_questionnaire(q_obj_sel["id"], "post_event")

            if st.button("💾 Assigner le questionnaire", type="primary", key="btn_do_assign_q_final"):
                if cible_assignation.startswith("👤") and not sel_a:
                    st.error("Sélectionnez au moins un athlète.")
                elif not cible_assignation.startswith("👤") and not sel_eq_id:
                    st.error("Sélectionnez une équipe.")
                else:
                    if cible_assignation.startswith("👤"):
                        for name in sel_a:
                            assigner_questionnaire(q_obj_sel["id"], athlete_id=dict_a[name])
                    else:
                        assigner_questionnaire(q_obj_sel["id"], team_id=sel_eq_id)
                    st.success("✅ [Questionnaire assigné] Validé avec succès !")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 Questionnaires assignés (Gérer / Retirer)")
        assignations_db = obtenir_assignations()
        if assignations_db:
            for ass in assignations_db:
                ass_id = ass.get("id")
                q_info = ass.get("questionnaires") or {}
                p_info = ass.get("profiles") or {}
                t_info = ass.get("teams") or {}
                
                q_nom = q_info.get("title", "Questionnaire")
                q_type_moment = "Avant séance" if q_info.get("type") == "pre_event" else "Après séance"
                
                duree_str = "-"
                if q_info.get("type") == "pre_event" and q_info.get("trigger_minutes"):
                    duree_str = f"{q_info.get('trigger_minutes')} min avant"
                elif q_info.get("type") == "post_event" and q_info.get("post_window_minutes"):
                    duree_str = f"{q_info.get('post_window_minutes')} min après"

                cible_nom = p_info.get("full_name") or t_info.get("name") or "—"
                
                col_as1, col_as2 = st.columns([4, 1])
                with col_as1:
                    st.markdown(f"- **{q_nom}** assigné à **{cible_nom}** ({q_type_moment} — Délai : {duree_str})")
                with col_as2:
                    if st.button("❌ Retirer", key=f"del_ass_{ass_id}"):
                        supprimer_assignation(ass_id)
                        st.success("✅ Assignation retirée.")
                        st.rerun()
        else:
            st.caption("Aucune assignation active.")

    with tab_repondre:
        athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
        dict_athletes = {a.get("full_name"): a["id"] for a in athletes if a.get("full_name")}
        if dict_athletes:
            sel_athlete_name = st.selectbox("Athlète :", list(dict_athletes.keys()), key="sel_ath_saisie_man")
            selected_athlete_id = dict_athletes[sel_athlete_name]
            events_ath = supabase.table("events").select("id, title, start_time").eq("athlete_id", selected_athlete_id).execute().data or []
            dict_events_rep = {f"{ev.get('title')} — {ev.get('start_time','')[:16]}": ev["id"] for ev in events_ath}
            q_list = supabase.table("questionnaires").select("*").execute().data or []
            if dict_events_rep and q_list:
                sel_event_label = st.selectbox("Séance :", list(dict_events_rep.keys()), key="sel_evt_saisie_man")
                selected_event_id = dict_events_rep[sel_event_label]
                sel_q_title = st.selectbox("Questionnaire :", [q["title"] for q in q_list], key="sel_q_saisie_man")
                q_obj = next(q for q in q_list if q["title"] == sel_q_title)
                
                # Chargement des réponses existantes pour modification directe
                rep = obtenir_reponse_evenement(selected_athlete_id, selected_event_id)
                reponses_existantes = (rep.get("answers") or {}) if rep else {}
                if reponses_existantes:
                    st.info("💡 Des réponses ont déjà été données pour cette séance. Vous pouvez les modifier ci-dessous :")
                
                rendre_formulaire_questionnaire(q_obj, selected_event_id, f"manuel_{selected_athlete_id}", reponses_existantes, athlete_id=selected_athlete_id)

    with tab_rpe_obligatoire:
        st.subheader("🚫 RPE obligatoire après la séance")
        if st.session_state.get("flash_rpe"):
            st.success(st.session_state.pop("flash_rpe"))

        evs_rpe = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []
        inv_rpe = {v: k for k, v in dict_athletes.items()}

        def _lib_ev(e):
            dt_obj = _parser_datetime_event(e)
            date_fr = dt_obj.strftime("%d/%m/%Y à %H:%M") if dt_obj else ""
            return f"{e.get('title', 'Séance')} — {date_fr}" + ("  🚫 RPE retiré" if e.get("rpe_desactive") else "")

        ids_cibles = []
        if not dict_athletes or not evs_rpe:
            st.info("Aucune séance planifiée.")
        else:
            groupes_rpe = {}
            for e in evs_rpe:
                groupes_rpe.setdefault((e.get("title"), e.get("start_time")), []).append(e)
            cles = st.multiselect(
                "Séance(s) concernée(s) :", list(groupes_rpe.keys()),
                format_func=lambda k: f"{k[0]} — {(k[1] or '')[:16]} ({len(groupes_rpe[k])} joueur(s))",
                key="rpe_sel_events_groupe"
            )
            ids_cibles = [e["id"] for k in cles for e in groupes_rpe[k]]

        c_r1, c_r2 = st.columns(2)
        for colonne, valeur, libelle, message in [
            (c_r1, True, "🚫 Retirer le RPE obligatoire", "✅ RPE retiré pour {n} séance(s)."),
            (c_r2, False, "✅ Remettre le RPE obligatoire", "✅ RPE remis pour {n} séance(s)."),
        ]:
            with colonne:
                if st.button(libelle, key=f"btn_rpe_{valeur}", disabled=not ids_cibles, type="primary" if valeur else "secondary"):
                    try:
                        supabase.table("events").update({"rpe_desactive": valeur}).in_("id", ids_cibles).execute()
                        st.session_state["flash_rpe"] = message.format(n=len(ids_cibles))
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erreur : {ex}")

# =====================================================================
# PAGE : EFFECTIF
# =====================================================================
elif menu == "👥 Effectif":
    st.header("👥 Gestion des Effectifs & Athlètes")
    teams_list = supabase.table("teams").select("*").execute().data or []
    dict_teams = {t["name"]: t["id"] for t in teams_list}

    if not dict_teams:
        st.warning("Créez d'abord une équipe dans l'onglet 'Gestion des profils'.")
    else:
        eq_sel = st.selectbox("Choisir l'équipe :", list(dict_teams.keys()), key="sel_eq_effectif_page")
        eq_id = dict_teams[eq_sel]

        athletes_eq = supabase.table("profiles").select("*").eq("team_id", eq_id).eq("role", "athlete").execute().data or []
        st.markdown(f"### 📋 Joueurs de l'équipe : {eq_sel} ({len(athletes_eq)} joueurs)")

        if not athletes_eq:
            st.info("Aucun joueur dans cette équipe.")
        else:
            for ath in athletes_eq:
                aid = ath["id"]
                with st.expander(f"🏃 {ath.get('full_name', 'Nom inconnu')} (N°{ath.get('numero', '-')})"):
                    with st.form(f"form_ath_mod_{aid}"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            m_nom = st.text_input("Nom & Prénom", value=ath.get("full_name", ""))
                            m_num = st.number_input("Numéro de maillot", value=int(ath.get("numero") or 0))
                        with c2:
                            m_age = st.number_input("Âge", value=int(ath.get("age") or 18))
                            m_taille = st.number_input("Taille (cm)", value=float(ath.get("taille") or 175.0))
                        with c3:
                            m_poids = st.number_input("Poids (kg)", value=float(ath.get("poids") or 70.0))

                        if st.form_submit_button("💾 Mettre à jour le joueur", type="primary"):
                            modifier_athlete(aid, m_nom, eq_id, m_num, m_age, m_taille, m_poids)
                            st.success("✅ [Profil mis à jour] Validé avec succès !")
                            st.rerun()

# =====================================================================
# PAGE (ATHLÈTE) : SÉANCES À VENIR
# =====================================================================
elif menu == "📅 Séances à venir":
    st.header("📅 Mes séances")
    maintenant = maintenant_local()

    events_mine_raw = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
    q_all = supabase.table("questionnaires").select("*").execute().data or []
    q_pre = [q for q in q_all if q.get("type") == "pre_event"]
    q_auto = obtenir_ou_creer_rpe_auto()
    q_post_perso = [q for q in q_all if q.get("type") != "pre_event" and not (q_auto and q.get("id") == q_auto.get("id"))]
    assignations = obtenir_assignations()

    reponses_par_event = {}
    for r in obtenir_reponses_athlete(mon_id):
        ans = r.get("answers") or {}
        if isinstance(ans, str):
            try: ans = json.loads(ans)
            except: ans = {}
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
        fichiers_ev = obtenir_fichiers_evenement(ev["id"])
        pdf_badge = " 📄" if fichiers_ev else ""
        date_fr = d0.strftime("%d/%m/%Y à %H:%M")
        titre = f"{emoji}{pdf_badge} {ev.get('title', 'Séance')} — {date_fr}"
        
        with st.expander(titre, expanded=ouvert):
            if ev.get("location"):
                st.caption(f"📍 {ev['location']}")
            
            afficher_fichiers_evenement(ev["id"], key_prefix=f"av_{ev['id']}")
            reponses_deja = reponses_par_event.get(ev["id"], {})

            st.markdown("##### 📝 Questionnaire de présence & état de forme")
            presence_statut = reponses_deja.get("Présence séance")
            if not presence_statut:
                with st.form(f"form_presence_{ev['id']}"):
                    p_val = st.selectbox("Serez-vous présent à cette séance ?", ["Présent", "Absent / Blessé", "Douleur localisée"])
                    if st.form_submit_button("Valider ma présence", type="primary"):
                        enregistrer_reponse_evenement(mon_id, ev["id"], q_pre[0]["id"] if q_pre else "0", {"Présence séance": p_val})
                        st.success("✅ [Présence enregistrée] Validé avec succès !")
                        st.rerun()
            else:
                st.info(f"Statut de présence validé : **{presence_statut}**")

            st.markdown("##### 📋 Questionnaires de la séance")
            q_pre_dispo = [q for q in q_pre if questionnaire_disponible_pour(q["id"], mon_id, ev["id"], assignations)]
            
            if q_pre_dispo:
                for q in q_pre_dispo:
                    if st.button(f"📝 Répondre au questionnaire : {q.get('title')}", key=f"btn_open_q_{ev['id']}_{q['id']}"):
                        st.session_state[f"show_q_{ev['id']}_{q['id']}"] = True
                    
                    if st.session_state.get(f"show_q_{ev['id']}_{q['id']}"):
                        rendre_formulaire_questionnaire(q, ev["id"], f"pre_{ev['id']}_{q['id']}", reponses_deja)

            if maintenant >= d1 and q_auto and rpe_requis:
                if st.button("📝 Répondre au RPE post-séance", key=f"btn_open_rpe_{ev['id']}"):
                    st.session_state[f"show_rpe_{ev['id']}"] = True
                if st.session_state.get(f"show_rpe_{ev['id']}"):
                    rendre_formulaire_questionnaire(q_auto, ev["id"], f"rpe_{ev['id']}_{q_auto['id']}", reponses_deja)

    if not rpe_en_attente and not a_venir:
        st.info("Aucune séance à venir. 👌")
    if rpe_en_attente:
        st.markdown("### 🔴 RPE à remplir")
        for ev, d0, d1, rr in rpe_en_attente:
            bloc_seance(ev, d0, d1, rr, True)
    if a_venir:
        st.markdown("### 📅 À venir")
        for i, (ev, d0, d1, rr) in enumerate(a_venir):
            bloc_seance(ev, d0, d1, rr, i == 0 and not rpe_en_attente)

# =====================================================================
# PAGE (ATHLÈTE) : CALENDRIER
# =====================================================================
elif menu == "📆 Calendrier":
    import calendar as _calendar
    import html as _html

    st.header("📆 Calendrier")
    aujourdhui = maintenant_local().date()
    events_mine_raw = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
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

    ref = st.session_state.ath_cal_ref
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
            c.markdown(f"<div style='{style_jour}'>{jour_num:02d}/{ref.month:02d}/{ref.year}</div>" if date_cell == aujourdhui else f"<div style='{style_jour}'>{jour_num:02d}</div>", unsafe_allow_html=True)
            
            evs_jour = events_par_jour.get(date_cell, [])
            for ev in evs_jour[:4]:
                emoji_type = "⚔️" if ev.get("event_type") == "match" else "🏋️"
                fichiers_ev = obtenir_fichiers_evenement(ev["id"])
                pdf_icon = " 📄" if fichiers_ev else ""
                if c.button(f"{emoji_type}{pdf_icon} {ev.get('title', 'Séance')[:10]}", key=f"ath_cal_btn_{ev['id']}", help=str(ev.get("title")), use_container_width=True):
                    st.session_state.ath_cal_event = ev["id"]
                    st.rerun()

    st.markdown("---")
    ev_sel = next((e for e in events_mine_raw if e["id"] == st.session_state.ath_cal_event), None)
    if ev_sel:
        d0 = _parser_datetime_event(ev_sel)
        horaire = d0.strftime("%d/%m/%Y à %H:%M") if d0 else ""
        st.subheader(f"{ev_sel.get('title', 'Séance')} — {horaire}")
        afficher_fichiers_evenement(ev_sel["id"], key_prefix=f"cal_{ev_sel['id']}")
        
        if st.button("✖ Fermer le détail", key="ath_cal_close"):
            st.session_state.ath_cal_event = None
            st.rerun()

# =====================================================================
# PAGE (ATHLÈTE) : MES DONNÉES
# =====================================================================
elif menu == "📊 Mes données":
    st.header("📊 Mes données")
    nom_moi = profil_connecte.get("full_name") or "Moi"

    records_flat = []
    for r in obtenir_reponses_athlete(mon_id):
        ans = r.get("answers", {})
        if isinstance(ans, str):
            try: ans = json.loads(ans)
            except: ans = {}
        if isinstance(ans, dict):
            for k, v in ans.items():
                records_flat.append({"Joueur": nom_moi, "Question": str(k), "Valeur": str(v), "Date": str(r.get("submitted_at") or "")[:10]})
    df_flat = pd.DataFrame(records_flat) if records_flat else pd.DataFrame()

    gps_rows = []
    for g in obtenir_rapports_gps(athlete_id=mon_id):
        ligne = {"Séance": g.get("seance_titre", "Séance"), "Date": str(g.get("seance_date") or "")[:10]}
        for m in COLONNES_GPS_NUMERIQUES:
            val = g.get(m, 0)
            if m == "duree_secondes":
                val = round(val / 60.0, 1)
            ligne[NOMS_METRIQUES_GPS.get(m, m)] = val
        gps_rows.append(ligne)
    df_gps_mine = pd.DataFrame(gps_rows) if gps_rows else pd.DataFrame()
    colonnes_metriques = [NOMS_METRIQUES_GPS.get(m, m) for m in COLONNES_GPS_NUMERIQUES]

    tab_q, tab_g, tab_gps, tab_brut = st.tabs(["Réponses par question", "Graphique", "Les données GPS", "Données brutes"])

    with tab_q:
        if not df_flat.empty:
            st.dataframe(df_flat, use_container_width=True)
            st.download_button("📥 Exporter mes réponses (CSV)", data=df_flat.to_csv(index=False).encode("utf-8"), file_name="mes_reponses.csv", mime="text/csv", key="md_dl_rep")
        else:
            st.info("Aucune donnée.")

    with tab_g:
        if not df_flat.empty:
            df_num = df_flat.copy()
            df_num["Valeur_num"] = pd.to_numeric(df_num["Valeur"], errors="coerce")
            df_num = df_num.dropna(subset=["Valeur_num"])
            if not df_num.empty:
                q_sel = st.selectbox("Variable numérique :", sorted(df_num["Question"].unique().tolist()), key="md_q_graph")
                df_q = df_num[df_num["Question"] == q_sel].sort_values("Date")
                fig = px.line(df_q, x="Date", y="Valeur_num", markers=True, template="plotly_dark", title=f"Évolution — {q_sel}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Pas de données numériques.")

    with tab_gps:
        st.markdown("### 🛰️ Mes données & rapports GPS")
        if df_gps_mine.empty:
            st.info("Aucun rapport GPS.")
        else:
            df_gps_mine = df_gps_mine.sort_values("Date")
            metrique_g = st.selectbox("Métrique à tracer :", colonnes_metriques, key="md_gps_metrique")
            df_gps_mine["Séance (date)"] = df_gps_mine["Séance"] + " — " + df_gps_mine["Date"]
            st.plotly_chart(px.bar(df_gps_mine, x="Séance (date)", y=metrique_g, template="plotly_dark", title=metrique_g), use_container_width=True)
            st.dataframe(df_gps_mine.round(2), use_container_width=True)

    with tab_brut:
        if not df_flat.empty:
            st.dataframe(df_flat, use_container_width=True)

# =====================================================================
# PAGE : ANALYTIQUE
# =====================================================================
elif menu == "📊 Analytique":
    st.header("📊 Analytique & Suivi des Performances")

    profiles = supabase.table("profiles").select("*").execute().data or []
    dict_profiles = {p["id"]: p.get("full_name", "") for p in profiles}
    dict_athletes = {p.get("full_name"): p["id"] for p in profiles if p.get("role") == "athlete"}
    teams_all = supabase.table("teams").select("*").execute().data or []
    dict_teams_an = {t["name"]: t["id"] for t in teams_all}

    mode_analyse = st.radio("Analyser :", ["👤 Un joueur", "👥 Une équipe"], horizontal=True, key="rad_mode_analytique")
    
    periode_filtre = st.selectbox("Filtrer par période :", ["Toutes les périodes", "Semaine spécifique", "Mois spécifique", "Année spécifique"])
    
    scope_joueurs = []
    is_team_mode = False

    if mode_analyse == "👤 Un joueur":
        j = st.selectbox("Joueur :", sorted(dict_athletes.keys()), key="sel_j_analytique")
        scope_joueurs = [j] if j else []
    else:
        eq = st.selectbox("Équipe :", sorted(dict_teams_an.keys()), key="sel_eq_analytique")
        if eq:
            tid = dict_teams_an[eq]
            scope_joueurs = [p.get("full_name") for p in profiles if p.get("team_id") == tid and p.get("full_name")]
            is_team_mode = True

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
            records_flat.append({"Joueur": str(nom), "Question": str(k), "Valeur": str(v), "Date": r.get("submitted_at","")[:10], "athlete_id": r.get("athlete_id"), "event_id": r.get("event_id")})

    df_flat = pd.DataFrame(records_flat) if records_flat else pd.DataFrame()
    if not df_flat.empty:
        df_flat = df_flat[df_flat["Joueur"].isin(scope_joueurs)]
        if periode_filtre != "Toutes les périodes":
            df_flat["Date_dt"] = pd.to_datetime(df_flat["Date"], errors="coerce")
            now = datetime.now()
            if periode_filtre == "Semaine spécifique":
                df_flat = df_flat[df_flat["Date_dt"] >= (now - timedelta(days=7))]
            elif periode_filtre == "Mois spécifique":
                df_flat = df_flat[df_flat["Date_dt"].dt.month == now.month]
            elif periode_filtre == "Année spécifique":
                df_flat = df_flat[df_flat["Date_dt"].dt.year == now.year]

    tab_q, tab_g, tab_seance, tab_gps, tab_brut = st.tabs([
        "Réponses par question", "Graphique", "Séance", "Les données GPS", "Données brutes"
    ])

    with tab_q:
        if not df_flat.empty:
            st.markdown("### 📋 Réponses par question (numériques, textuelles et blessures)")
            st.dataframe(df_flat[["Joueur", "Question", "Valeur", "Date"]], use_container_width=True)
            st.download_button("📥 Exporter ces réponses (CSV)", data=df_flat[["Joueur", "Question", "Valeur", "Date"]].to_csv(index=False).encode('utf-8'), file_name="reponses_par_question.csv", mime="text/csv")
        else:
            st.info("Aucune donnée.")

    with tab_g:
        if not df_flat.empty:
            df_num = df_flat.copy()
            df_num["Valeur_num"] = pd.to_numeric(df_num["Valeur"], errors="coerce")
            df_num = df_num.dropna(subset=["Valeur_num"])
            if not df_num.empty:
                variables_dispo = df_num["Question"].unique().tolist()
                vars_sel = st.multiselect("Choisir une ou plusieurs données à afficher :", variables_dispo, default=variables_dispo[:1])
                if vars_sel:
                    df_filtered = df_num[df_num["Question"].isin(vars_sel)]
                    fig = px.line(df_filtered, x="Date", y="Valeur_num", color="Question", markers=True, template="plotly_dark", title="Évolution multi-données")
                    st.plotly_chart(fig, use_container_width=True)
                    st.download_button("📥 Exporter les données du graphique (CSV)", data=df_filtered.to_csv(index=False).encode('utf-8'), file_name="graphique_donnees.csv", mime="text/csv")
            else:
                st.info("Pas de données numériques.")
        else:
            st.info("Aucune donnée.")

    with tab_seance:
        st.markdown("### 🏋️ Données complètes de la séance (GPS, RPE & Questionnaires)")
        all_events_an = supabase.table("events").select("id, title, start_time").execute().data or []
        if all_events_an:
            dict_ev_an = {f"{e.get('title')} — {(e.get('start_time') or '')[:16]}": e["id"] for e in all_events_an}
            sel_ev_label_an = st.selectbox("Choisir une séance :", list(dict_ev_an.keys()), key="sel_ev_an_complet")
            sel_ev_id_an = dict_ev_an[sel_ev_label_an]

            gps_seance = obtenir_rapports_gps(event_id=sel_ev_id_an)
            if gps_seance:
                st.markdown("##### 🛰️ Données GPS")
                df_gps_s = pd.DataFrame(gps_seance)
                df_gps_s["Nom_Joueur"] = df_gps_s["athlete_id"].map(dict_profiles)
                if is_team_mode:
                    df_gps_s = df_gps_s[df_gps_s["Nom_Joueur"].isin(scope_joueurs)]
                else:
                    df_gps_s = df_gps_s[df_gps_s["Nom_Joueur"].isin(scope_joueurs)]
                st.dataframe(df_gps_s, use_container_width=True)
            else:
                st.info("Aucun rapport GPS pour cette séance.")

            st.markdown("##### 📝 Réponses aux questionnaires & RPE de la séance")
            if not df_flat.empty:
                df_seance_resp = df_flat[df_flat["event_id"] == sel_ev_id_an]
                if not df_seance_resp.empty:
                    st.dataframe(df_seance_resp[["Joueur", "Question", "Valeur", "Date"]], use_container_width=True)
                    st.download_button("📥 Exporter les données de cette séance (CSV)", data=df_seance_resp[["Joueur", "Question", "Valeur", "Date"]].to_csv(index=False).encode('utf-8'), file_name="donnees_seance.csv", mime="text/csv")
                else:
                    st.info("Aucune réponse de questionnaire pour cette séance.")
        else:
            st.info("Aucune séance disponible.")

    with tab_gps:
        st.markdown("### 🛰️ Données & Rapports GPS")
        gps_all = obtenir_rapports_gps()
        gps_rows = []
        for g in gps_all:
            ligne = {
                "Joueur": dict_profiles.get(g.get("athlete_id")) or "Athlète inconnu",
                "Séance": g.get("seance_titre", "Séance"),
                "Date": str(g.get("seance_date") or "")[:10],
            }
            for m in COLONNES_GPS_NUMERIQUES:
                val = g.get(m, 0)
                if m == "duree_secondes":
                    val = round(val / 60.0, 1)
                ligne[NOMS_METRIQUES_GPS.get(m, m)] = val
            gps_rows.append(ligne)
        df_gps_tous = pd.DataFrame(gps_rows) if gps_rows else pd.DataFrame()
        colonnes_metriques = [NOMS_METRIQUES_GPS.get(m, m) for m in COLONNES_GPS_NUMERIQUES]

        df_gps_all = df_gps_tous[df_gps_tous["Joueur"].isin(scope_joueurs)].copy() if not df_gps_tous.empty else pd.DataFrame()

        if df_gps_all.empty:
            st.info("Aucun rapport GPS pour cette sélection.")
        else:
            metrique_g = st.selectbox("Métrique à tracer :", colonnes_metriques, key="sel_metrique_gps_ind")
            df_gps_all["Séance (date)"] = df_gps_all["Séance"] + " — " + df_gps_all["Date"]
            
            st.plotly_chart(px.bar(df_gps_all, x="Séance (date)", y=metrique_g, color="Joueur" if not is_team_mode else None, barmode="group",
                                   template="plotly_dark", title=metrique_g), use_container_width=True)
            
            st.markdown("##### Données brutes GPS")
            st.dataframe(df_gps_all.round(2), use_container_width=True)
            st.download_button("📥 Exporter les données GPS (CSV)", data=df_gps_all.round(2).to_csv(index=False).encode('utf-8'), file_name="donnees_gps.csv", mime="text/csv")

    with tab_brut:
        st.markdown("### 📋 Données brutes (sans identifiants techniques)")
        if not df_flat.empty:
            df_brut_clean = df_flat[["Joueur", "Question", "Valeur", "Date"]]
            st.dataframe(df_brut_clean, use_container_width=True)
            st.download_button("📥 Exporter les données brutes (CSV)", data=df_brut_clean.to_csv(index=False).encode('utf-8'), file_name="donnees_brutes.csv", mime="text/csv")
        else:
            st.info("Aucune donnée brute.")

# =====================================================================
# PAGE : GESTION DES PROFILS
# =====================================================================
elif menu == "⚙️ Gestion des profils":
    st.header("⚙️ Gestion des Profils, Équipes & Comptes")
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
                modifier_athlete(ath_id, upd_name, new_t_id)
                st.success("✅ [Profil mis à jour] Validé avec succès !")
                st.rerun()

    with tab_teams:
        st.subheader("🛡️ Gérer, modifier les équipes et ses joueurs")
        teams_list = supabase.table("teams").select("*").execute().data or []
        
        st.markdown("##### ➕ Créer une nouvelle équipe")
        new_t = st.text_input("Nom de la nouvelle équipe", key="input_create_team_mgt")
        if st.button("Créer l'équipe", type="primary"):
            if new_t:
                creer_equipe(new_t)
                st.success("✅ [Équipe créée] Validé avec succès !")
                st.rerun()

        if teams_list:
            st.markdown("---")
            dict_teams_mgt = {t["name"]: t for t in teams_list}
            sel_t_mgt = st.selectbox("Sélectionner l'équipe à gérer :", list(dict_teams_mgt.keys()), key="sel_team_mgt_box")
            t_obj = dict_teams_mgt[sel_t_mgt]
            t_id = t_obj["id"]

            renamed_t = st.text_input("Modifier le nom de l'équipe :", value=t_obj["name"], key=f"rename_team_inp_{t_id}")
            if st.button("💾 Enregistrer le nouveau nom", key=f"btn_save_rename_eq_{t_id}"):
                supabase.table("teams").update({"name": renamed_t}).eq("id", t_id).execute()
                st.success("✅ Équipe renommée !")
                st.rerun()

    with tab_comptes:
        st.subheader("🔑 Créer un compte (Athlète uniquement - Coach sur Supabase)")
        with st.form("form_creer_compte_mgt"):
            c1, c2 = st.columns(2)
            with c1:
                new_email = st.text_input("E-mail")
                new_password = st.text_input("Mot de passe", type="password")
            with c2:
                new_full_name = st.text_input("Nom complet")
                teams_data = supabase.table("teams").select("*").execute().data or []
                dict_teams_cpt = {t["name"]: t["id"] for t in teams_data}
                new_team = st.selectbox("Équipe", ["Aucune"] + list(dict_teams_cpt.keys()))

            if st.form_submit_button("🚀 Créer le compte athlète", type="primary"):
                if new_email and new_password and new_full_name:
                    t_id = dict_teams_cpt.get(new_team) if new_team != "Aucune" else None
                    ok, msg = creer_compte(new_email, new_password, new_full_name, "athlete", t_id)
                    if ok: 
                        st.success("✅ [Compte créé] Validé avec succès !")
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
            st.success("✅ [Fichier audio généré] Validé avec succès !")
            st.audio(audio_data, format="audio/wav")
            st.download_button("💾 Télécharger (.WAV)", data=audio_data, file_name="test_bips.wav", mime="audio/wav", use_container_width=True, key="dl_wav_audio")
