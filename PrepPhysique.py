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
import unicodedata
import re
import difflib
import wave
import math
import struct
import io
from supabase import create_client, Client

# =====================================================================
# CONFIGURATION & LOGIQUE SUPABASE / ANALYTICS
# =====================================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gedzzrwxefwycrtrgbwj.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "SUPABASE_KEY_VALUE")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

FORMAT_BLESSURE = "blessure"
COLONNES_GPS_NUMERIQUES = [
    "distance_totale_m",
    "distance_haute_intensite_m",
    "distance_haute_vitesse_m",
    "distance_sprint_m",
    "nb_accelerations",
    "nb_decelerations",
    "vmax_kmh",
    "meterage_par_minute",
    "duree_secondes"
]

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

def parse_duree_en_minutes(val_str):
    if pd.isna(val_str):
        return 0.0
    val_str = str(val_str).strip()
    if ":" in val_str:
        parts = val_str.split(":")
        try:
            if len(parts) == 3:
                return (float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])) / 60.0
            elif len(parts) == 2:
                return (float(parts[0]) * 60 + float(parts[1])) / 60.0
        except:
            return 0.0
    try:
        return float(val_str.replace(",", ".")) / 60.0 if "sec" in str(val_str).lower() else float(val_str.replace(",", "."))
    except:
        return 0.0

def lire_fichier_gps(file_bytes, nom_fichier=""):
    try:
        if nom_fichier.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes), skiprows=9, sep=None, engine='python')
        else:
            df = pd.read_excel(io.BytesIO(file_bytes), skiprows=9)
    except Exception:
        try:
            if nom_fichier.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python')
            else:
                df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            raise Exception(f"Impossible de lire le fichier : {e}")

    df.columns = [str(c).strip() for c in df.columns]
    col_player = next((c for c in df.columns if "player" in c.lower() and "name" in c.lower()), None)
    col_period = next((c for c in df.columns if "period" in c.lower() and "name" in c.lower()), None)

    if not col_player:
        for i, row in df.iterrows():
            row_str = str(row.values)
            if "Player Name" in row_str or "Player" in row_str:
                df = pd.read_csv(io.BytesIO(file_bytes), skiprows=i, sep=None, engine='python') if nom_fichier.endswith(".csv") else pd.read_excel(io.BytesIO(file_bytes), skiprows=i)
                df.columns = [str(c).strip() for c in df.columns]
                col_player = next((c for c in df.columns if "player" in c.lower() and "name" in c.lower()), None)
                col_period = next((c for c in df.columns if "period" in c.lower() and "name" in c.lower()), None)
                break

    if not col_player:
        raise Exception("Colonne 'Player Name' introuvable dans le fichier.")

    if col_period:
        df = df[df[col_period].astype(str).str.contains("session", case=False, na=False)]

    lignes_extraites = []
    for _, row in df.iterrows():
        nom_joueur = str(row.get(col_player, "")).strip()
        if not nom_joueur or nom_joueur.lower() in ["nan", "none", "nat", ""]:
            continue
            
        def get_val(possibles):
            for p in possibles:
                for c in df.columns:
                    if p.lower() in c.lower():
                        try:
                            val = float(str(row.get(c, 0)).replace(",", "."))
                            return 0.0 if pd.isna(val) else val
                        except:
                            pass
            return 0.0

        duree_brute = row.get("Duration", row.get("Time", 0))
        duree_minutes = parse_duree_en_minutes(duree_brute)

        lignes_extraites.append({
            "player_name": nom_joueur,
            "distance_totale_m": get_val(["Distance", "Total Distance"]),
            "distance_haute_intensite_m": get_val(["High Intensity", "High-Intensity", "HI Distance"]),
            "distance_haute_vitesse_m": get_val(["High Speed", "Speed Distance"]),
            "distance_sprint_m": get_val(["Sprint"]),
            "nb_accelerations": get_val(["Accel"]),
            "nb_decelerations": get_val(["Decel"]),
            "vmax_kmh": get_val(["Vmax", "Max Velocity", "Speed Max"]),
            "meterage_par_minute": get_val(["Meterage", "m/min", "Distance per minute"]),
            "duree_secondes": int(round(duree_minutes * 60))
        })
    return lignes_extraites

def _norm_nom(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s).lower()
    return " ".join(s.split())

def matcher_nom_athlete(nom_fichier, dict_athletes):
    nom_propre = _norm_nom(nom_fichier)
    if not nom_propre:
        return None
    base = {nom: _norm_nom(nom) for nom in dict_athletes}
    for nom_db, n in base.items():
        if n == nom_propre:
            return dict_athletes[nom_db]
    mots_fichier = set(nom_propre.split())
    for nom_db, n in base.items():
        if mots_fichier and mots_fichier == set(n.split()):
            return dict_athletes[nom_db]
    cle_f = " ".join(sorted(nom_propre.split()))
    meilleur, meilleur_score = None, 0.0
    for nom_db, n in base.items():
        score = difflib.SequenceMatcher(None, cle_f, " ".join(sorted(n.split()))).ratio()
        if score > meilleur_score:
            meilleur, meilleur_score = nom_db, score
    if meilleur and meilleur_score >= 0.88:
        return dict_athletes[meilleur]
    return None

def enregistrer_rapport_gps(event_id, lignes, dict_athletes):
    resultat = {"inseres": 0, "importes": [], "non_trouves": [], "erreurs": []}
    date_seance = datetime.now().isoformat()
    try:
        ev_res = supabase.table("events").select("title, start_time").eq("id", event_id).execute()
        if ev_res.data and ev_res.data[0].get("start_time"):
            date_seance = ev_res.data[0]["start_time"]
    except:
        pass

    for l in lignes:
        p_name = l.get("player_name")
        athlete_id = matcher_nom_athlete(p_name, dict_athletes)
        if not athlete_id:
            continue
        try:
            supabase.table("gps_reports").delete().eq("event_id", event_id).eq("athlete_id", athlete_id).execute()
            rec = {"event_id": event_id, "athlete_id": athlete_id, "recorded_at": date_seance}
            for col in COLONNES_GPS_NUMERIQUES:
                val = float(l.get(col, 0) or 0)
                rec[col] = int(round(val)) if col in ("nb_accelerations", "nb_decelerations", "duree_secondes") else round(val, 2)
            supabase.table("gps_reports").insert(rec).execute()
            resultat["inseres"] += 1
            resultat["importes"].append(p_name)
        except Exception as e:
            resultat["erreurs"].append(str(e))
    return resultat

def obtenir_rapports_gps(athlete_id=None, event_id=None):
    try:
        q = supabase.table("gps_reports").select("*")
        if athlete_id:
            q = q.eq("athlete_id", athlete_id)
        if event_id:
            q = q.eq("event_id", event_id)
        rapports = q.execute().data or []
    except:
        return []
    
    ids_events = list({r.get("event_id") for r in rapports if r.get("event_id")})
    events = {}
    if ids_events:
        for ev in supabase.table("events").select("id, title, start_time").in_("id", ids_events[:80]).execute().data or []:
            events[ev["id"]] = ev

    for r in rapports:
        ev = events.get(r.get("event_id"), {})
        r["seance_titre"] = ev.get("title") or "Séance"
        r["seance_date"] = ev.get("start_time") or r.get("recorded_at") or ""
    rapports.sort(key=lambda r: str(r.get("seance_date") or ""), reverse=True)
    return rapports

def connexion(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session and res.user:
            prof = supabase.table("profiles").select("*").eq("id", res.user.id).single().execute()
            return res.session, prof.data, None
    except Exception as e:
        return None, None, str(e)
    return None, None, "Identifiants invalides."

def deconnexion():
    try:
        supabase.auth.sign_out()
    except:
        pass

def creer_compte(email, password, full_name, role, team_id=None):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            data = {"id": res.user.id, "full_name": full_name, "role": role}
            if team_id:
                data["team_id"] = team_id
            supabase.table("profiles").insert(data).execute()
            return True, "Compte créé avec succès !"
    except Exception as e:
        return False, str(e)
    return False, "Erreur lors de la création."

def modifier_athlete(athlete_id, full_name, team_id=None, numero=None, age=None, taille=None, poids=None):
    try:
        data = {"full_name": full_name, "team_id": team_id}
        if numero is not None: data["numero"] = numero
        if age is not None: data["age"] = age
        if taille is not None: data["taille"] = taille
        if poids is not None: data["poids"] = poids
        supabase.table("profiles").update(data).eq("id", athlete_id).execute()
        return True
    except:
        return False

def creer_equipe(name):
    try:
        supabase.table("teams").insert({"name": name}).execute()
        return True
    except:
        return False

def obtenir_reponses_avec_definitions():
    try:
        res = supabase.table("questionnaire_responses").select("*, questionnaires(title, type)").execute()
        return res.data if res.data else []
    except:
        return []

def calculer_statut_disponibilite(profiles, responses):
    statuts = {}
    for p in profiles:
        statuts[p["id"]] = {"statut": "disponible", "raison": ""}
    return statuts

def _lire_answers(valeur):
    if isinstance(valeur, str):
        try:
            valeur = json.loads(valeur)
        except:
            return {}
    return valeur if isinstance(valeur, dict) else {}

def obtenir_reponses_athlete(athlete_id):
    try:
        return supabase.table("questionnaire_responses").select("*").eq("athlete_id", athlete_id).execute().data or []
    except:
        return []

def enregistrer_reponse_evenement(athlete_id, event_id, questionnaire_id, answers, rpe=None):
    def _maj(ligne, fusion):
        data = {"answers": fusion, "submitted_at": datetime.now().isoformat()}
        if rpe is not None:
            data["rpe"] = rpe
        supabase.table("questionnaire_responses").update(data).eq("id", ligne["id"]).execute()

    try:
        lignes = supabase.table("questionnaire_responses").select("*").eq("athlete_id", athlete_id).eq("event_id", event_id).execute().data or []
        existante = next((r for r in lignes if r.get("questionnaire_id") == questionnaire_id), None)
        if existante:
            fusion = _lire_answers(existante.get("answers"))
            fusion.update(answers)
            _maj(existante, fusion)
            return True, None

        data = {
            "athlete_id": athlete_id,
            "event_id": event_id,
            "questionnaire_id": questionnaire_id,
            "answers": answers,
            "submitted_at": datetime.now().isoformat()
        }
        if rpe is not None:
            data["rpe"] = rpe
        supabase.table("questionnaire_responses").insert(data).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def obtenir_reponse_evenement(athlete_id, event_id):
    try:
        res = supabase.table("questionnaire_responses").select("*").eq("athlete_id", athlete_id).eq("event_id", event_id).execute()
        if not res.data:
            return None
        base = dict(res.data[0])
        fusion = {}
        for r in res.data:
            fusion.update(_lire_answers(r.get("answers")))
        base["answers"] = fusion
        return base
    except:
        return None

TITRE_RPE_AUTO = "RPE Post-Séance (Auto)"
LABEL_RPE_AUTO = "Score RPE global de la séance"

def obtenir_ou_creer_rpe_auto():
    try:
        ex = supabase.table("questionnaires").select("*").eq("title", TITRE_RPE_AUTO).execute().data
        if ex:
            return ex[0]
        ins = supabase.table("questionnaires").insert({
            "title": TITRE_RPE_AUTO,
            "type": "post_event",
            "questions": [{"label": LABEL_RPE_AUTO, "format": "scale", "scale_max": 10}]
        }).execute().data
        return ins[0] if ins else None
    except:
        return None

def definir_minutes_avant(q_id, minutes):
    try:
        supabase.table("questionnaires").update({"trigger_minutes": minutes}).eq("id", q_id).execute()
    except:
        pass

def definir_minutes_apres(q_id, minutes):
    try:
        supabase.table("questionnaires").update({"post_window_minutes": minutes}).eq("id", q_id).execute()
    except:
        pass

def definir_type_questionnaire(q_id, q_type):
    try:
        supabase.table("questionnaires").update({"type": q_type}).eq("id", q_id).execute()
    except:
        pass

def assigner_questionnaire(questionnaire_id, athlete_id=None, event_id=None, team_id=None):
    try:
        data = {"questionnaire_id": questionnaire_id, "athlete_id": athlete_id, "event_id": event_id}
        if team_id:
            data["team_id"] = team_id
        supabase.table("questionnaire_assignments").insert(data).execute()
    except:
        pass

def supprimer_assignation(assignment_id):
    try:
        supabase.table("questionnaire_assignments").delete().eq("id", assignment_id).execute()
        return True
    except:
        return False

def obtenir_assignations():
    try:
        res = supabase.table("questionnaire_assignments").select("*, questionnaires(title, type, trigger_minutes, post_window_minutes), profiles(full_name), teams(name)").execute()
        return res.data if res.data else []
    except:
        try:
            return supabase.table("questionnaire_assignments").select("*").execute().data or []
        except:
            return []

def questionnaire_disponible_pour(q_id, athlete_id, event_id, assignations):
    return True

def obtenir_fichiers_evenement(event_id):
    try:
        res = supabase.table("session_files").select("*").eq("event_id", event_id).execute()
        return res.data if res.data else []
    except:
        return []

# =====================================================================
# INTERFACE STREAMLIT (APPLICATION PRINCIPALE)
# =====================================================================

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
        --bg-base: #0a0e1a; --bg-panel: #131a2b; --bg-panel-2: #172038;
        --border-soft: #263049; --text-main: #f1f5f9; --text-dim: #93a0bd;
        --accent: #ff5a1f; --accent-2: #ffb020; --accent-cyan: #22d3ee;
    }
    html, body, .stApp {
        background: radial-gradient(circle at 15% 0%, #101a30 0%, var(--bg-base) 45%) fixed;
        color: var(--text-main); font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5 { font-family: 'Sora', sans-serif !important; color: var(--text-main) !important; font-weight: 700 !important; }
    .stButton>button { border-radius: 10px !important; font-family: 'Sora', sans-serif; font-weight: 600; border: 1px solid var(--border-soft); }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%) !important; color: #0a0e1a !important; border: none !important;
    }
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background: var(--bg-panel); border: 1px solid var(--border-soft); border-radius: 16px; padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

if st.session_state.user_profile is None:
    try:
        current_session = supabase.auth.get_session()
        if current_session and current_session.user:
            prof_res = supabase.table("profiles").select("*").eq("id", current_session.user.id).single().execute()
            if prof_res.data:
                st.session_state.user_profile = prof_res.data
    except:
        pass

def ecran_connexion():
    st.markdown("""<div style="text-align:center; padding: 40px 0 10px 0;"><div style="font-size:2.4em; font-weight:800;">⚡ PERFORMANCE+</div><div style="color:#93a0bd;">Préparation physique & suivi de performance</div></div>""", unsafe_allow_html=True)
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
            if erreur:
                st.error(erreur)
            else:
                st.session_state.user_profile = profile
                st.rerun()

if not st.session_state.user_profile:
    ecran_connexion()
    st.stop()

profil_connecte = st.session_state.user_profile
role_connecte = profil_connecte.get("role", "athlete")
mon_id = profil_connecte.get("id")

st.sidebar.markdown(f"**👤 {profil_connecte.get('full_name', 'Utilisateur')}**")
st.sidebar.caption(f"Rôle : {'🏋️ Coach' if role_connecte == 'coach' else '🏃 Athlète'}")
if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
    deconnexion()
    st.session_state.user_profile = None
    st.rerun()
st.sidebar.markdown("---")

menu_options = [
    "📅 Planning & Séances", "📁 Fichiers & Rapports GPS", "📝 Questionnaires",
    "📊 Analytique", "👥 Effectif", "⚙️ Gestion des profils", "🔊 Générateur de Bips Audio"
] if role_connecte == "coach" else ["📅 Séances à venir", "📆 Calendrier", "📊 Mes données"]

menu = st.sidebar.radio("Navigation", menu_options)

def maintenant_local():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Paris")).replace(tzinfo=None)
    except:
        return datetime.now()

def _parser_datetime_event(ev, champ="start_time"):
    try:
        return datetime.fromisoformat((ev.get(champ) or "").replace("Z", "+00:00")).replace(tzinfo=None)
    except:
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
                st.download_button(f"💾 📄 {f.get('title', 'Document')} (PDF)", data=base64.b64decode(f_url.split(",")[1]), file_name=f.get("file_name", "document.pdf"), key=f"{key_prefix}_dl_{f['id']}")
            except:
                pass
        else:
            st.markdown(f"📄 📄 [{f.get('title', 'Document')}]({f_url})")

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
                except:
                    idx_defaut = None if est_rpe else 0
                ans = st.selectbox(f"{lbl} (1-{scale_max})", options, index=idx_defaut, key=f"{key_suffix}_{idx}", placeholder="Choisis une valeur")
                if ans is None:
                    valeurs_manquantes.append(lbl)
                else:
                    answers_dict[lbl] = float(ans)
                    if est_rpe: rpe_val = float(ans)
            elif fmt == "number":
                try: val_defaut = float(valeur_existante) if valeur_existante not in (None, "") else 0.0
                except: val_defaut = 0.0
                ans = st.number_input(lbl, value=val_defaut, key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = float(ans)
            elif fmt == FORMAT_BLESSURE:
                idx_defaut = 1 if str(valeur_existante).strip().lower() == "oui" else 0
                ans = st.selectbox(f"🚑 {lbl}", ["Non", "Oui"], index=idx_defaut, key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = ans
            else:
                ans = st.text_input(lbl, value=str(valeur_existante) if valeur_existante is not None else "", key=f"{key_suffix}_{idx}")
                answers_dict[lbl] = ans

        if st.form_submit_button("💾 Mettre à jour / Envoyer", type="primary"):
            if valeurs_manquantes:
                st.error("Choisis une valeur pour : " + ", ".join(valeurs_manquantes))
            else:
                ok, err = enregistrer_reponse_evenement(cible_id, event_id, q_obj["id"], answers_dict, rpe_val)
                if ok:
                    st.success("✅ Enregistré avec succès !")
                    st.rerun()
                else:
                    st.error(f"Erreur : {err}")

# =====================================================================
# PAGES COACH
# =====================================================================
if role_connecte == "coach":
    if menu == "📅 Planning & Séances":
        st.header("📅 Planning & Séances")
        athletes_list = supabase.table("profiles").select("id, full_name, team_id").eq("role", "athlete").execute().data or []
        dict_athletes = {a.get("full_name"): a["id"] for a in athletes_list if a.get("full_name")}
        dict_athletes_inv = {v: k for k, v in dict_athletes.items()}

        st.markdown("### ⚡ Séances du jour & du lendemain")
        toutes_seances_brutes = supabase.table("events").select("*").order("start_time").execute().data or []
        auj_date = maintenant_local().date()
        lend_date = auj_date + timedelta(days=1)

        seances_proches = [ev for ev in toutes_seances_brutes if (dt := _parser_datetime_event(ev)) and dt.date() in [auj_date, lend_date]]
        if seances_proches:
            for ev in seances_proches:
                dt_ev = _parser_datetime_event(ev)
                nom_j = dict_athletes_inv.get(ev.get("athlete_id"), "Tous / Équipe")
                with st.expander(f"🏋️ {ev.get('title')} — {dt_ev.strftime('%d/%m/%Y à %H:%M')} (Athlète: {nom_j})"):
                    rep_ev = obtenir_reponse_evenement(ev.get("athlete_id"), ev["id"]) if ev.get("athlete_id") else None
                    statut_p = (rep_ev.get("answers") or {}).get("Présence séance", "Présent") if rep_ev else "Présent"
                    st.write(f"**Lieu :** {ev.get('location', 'Non spécifié')} | **Statut présence :** {statut_p}")
        else:
            st.info("Aucune séance prévue aujourd'hui ou demain.")

        st.markdown("---")
        tab_nouvelle, tab_existantes = st.tabs(["🆕 Planifier une nouvelle séance", "📋 Séances planifiées"])
        with tab_nouvelle:
            with st.form("form_plan_seance"):
                title = st.text_input("Titre de la séance")
                event_type = st.selectbox("Type d'événement", ["training", "match"])
                athlete_sel = st.selectbox("Athlète concerné", ["-- Tous les athlètes --"] + sorted(dict_athletes.keys()))
                location = st.text_input("Lieu")
                rpe_cible = st.number_input("RPE Cible", 1.0, 10.0, 7.0, 0.5)
                event_date = st.date_input("Date", datetime.now())
                start_time = st.time_input("Début", datetime.strptime("10:00", "%H:%M").time())
                end_time = st.time_input("Fin", datetime.strptime("11:30", "%H:%M").time())
                if st.form_submit_button("Planifier", type="primary"):
                    target_ids = list(dict_athletes.values()) if athlete_sel == "-- Tous les athlètes --" else [dict_athletes[athlete_sel]]
                    dt_start = datetime.combine(event_date, start_time).isoformat()
                    dt_end = datetime.combine(event_date, end_time).isoformat()
                    inserts = [{"title": title, "event_type": event_type, "start_time": dt_start, "end_time": dt_end, "location": location, "athlete_id": aid, "rpe_cible": rpe_cible} for aid in target_ids]
                    supabase.table("events").insert(inserts).execute()
                    st.success("✅ Séance planifiée !")
                    st.rerun()

        with tab_existantes:
            tous_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []
            if tous_events:
                dict_ev_labels = {f"{e.get('title')} — {(e.get('start_time') or '')[:16]} ({dict_athletes_inv.get(e.get('athlete_id'), 'Tous')})": e for e in tous_events}
                sel_ev_str = st.selectbox("Sélectionner une séance à modifier/supprimer :", list(dict_ev_labels.keys()))
                ev_sel = dict_ev_labels[sel_ev_str]
                ev_id = ev_sel["id"]

                st.markdown("##### 👥 Effectif convoqué sur cette séance")
                memes_seances = [e for e in tous_events if e.get("title") == ev_sel.get("title") and e.get("start_time") == ev_sel.get("start_time")]
                dispos, indispos = [], []
                for ms in memes_seances:
                    aid = ms.get("athlete_id")
                    nom = dict_athletes_inv.get(aid, "Inconnu")
                    rep = obtenir_reponse_evenement(aid, ms["id"])
                    ans = (rep.get("answers") or {}) if rep else {}
                    pres = ans.get("Présence séance", "Présent")
                    bless = ans.get(FORMAT_BLESSURE, "Non")
                    if pres == "Présent" and str(bless).lower() not in ["oui", "yes", "1"]:
                        dispos.append(nom)
                    else:
                        indispos.append(f"{nom} ({pres} / Blessé: {bless})")
                
                c_ef1, c_ef2 = st.columns(2)
                with c_ef1:
                    st.markdown("**✅ Disponibles :**")
                    for d in dispos: st.markdown(f"- {d}")
                with c_ef2:
                    st.markdown("**🛑 Indisponibles :**")
                    for i in indispos: st.markdown(f"<span style='color:#93a0bd; text-decoration:line-through;'>- {i}</span>", unsafe_allow_html=True)

                if st.button("❌ Supprimer cette séance", type="primary"):
                    supabase.table("events").delete().eq("id", ev_id).execute()
                    st.success("✅ Supprimé !")
                    st.rerun()

    elif menu == "📁 Fichiers & Rapports GPS":
        st.header("📁 Fichiers & Rapports GPS")
        res_athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
        dict_athletes = {a.get("full_name"): a["id"] for a in res_athletes if a.get("full_name")}
        res_events = supabase.table("events").select("*").order("start_time", desc=True).execute().data or []
        dict_events = {f"{e.get('title')} — {(e.get('start_time') or '')[:16]}": e for e in res_events}

        tab_up, tab_gps = st.tabs(["📤 Joindre un PDF", "🛰️ Importer GPS"])
        with tab_up:
            if dict_events:
                sel_ev = st.selectbox("Séance :", list(dict_events.keys()), key="pdf_ev")
                titre_doc = st.text_input("Titre du document")
                up_file = st.file_uploader("Fichier PDF", type=["pdf"])
                if st.button("Publier", type="primary") and titre_doc and up_file:
                    file_bytes = up_file.read()
                    mime_type = up_file.type or "application/pdf"
                    file_url = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode('utf-8')}"
                    supabase.table("session_files").insert({
                        "title": titre_doc, "file_name": up_file.name, "file_url": file_url,
                        "event_id": dict_events[sel_ev]["id"], "created_at": datetime.now().isoformat()
                    }).execute()
                    st.success("✅ Document publié !")
                    st.rerun()
        with tab_gps:
            if dict_events:
                sel_ev_gps = st.selectbox("Séance :", list(dict_events.keys()), key="gps_ev")
                gps_file = st.file_uploader("Fichier GPS (CSV/XLSX)", type=["csv", "xlsx", "xls"])
                if gps_file and st.button("Importer GPS", type="primary"):
                    lignes = lire_fichier_gps(gps_file.getvalue(), gps_file.name)
                    res = enregistrer_rapport_gps(dict_events[sel_ev_gps]["id"], lignes, dict_athletes)
                    st.success(f"✅ Importé : {res['inseres']} lignes.")

    elif menu == "📝 Questionnaires":
        st.header("📝 Questionnaires & Assignations")
        tab_creer, tab_assign, tab_man, tab_rpe = st.tabs(["🆕 Créer", "📩 Assigner & Gérer", "✍️ Saisie manuelle", "🚫 RPE obligatoire"])
        
        with tab_creer:
            with st.form("form_creer_q"):
                q_t = st.text_input("Titre du questionnaire")
                q_ty = st.selectbox("Type", ["Pre-Event", "Post-Event"])
                if st.form_submit_button("Créer", type="primary") and q_t:
                    supabase.table("questionnaires").insert({
                        "title": q_t, "type": "pre_event" if "Pre" in q_ty else "post_event",
                        "questions": [{"label": "État de forme", "format": "scale", "scale_max": 5}]
                    }).execute()
                    st.success("✅ Questionnaire créé !")
                    st.rerun()

        with tab_assign:
            q_list = supabase.table("questionnaires").select("*").execute().data or []
            a_list = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
            if q_list and a_list:
                dict_q = {q["title"]: q["id"] for q in q_list}
                dict_a = {a["full_name"]: a["id"] for a in a_list if a.get("full_name")}
                with st.form("form_assign"):
                    sel_q = st.selectbox("Questionnaire", list(dict_q.keys()))
                    sel_a = st.selectbox("Athlète", list(dict_a.keys()))
                    moment = st.selectbox("Moment", ["Avant séance", "Après séance"])
                    if st.form_submit_button("Assigner", type="primary"):
                        definir_type_questionnaire(dict_q[sel_q], "pre_event" if moment == "Avant séance" else "post_event")
                        assigner_questionnaire(dict_q[sel_q], athlete_id=dict_a[sel_a])
                        st.success("✅ Assigné !")
                        st.rerun()

            st.markdown("##### 📋 Liste des assignations")
            assigns = obtenir_assignations()
            if assigns:
                for ass in assigns:
                    q_info = ass.get("questionnaires") or {}
                    p_info = ass.get("profiles") or {}
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.write(f"- **{q_info.get('title', 'Questionnaire')}** -> {p_info.get('full_name', 'Athlète')} ({q_info.get('type')})")
                    with c2:
                        if st.button("❌ Retirer", key=f"del_as_{ass['id']}"):
                            supprimer_assignation(ass["id"])
                            st.rerun()

        with tab_man:
            athletes = supabase.table("profiles").select("id, full_name").eq("role", "athlete").execute().data or []
            dict_ath = {a.get("full_name"): a["id"] for a in athletes if a.get("full_name")}
            if dict_ath:
                ath_sel = st.selectbox("Athlète", list(dict_ath.keys()), key="man_ath")
                evs = supabase.table("events").select("id, title, start_time").eq("athlete_id", dict_ath[ath_sel]).execute().data or []
                q_list = supabase.table("questionnaires").select("*").execute().data or []
                if evs and q_list:
                    ev_sel = st.selectbox("Séance", [f"{e['title']} ({e['start_time'][:10]})" for e in evs], key="man_ev")
                    ev_id = [e["id"] for e in evs if f"{e['title']} ({e['start_time'][:10]})" == ev_sel][0]
                    q_sel = st.selectbox("Questionnaire", [q["title"] for q in q_list], key="man_q")
                    q_obj = next(q for q in q_list if q["title"] == q_sel)
                    
                    rep_exist = obtenir_reponse_evenement(dict_ath[ath_sel], ev_id)
                    rendre_formulaire_questionnaire(q_obj, ev_id, "saisie_man", (rep_exist.get("answers") or {}) if rep_exist else {}, athlete_id=dict_ath[ath_sel])

        with tab_rpe:
            st.subheader("🚫 RPE obligatoire")
            evs_rpe = supabase.table("events").select("id, title, start_time").execute().data or []
            if evs_rpe:
                ev_labels = {f"{e['title']} ({e['start_time'][:16]})": e["id"] for e in evs_rpe}
                sel_evs = st.multiselect("Sélectionner les séances :", list(ev_labels.keys()))
                if st.button("Retirer RPE obligatoire", type="primary") and sel_evs:
                    ids = [ev_labels[k] for k in sel_evs]
                    supabase.table("events").update({"rpe_desactive": True}).in_("id", ids).execute()
                    st.success("✅ RPE désactivé pour ces séances.")

    elif menu == "📊 Analytique":
        st.header("📊 Analytique & Données")
        profiles = supabase.table("profiles").select("*").execute().data or []
        dict_profiles = {p["id"]: p.get("full_name", "") for p in profiles}
        dict_athletes = {p.get("full_name"): p["id"] for p in profiles if p.get("role") == "athlete"}

        mode = st.radio("Mode :", ["👤 Un joueur", "👥 Une équipe"], horizontal=True)
        j_sel = st.selectbox("Athlète", sorted(dict_athletes.keys())) if mode == "👤 Un joueur" else None
        
        res_resp = supabase.table("questionnaire_responses").select("*").execute().data or []
        records = [{"Joueur": dict_profiles.get(r.get("athlete_id")), "Question": k, "Valeur": v, "Date": r.get("submitted_at","")[:10]} for r in res_resp for k, v in _lire_answers(r.get("answers")).items()]
        df = pd.DataFrame(records) if records else pd.DataFrame()

        tab_q, tab_g, tab_gps, tab_brut = st.tabs(["Réponses", "Graphique", "GPS", "Données brutes"])
        with tab_q:
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Exporter CSV", df.to_csv(index=False).encode('utf-8'), "reponses.csv", "text/csv")
        with tab_g:
            if not df.empty:
                df_num = df.copy()
                df_num["Valeur_num"] = pd.to_numeric(df_num["Valeur"], errors="coerce")
                df_num = df_num.dropna(subset=["Valeur_num"])
                if not df_num.empty:
                    q_var = st.selectbox("Métrique", df_num["Question"].unique())
                    st.plotly_chart(px.line(df_num[df_num["Question"] == q_var], x="Date", y="Valeur_num", markers=True, template="plotly_dark"))
        with tab_gps:
            gps_all = obtenir_rapports_gps()
            if gps_all:
                df_gps = pd.DataFrame(gps_all)
                st.dataframe(df_gps, use_container_width=True)
                st.download_button("📥 Exporter GPS CSV", df_gps.to_csv(index=False).encode('utf-8'), "gps.csv", "text/csv")
        with tab_brut:
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Exporter Brutes CSV", df.to_csv(index=False).encode('utf-8'), "brutes.csv", "text/csv")

    elif menu == "👥 Effectif":
        st.header("👥 Gestion de l'effectif")
        teams = supabase.table("teams").select("*").execute().data or []
        dict_teams = {t["name"]: t["id"] for t in teams}
        if dict_teams:
            eq = st.selectbox("Équipe", list(dict_teams.keys()))
            athletes = supabase.table("profiles").select("*").eq("team_id", dict_teams[eq]).eq("role", "athlete").execute().data or []
            for ath in athletes:
                with st.expander(f"🏃 {ath.get('full_name')} (N°{ath.get('numero', '-')})"):
                    with st.form(f"ath_{ath['id']}"):
                        n = st.text_input("Nom", value=ath.get("full_name", ""))
                        num = st.number_input("Numéro", value=int(ath.get("numero") or 0))
                        if st.form_submit_button("Modifier", type="primary"):
                            modifier_athlete(ath["id"], n, dict_teams[eq], num)
                            st.success("✅ Mis à jour !")
                            st.rerun()

    elif menu == "⚙️ Gestion des profils":
        st.header("⚙️ Équipes & Comptes")
        with st.form("creer_eq"):
            new_eq = st.text_input("Nouvelle équipe")
            if st.form_submit_button("Créer équipe", type="primary") and new_eq:
                creer_equipe(new_eq)
                st.success("✅ Équipe créée !")
                st.rerun()

    elif menu == "🔊 Générateur de Bips Audio":
        st.header("🔊 Générateur de Bips Audio")
        st.info("Utilisez l'outil de génération pour vos tests de terrain.")

# =====================================================================
# PAGES ATHLÈTE
# =====================================================================
else:
    if menu == "📅 Séances à venir":
        st.header("📅 Mes séances")
        events = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
        q_all = supabase.table("questionnaires").select("*").execute().data or []
        q_pre = [q for q in q_all if q.get("type") == "pre_event"]
        q_auto = obtenir_ou_creer_rpe_auto()

        for ev in events:
            dt = _parser_datetime_event(ev)
            if dt:
                with st.expander(f"🏋️ {ev.get('title')} — {dt.strftime('%d/%m/%Y à %H:%M')}"):
                    rep = obtenir_reponse_evenement(mon_id, ev["id"]) or {}
                    reponses_deja = rep.get("answers", {})
                    
                    st.markdown("##### 📝 Présence")
                    with st.form(f"pres_{ev['id']}"):
                        p_val = st.selectbox("Présence ?", ["Présent", "Absent / Blessé", "Douleur localisée"])
                        if st.form_submit_button("Valider présence", type="primary"):
                            enregistrer_reponse_evenement(mon_id, ev["id"], q_pre[0]["id"] if q_pre else "0", {"Présence séance": p_val})
                            st.success("✅ Validé !")
                            st.rerun()

    elif menu == "📆 Calendrier":
        st.header("📆 Calendrier")
        events = supabase.table("events").select("*").eq("athlete_id", mon_id).execute().data or []
        for ev in events:
            dt = _parser_datetime_event(ev)
            if dt:
                st.markdown(f"- **{dt.strftime('%d/%m/%Y %H:%M')}** : {ev.get('title')} ({ev.get('location', '')})")

    elif menu == "📊 Mes données":
        st.header("📊 Mes données")
        res = obtenir_reponses_athlete(mon_id)
        records = [{"Question": k, "Valeur": v, "Date": r.get("submitted_at","")[:10]} for r in res for k, v in _lire_answers(r.get("answers")).items()]
        df = pd.DataFrame(records) if records else pd.DataFrame()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Exporter mes données (CSV)", df.to_csv(index=False).encode('utf-8'), "mes_donnees.csv", "text/csv")
        else:
            st.info("Aucune donnée enregistrée.")
