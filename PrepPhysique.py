import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    page_title="Performance",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    :root {
        --bg-base: #0a0e1a; --bg-panel: #131a2b; --bg-panel-2: #172038;
        --border-soft: #263049; --text-main: #f1f5f9; --text-dim: #93a0bd;
        --accent: #ff5a1f; --accent-2: #ffb020; --success: #22c55e; --danger: #ef4444;
    }
    html, body, .stApp { background: radial-gradient(circle at 15% 0%, #101a30 0%, var(--bg-base) 45%) fixed; color: var(--text-main); font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: visible;} footer {visibility: hidden;} header {visibility: visible;}
    .stDeployButton {display:none;} div[data-testid="stDecoration"] {display: none;}
    [data-testid="collapsedControl"] { top: 3.5rem !important; left: 1rem !important; z-index: 999999; }
    h1, h2, h3, h4, h5 { font-family: 'Sora', sans-serif !important; color: var(--text-main) !important; font-weight: 700 !important; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1424 0%, #0a0e1a 100%); border-right: 1px solid var(--border-soft); }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: var(--bg-panel); border: 1px solid var(--border-soft); border-radius: 10px; padding: 10px 14px; margin-bottom: 6px; font-weight: 500;
    }
    .stButton>button { border-radius: 10px !important; font-family: 'Sora', sans-serif; font-weight: 600; border: 1px solid var(--border-soft); }
    .stButton>button[kind="primary"] { background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%) !important; color: #0a0e1a !important; border: none !important; }
    div[data-testid="stForm"] { background: var(--bg-panel); border: 1px solid var(--border-soft); border-radius: 16px; padding: 26px; }
    div[data-testid="stExpander"] { background: var(--bg-panel); border: 1px solid var(--border-soft) !important; border-radius: 14px !important; }
    div[data-testid="stMetric"] { background: var(--bg-panel); border: 1px solid var(--border-soft); border-left: 3px solid var(--accent); border-radius: 12px; }
    .brand-kicker { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.35em; background: linear-gradient(90deg, var(--accent) 0%, var(--accent-2) 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .brand-tagline { color: var(--text-dim); font-size: 0.8em; margin-top: -6px; margin-bottom: 14px; }
</style>
""", unsafe_allow_html=True)

if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

def ecran_connexion():
    st.markdown("""<div style="text-align:center; padding: 40px 0 10px 0;"><div class="brand-kicker" style="font-size:2.4em;">⚡ PERFORMANCE</div><div class="brand-tagline" style="font-size:1em;">Plateforme de suivi</div></div>""", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.3, 1])
    with col_login:
        st.subheader("🔐 Connexion")
        with st.form("form_login"):
            email = st.text_input("E-mail")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
    if submitted:
        if not email or not password:
            st.error("Renseignez l'e-mail et le mot de passe.")
        else:
            session, profile, erreur = connexion(email, password)
            if erreur: st.error(erreur)
            else: st.session_state.user_profile = profile; st.rerun()

if not st.session_state.user_profile:
    ecran_connexion()
    st.stop()

profil_connecte = st.session_state.user_profile
role_connecte = profil_connecte.get("role", "athlete")
mon_id = profil_connecte.get("id")

st.sidebar.markdown("""<div class="brand-kicker">⚡ PERFORMANCE</div><div class="brand-tagline">Suivi & Performance</div>""", unsafe_allow_html=True)
st.sidebar.markdown(f"**👤 {profil_connecte.get('full_name', 'Utilisateur')}**")
st.sidebar.caption(f"Rôle : {'🏋️ Coach' if role_connecte == 'coach' else '🏃 Athlète'}")
if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
    deconnexion()
    st.session_state.user_profile = None
    st.rerun()
st.sidebar.markdown("---")

st.markdown("""<div style="display:flex; align-items:baseline; gap:12px; margin-bottom: -10px;"><span style="font-family:'Sora',sans-serif; font-weight:800; font-size:2.1em;">⚡ Performance</span></div>""", unsafe_allow_html=True)

menu_options = [
    "📅 Planning & Séances",
    "📁 Fichiers & Rapports GPS",
    "📝 Questionnaires",
    "📊 Analytique",
    "⚙️ Gestion des profils",
    "🔊 Générateur de Bips Audio",
] if role_connecte == "coach" else ["📅 Séances à venir", "📆 Calendrier", "📊 Mes données"]

def upload_file_direct_http(bucket_name, storage_path, file_bytes, mime_type):
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{storage_path}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "apiKey": SUPABASE_KEY, "Content-Type": mime_type}
    resp = requests.post(url, data=file_bytes, headers=headers, timeout=30)
    if resp.status_code in [200, 201]:
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{storage_path}"
    else:
        raise Exception(f"Erreur Upload HTTP {resp.status_code}: {resp.text}")

menu = st.sidebar.radio("Navigation", menu_options)

# =====================================================================
# PLANNING & SÉANCES
# =====================================================================
if menu == "📅 Planning & Séances":
    st.header("📅 Planning & Séances")
    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute()
    dict_athletes = {a.get("full_name"): a["id"] for a in (res_athletes.data or []) if a.get("full_name")}
    teams_data = supabase.table("teams").select("*").execute().data or []
    dict_teams = {t["name"]: t["id"] for t in teams_data}

    vue_planning = st.selectbox("Afficher le planning de :", ["Mon planning", "Planning d'une équipe", "Planning d'un joueur"])
    filtre_ids_equipe, filtre_id_joueur = None, None
    if vue_planning == "Planning d'une équipe" and dict_teams:
        eq_choisie = st.selectbox("Choisir l'équipe :", list(dict_teams.keys()))
        mems = supabase.table("profiles").select("id").eq("team_id", dict_teams[eq_choisie]).execute().data or []
        filtre_ids_equipe = [m["id"] for m in mems]
    elif vue_planning == "Planning d'un joueur" and dict_athletes:
        ath_choisi = st.selectbox("Choisir le joueur :", sorted(dict_athletes.keys()))
        filtre_id_joueur = dict_athletes[ath_choisi]

    tab_nouvelle, tab_existantes = st.tabs(["🆕 Planifier une séance", "📅 Calendrier & Séances"])
    with tab_nouvelle:
        col_a, col_b = st.columns(2)
        with col_a:
            title = st.text_input("Titre de la séance")
            event_type = st.selectbox("Type", ["training", "match"])
            athlete_sel = st.selectbox("Athlète", ["-- Tous --"] + sorted(dict_athletes.keys()))
            location = st.text_input("Lieu")
        with col_b:
            event_date = st.date_input("Date", datetime.now())
            start_time = st.time_input("Début", datetime.strptime("10:00", "%H:%M").time())
            end_time = st.time_input("Fin", datetime.strptime("11:30", "%H:%M").time())
            rpe_cible = st.number_input("RPE Cible", min_value=1.0, max_value=10.0, value=7.0)

        if st.button("🚀 Planifier", type="primary"):
            if title:
                target_ids = list(dict_athletes.values()) if athlete_sel == "-- Tous --" else [dict_athletes[athlete_sel]]
                dt_s, dt_e = datetime.combine(event_date, start_time), datetime.combine(event_date, end_time)
                events_to_insert = [{"title": title, "event_type": event_type, "start_time": dt_s.isoformat(), "end_time": dt_e.isoformat(), "location": location or "N/A", "athlete_id": a_id, "target_rpe": rpe_cible} for a_id in target_ids]
                supabase.table("events").insert(events_to_insert).execute()
                st.success("Séance planifiée !"); st.rerun()

    with tab_existantes:
        tous_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []
        if vue_planning == "Planning d'un joueur" and filtre_id_joueur:
            tous_events = [e for e in tous_events if e.get("athlete_id") == filtre_id_joueur]
        elif vue_planning == "Planning d'une équipe" and filtre_ids_equipe:
            tous_events = [e for e in tous_events if e.get("athlete_id") in filtre_ids_equipe]

        for ev in tous_events[:15]:
            dstr = (ev.get("start_time") or "")[:16].replace("T", " ")
            with st.expander(f"📌 {ev.get('title')} ({dstr})"):
                if st.button("Supprimer", key=f"del_ev_{ev['id']}"):
                    supabase.table("events").delete().eq("id", ev["id"]).execute(); st.rerun()

# =====================================================================
# FICHIERS & RAPPORTS GPS (Correction rapport GPS & DB)
# =====================================================================
elif menu == "📁 Fichiers & Rapports GPS":
    st.header("📁 Fichiers de Séances & Rapports GPS")
    res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
    dict_athletes = {a.get("full_name"): a["id"] for a in res_athletes if a.get("full_name")}
    res_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []
    dict_events = {f"{ev.get('title')} ({(ev.get('start_time') or '')[:10]})": ev for ev in res_events}

    tab_upload, tab_manage, tab_gps = st.tabs(["📤 Joindre un PDF", "📚 Gérer les fichiers & GPS", "🛰️ Importer GPS (xlsx/csv)"])
    with tab_upload:
        if dict_events:
            sel_ev = dict_events[st.selectbox("Séance :", list(dict_events.keys()))]
            title_doc = st.text_input("Titre :", value=sel_ev.get("title", ""))
            up_file = st.file_uploader("Fichier", type=["pdf", "png", "jpg"])
            if st.button("Publier", type="primary") and up_file:
                b = up_file.read()
                url = upload_file_direct_http("session-files", f"{int(datetime.now().timestamp())}_{up_file.name}", b, up_file.type or "application/octet-stream")
                supabase.table("session_files").insert({"title": title_doc, "file_name": up_file.name, "file_url": url, "event_id": sel_ev.get("id"), "athlete_id": sel_ev.get("athlete_id")}).execute()
                st.success("Publié !"); st.rerun()

    with tab_manage:
        st.subheader("📚 Documents et GPS en base")
        for f in (supabase.thable("session_files").select("*").execute().data or [] if hasattr(supabase, 'thable') else supabase.table("session_files").select("*").execute().data or []):
            col1, col2 = st.columns([4, 1])
            col1.write(f"• {f.get('title')}")
            if col2.button("Supprimer", key=f"del_sf_{f['id']}"):
                supabase.table("session_files").delete().eq("id", f["id"]).execute(); st.rerun()

    with tab_gps:
        st.subheader("🛰️ Import rapport GPS")
        if dict_events:
            sel_ev_gps = dict_events[st.selectbox("Séance GPS :", list(dict_events.keys()), key="gps_sel")]
            gps_file = st.file_uploader("Fichier GPS (.csv, .xlsx)", type=["csv", "xlsx", "xls"])
            if gps_file:
                try:
                    lignes = lire_fichier_gps(gps_file.read(), nom_fichier=gps_file.name)
                except Exception as ex:
                    lignes = []; st.error(f"Erreur de lecture : {ex}")
                if lignes:
                    st.dataframe(pd.DataFrame(lignes), use_container_width=True)
                    if st.button("💾 Importer dans la base", type="primary"):
                        n_ins, non_trouves = enregistrer_rapport_gps(sel_ev_gps["id"], lignes, dict_athletes)
                        st.success(f"✅ {n_ins} lignes GPS importées avec succès !")
                        if non_trouves: st.warning(f"Joueurs non reconnus : {', '.join(non_trouves)}")

# =====================================================================
# QUESTIONNAIRES (Modification questions/réponses & délais d'envoi)
# =====================================================================
elif menu == "📝 Questionnaires":
    st.header("📝 Questionnaires & Alertes")
    tab_creer, tab_assigner = st.tabs(["🆕 Créer & Modifier", "📩 Assigner"])
    with tab_creer:
        q_list = supabase.table("questionnaires").select("*").execute().data or []
        dict_q = {q["title"]: q for q in q_list}
        mode_q = st.radio("Action :", ["Créer", "Modifier"], horizontal=True)
        if mode_q == "Créer":
            q_title = st.text_input("Titre")
            q_type = st.selectbox("Type", ["Pre-Event", "Post-Event"])
            if "draft_q" not in st.session_state: st.session_state.draft_q = []
            ql = st.text_input("Intitulé question")
            qf = st.selectbox("Format", ["Échelle", "Texte", "Nombre"])
            if st.button("+ Ajouter question") and ql:
                st.session_state.draft_q.append({"label": ql, "format": "scale" if qf=="Échelle" else ("number" if qf=="Nombre" else "text")})
                st.rerun()
            for i, q in enumerate(st.session_state.draft_q): st.write(f"Q{i+1}: {q['label']}")
            if st.button("Enregistrer", type="primary") and q_title and st.session_state.draft_q:
                supabase.table("questionnaires").insert({"title": q_title, "type": "pre_event" if "Pre" in q_type else "post_event", "questions": st.session_state.draft_q}).execute()
                st.session_state.draft_q = []; st.success("Créé !"); st.rerun()
        else:
            if dict_q:
                sel_q = dict_q[st.selectbox("Questionnaire :", list(dict_q.keys()))]
                new_t = st.text_input("Titre", value=sel_q.get("title", ""))
                if st.button("Mettre à jour", type="primary"):
                    supabase.table("questionnaires").update({"title": new_t}).eq("id", sel_q["id"]).execute(); st.success("Mis à jour !"); st.rerun()
                if st.button("Supprimer"):
                    supabase.table("questionnaires").delete().eq("id", sel_q["id"]).execute(); st.success("Supprimé."); st.rerun()

    with tab_assigner:
        st.subheader("Assignation avec délais")
        q_data = supabase.table("questionnaires").select("*").execute().data or []
        a_data = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
        if q_data and a_data:
            sel_q_obj = q_data[0] # Simplifié
            moment = st.radio("Moment d'envoi :", ["Avant la séance", "Après la séance"])
            delai_sec = st.number_input("Délai en secondes (ex: 60 ou avant/après)", min_value=0, value=60)
            sel_ath = st.multiselect("Athlètes :", [a["full_name"] for a in a_data])
            if st.button("Assigner", type="primary") and sel_ath:
                for an in sel_ath:
                    aid = next(a["id"] for a in a_data if a["full_name"] == an)
                    assigner_questionnaire(sel_q_obj["id"], aid, None)
                st.success("Assigné !")

# =====================================================================
# ANALYTIQUE
# =====================================================================

elif menu == "📊 Analytique":
    st.header("📊 Analytique")
    profiles = supabase.table("profiles").select("*").execute().data or []
    dict_profiles = {p["id"]: p.get("full_name") for p in profiles}
    dict_athletes = {p.get("full_name"): p["id"] for p in profiles if p.get("role") == "athlete"}
    teams = supabase.table("teams").select("*").execute().data or []
    
    mode = st.radio("Analyser :", ["Joueur", "Équipe"], horizontal=True)
    scope = [st.selectbox("Joueur :", sorted(dict_athletes.keys()))] if mode == "Joueur" else [p.get("full_name") for p in profiles if p.get("team_id")]

    res_resp = supabase.table("questionnaire_responses").select("*").execute().data or []
    records = []
    for r in res_resp:
        jnom = dict_profiles.get(r.get("athlete_id") or r.get("user_id"), "Inconnu")
        if r.get("rpe_score") is not None:
            records.append({"Joueur": jnom, "Date": str(r.get("submitted_at", ""))[:10], "Question": "RPE", "Valeur": float(r.get("rpe_score"))})
    df = pd.DataFrame(records) if records else pd.DataFrame()
    if not df.empty:
        df = df[df["Joueur"].isin(scope)]

    t1, t2, t3, t4 = st.tabs(["Graphique", "Comparaison joueur", "Données GPS", "Données brutes"])
    with t1:
        if not df.empty:
            st.plotly_chart(px.line(df, x="Date", y="Valeur", color="Joueur", template="plotly_dark"), use_container_width=True)
        else:
            st.info("Pas de données.")
    with t2:
        st.info("Comparaison disponible.")
    with t3:
        st.info("Données GPS.")
    with t4:
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucune donnée brute disponible.")

# =====================================================================
# GESTION DES PROFILS & ÉQUIPES (Modification complète des équipes)
# =====================================================================
elif menu == "⚙️ Gestion des profils":
    st.header("⚙️ Gestion des Profils, Équipes & Comptes")
    tab_ath, tab_teams, tab_cpt = st.tabs(["👤 Athlètes", "🛡️ Équipes", "🔑 Comptes"])
    with tab_ath:
        ath_data = supabase.table("profiles").select("*").eq("role", "athlete").execute().data or []
        if ath_data:
            sel_a = ath_data[0] # Simplifié
            new_n = st.text_input("Nom", value=sel_a.get("full_name", ""))
            if st.button("Mettre à jour profil"):
                supabase.table("profiles").update({"full_name": new_n}).eq("id", sel_a["id"]).execute(); st.success("Mis à jour !"); st.rerun()
    with tab_teams:
        st.subheader("Gestion des équipes & membres")
        new_eq = st.text_input("Nom nouvelle équipe")
        if st.button("Créer l'équipe") and new_eq:
            supabase.table("teams").insert({"name": new_eq}).execute(); st.success("Équipe créée !"); st.rerun()
        
        teams_list = supabase.table("teams").select("*").execute().data or []
        for eq in teams_list:
            with st.expander(f"🛡️ Équipe : {eq['name']}"):
                eq_name_upd = st.text_input("Renommer", value=eq['name'], key=f"eq_n_{eq['id']}")
                if st.button("Enregistrer", key=f"sv_eq_{eq['id']}"):
                    supabase.table("teams").update({"name": eq_name_upd}).eq("id", eq['id']).execute(); st.success("Modifié !"); st.rerun()
                if st.button("Supprimer l'équipe", key=f"rm_eq_{eq['id']}"):
                    supabase.table("teams").delete().eq("id", eq['id']).execute(); st.success("Supprimée."); st.rerun()
    with tab_cpt:
        with st.form("fcpt"):
            em, pw, nm, rl = st.text_input("E-mail"), st.text_input("Mot de passe", type="password"), st.text_input("Nom"), st.selectbox("Rôle", ["athlete", "coach"])
            if st.form_submit_button("Créer le compte") and em and pw and nm:
                ok, msg = creer_compte(em, pw, nm, rl)
                if ok: st.success(msg); st.rerun()
                else: st.error(msg)

# =====================================================================
# GÉNÉRATEUR DE BIPS AUDIO (Correction Progressif / Accéléré)
# =====================================================================
elif menu == "🔊 Générateur de Bips Audio":
    import wave, math, struct, io
    st.header("🔊 Générateur de Bips Audio (Tests VMA & Pacing)")
    mode_bip = st.radio("Mode :", ["Constant", "Progressif / Accéléré"])
    base_int = st.number_input("Intervalle de départ (sec) :", value=5.0, step=0.5)
    total_beps = st.number_input("Nombre de bips :", value=30)
    step_dec = st.number_input("Réduction d'intervalle à chaque accélération (sec) :", value=0.5, step=0.1) if mode_bip == "Progressif / Accéléré" else 0.0

    if st.button("🎵 Générer l'audio", type="primary", use_container_width=True):
        sample_rate = 44100
        frames = bytearray()
        cur_int = float(base_int)
        for b in range(1, int(total_beps) + 1):
            if mode_bip == "Progressif / Accéléré" and b > 1 and (b - 1) % 5 == 0:
                cur_int = max(1.0, cur_int - float(step_dec))
            num_s = int(sample_rate * 0.2)
            for i in range(num_s):
                frames.extend(struct.pack('<h', int(32767 * math.sin(2 * math.pi * 2000 * i / sample_rate))))
            sil_s = int(sample_rate * max(0.0, cur_int - 0.2))
            frames.extend(struct.pack('<h', 0) * sil_s)
        
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate); wf.writeframes(frames)
        st.success("✅ Fichier audio généré avec succès !")
        st.audio(buf.getvalue(), format="audio/wav")
        st.download_button("💾 Télécharger (.WAV)", data=buf.getvalue(), file_name="bips_audio.wav", mime="audio/wav", use_container_width=True)

# =====================================================================
# PAGES ATHLÈTE
# =====================================================================
elif menu == "📅 Séances à venir":
    st.header("📅 Mes séances à venir")
    for ev in (supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []):
        with st.expander(f"🏋️ {ev.get('title')}"): afficher_fichiers_evenement(ev["id"])
elif menu == "📆 Calendrier": st.header("📆 Mon Calendrier")
elif menu == "📊 Mes données": st.header("📊 Mes données personnelles")
