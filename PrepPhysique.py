import os
import io
import csv
import re
import json
import datetime
import unicodedata
import pandas as pd
from supabase import create_client, Client
st.write("Test de démarrage OK")

def _get_secret(name: str, default: str = None):
    val = os.environ.get(name)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default

SUPABASE_URL = _get_secret("SUPABASE_URL", "https://gedzzrwxefwycrtrgbwj.supabase.co")
SUPABASE_KEY = _get_secret("SUPABASE_KEY", None)

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY manquante.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def connexion(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if not res.user:
            return None, None, "Identifiants invalides."
        profile_res = supabase.table("profiles").select("*").eq("id", res.user.id).single().execute()
        profile = profile_res.data
        if not profile:
            return None, None, "Compte sans profil associé."
        return res.session, profile, None
    except Exception as e:
        return None, None, f"Erreur de connexion : {e}"

def deconnexion():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

def creer_compte(email: str, password: str, full_name: str, role: str, team_id: str = None):
    if role not in ("coach", "athlete"):
        return False, "Rôle invalide."
    try:
        res = supabase.auth.admin.create_user({
            "email": email, "password": password, "email_confirm": True,
            "user_metadata": {"full_name": full_name}
        })
        if res.user:
            supabase.table("profiles").upsert({
                "id": res.user.id, "full_name": full_name, "role": role, "team_id": team_id
            }).execute()
            return True, f"Compte {role} créé pour {full_name} !"
        return False, "Erreur création utilisateur."
    except Exception as e:
        return False, f"Erreur : {e}"

def modifier_compte(user_id: str, full_name: str = None, role: str = None, team_id=None, new_password: str = None, new_email: str = None):
    try:
        auth_upd = {}
        if new_password: auth_upd["password"] = new_password
        if new_email: auth_upd["email"] = new_email
        if auth_upd: supabase.auth.admin.update_user_by_id(user_id, auth_upd)

        prof_upd = {}
        if full_name is not None: prof_upd["full_name"] = full_name
        if role is not None: prof_upd["role"] = role
        if team_id is not None: prof_upd["team_id"] = team_id if team_id != "" else None
        if prof_upd: supabase.table("profiles").update(prof_upd).eq("id", user_id).execute()
        return True, "Mis à jour avec succès."
    except Exception as e:
        return False, f"Erreur : {e}"

def supprimer_compte(user_id: str):
    try:
        supabase.table("profiles").delete().eq("id", user_id).execute()
        supabase.auth.admin.delete_user(user_id)
        return True, "Supprimé définitivement."
    except Exception as e:
        return False, f"Erreur : {e}"

def lister_comptes():
    try:
        return supabase.table("profiles").select("*").order("role").execute().data or []
    except:
        return []

def definir_type_questionnaire(questionnaire_id: str, type_questionnaire: str):
    supabase.table("questionnaires").update({"type": type_questionnaire}).eq("id", questionnaire_id).execute()

def obtenir_fichiers_evenement(event_id: str):
    try:
        return supabase.table("session_files").select("*").eq("event_id", event_id).order("created_at", desc=True).execute().data or []
    except:
        return []

def definir_minutes_avant(questionnaire_id: str, minutes: int):
    supabase.table("questionnaires").update({"trigger_minutes": int(minutes)}).eq("id", questionnaire_id).execute()

def definir_minutes_apres(questionnaire_id: str, minutes: int):
    supabase.table("questionnaires").update({"post_window_minutes": int(minutes)}).eq("id", questionnaire_id).execute()

def assigner_questionnaire(questionnaire_id: str, athlete_id: str, event_id: str = None):
    try:
        req = supabase.table("questionnaire_assignments").delete().eq("questionnaire_id", questionnaire_id).eq("athlete_id", athlete_id)
        req = req.is_("event_id", None) if event_id is None else req.eq("event_id", event_id)
        req.execute()
    except:
        pass
    supabase.table("questionnaire_assignments").insert({
        "questionnaire_id": questionnaire_id, "athlete_id": athlete_id, "event_id": event_id, "is_active": True
    }).execute()

def obtenir_assignations():
    try:
        return supabase.table("questionnaire_assignments").select("*").execute().data or []
    except:
        return []

def questionnaire_disponible_pour(questionnaire_id: str, athlete_id: str, event_id: str, assignations: list) -> bool:
    assignations_q = [a for a in assignations if a.get("questionnaire_id") == questionnaire_id]
    if not assignations_q:
        return True
    for a in assignations_q:
        if a.get("athlete_id") != athlete_id: continue
        if a.get("event_id") is None or a.get("event_id") == event_id: return True
    return False

def ajouter_athlete_manual(email: str, password: str, full_name: str, team_id: str = None):
    return creer_compte(email, password, full_name, role="athlete", team_id=team_id)

def modifier_athlete(athlete_id: str, new_name: str, new_team_id: str = None):
    return supabase.table("profiles").update({"full_name": new_name, "team_id": new_team_id if new_team_id else None}).eq("id", athlete_id).execute()

def supprimer_profil_athlete(athlete_id: str):
    return supabase.table("profiles").delete().eq("id", athlete_id).execute()

def creer_equipe(nom_equipe: str):
    return supabase.table("teams").insert({"name": nom_equipe}).execute()

def supprimer_equipe(team_id: str):
    return supabase.table("teams").delete().eq("id", team_id).execute()

FORMAT_BLESSURE = "injury_flag"

def enregistrer_reponse_evenement(athlete_id: str, event_id: str, questionnaire_id: str, nouvelles_reponses: dict, rpe_score: float = None):
    try:
        existant = supabase.table("questionnaire_responses").select("*").eq("athlete_id", athlete_id).eq("event_id", event_id).execute().data
        deja = existant[0] if existant else None
        reponses_existantes = (deja or {}).get("answers") or {}
        if isinstance(reponses_existantes, str):
            try: reponses_existantes = json.loads(reponses_existantes)
            except: reponses_existantes = {}
        reponses_fusionnees = dict(reponses_existantes)
        reponses_fusionnees.update(nouvelles_reponses)

        payload = {
            "athlete_id": athlete_id, "event_id": event_id,
            "questionnaire_id": (deja.get("questionnaire_id") if deja else None) or questionnaire_id,
            "answers": reponses_fusionnees,
            "rpe_score": rpe_score if rpe_score is not None else (deja.get("rpe_score") if deja else None),
            "submitted_at": datetime.datetime.now().isoformat(),
        }
        supabase.table("questionnaire_responses").upsert(payload, on_conflict="athlete_id,event_id").execute()
        return True, None
    except Exception as e:
        return False, str(e)

def obtenir_reponse_evenement(athlete_id: str, event_id: str):
    try:
        res = supabase.table("questionnaire_responses").select("*").eq("athlete_id", athlete_id).eq("event_id", event_id).execute().data
        return res[0] if res else None
    except:
        return None

def obtenir_reponses_avec_definitions():
    try:
        res = supabase.table("questionnaire_responses").select("id, athlete_id, rpe_score, answers, submitted_at, questionnaire_id, questionnaires(questions)").execute()
        return res.data or []
    except:
        return []

def calculer_statut_disponibilite(profiles: list, responses: list):
    statuts = {p["id"]: {"statut": "disponible", "depuis": None} for p in profiles if p.get("role") == "athlete"}
    return statuts

COLONNES_GPS_CATAPULT = {
    "Acceleration Efforts": "nb_accelerations", "Deceleration Efforts": "nb_decelerations",
    "Duration": "duree_secondes", "Distance": "distance_totale_m", "Max Velocity": "vmax_kmh",
    "Meterage Per Minute": "meterage_par_minute", "Sprint Distance": "distance_sprint_m",
    "HI Distance": "distance_haute_intensite_m", "High Speed Distance": "distance_haute_vitesse_m",
}

COLONNES_GPS_NUMERIQUES = [
    "distance_totale_m", "distance_haute_intensite_m", "distance_haute_vitesse_m",
    "distance_sprint_m", "nb_accelerations", "nb_decelerations",
    "vmax_kmh", "meterage_par_minute", "duree_secondes",
]

def _cle_nom(s: str) -> str:
    s = str(s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z\s]", " ", s)
    return " ".join(sorted(s.upper().split()))

def matcher_nom_athlete(nom_fichier: str, dict_athletes: dict):
    cle_cherchee = _cle_nom(nom_fichier)
    if not cle_cherchee: return None
    for nom, athlete_id in dict_athletes.items():
        if _cle_nom(nom) == cle_cherchee: return athlete_id
    return None

def _parser_nombre_fr(val):
    if val is None: return None
    val = str(val).strip().strip('"').replace(" ", "").replace(",", ".")
    try: return float(val)
    except: return None

def _parser_duree_hms(val):
    if not val: return None
    m = re.match(r"^(\d+):(\d{2}):(\d{2})$", str(val).strip().strip('"'))
    if not m: return None
    h, mn, s = (int(x) for x in m.groups())
    return h * 3600 + mn * 60 + s

def lire_fichier_gps(file_bytes: bytes, nom_fichier: str = ""):
    texte = None
    for enc in ("utf-8-sig", "cp1252", "latin1"):
        try:
            texte = file_bytes.decode(enc)
            break
        except: continue

    lignes = []
    if texte:
        lignes_brutes = texte.splitlines()
        idx_entete = next((i for i, l in enumerate(lignes_brutes) if "Player" in l or "Name" in l or "Distance" in l), 0)
        
        # Test avec séparateur point-virgule ou virgule
        for sep in [";", ","]:
            try:
                reader = csv.reader(lignes_brutes[idx_entete:], delimiter=sep)
                entetes = [e.strip().strip('"') for e in next(reader)]
                
                # Recherche des colonnes de nom et période
                idx_nom = next((i for i, e in enumerate(entetes) if "player" in e.lower() or "name" in e.lower() or "nom" in e.lower()), None)
                idx_periode = next((i for i, e in enumerate(entetes) if "period" in e.lower() or "periode" in e.lower()), None)
                
                if idx_nom is not None:
                    for row in reader:
                        if len(row) <= idx_nom: continue
                        if idx_periode is not None and len(row) > idx_periode:
                            periode_val = row[idx_periode].strip().strip('"').lower()
                            if periode_val and periode_val != "session" and "session" not in periode_val:
                                continue
                        
                        nom_joueur = row[idx_nom].strip().strip('"')
                        if not nom_joueur: continue
                        
                        ligne = {"nom_joueur": nom_joueur}
                        for i, ent in enumerate(entetes):
                            if i < len(row):
                                val = row[i]
                                ent_lower = ent.lower()
                                if "distance" in ent_lower and "sprint" not in ent_lower and "hi" not in ent_lower and "high" not in ent_lower:
                                    ligne["distance_totale_m"] = _parser_nombre_fr(val)
                                elif "hi distance" in ent_lower or "high intensity" in ent_lower:
                                    ligne["distance_haute_intensite_m"] = _parser_nombre_fr(val)
                                elif "high speed" in ent_lower:
                                    ligne["distance_haute_vitesse_m"] = _parser_nombre_fr(val)
                                elif "sprint" in ent_lower:
                                    ligne["distance_sprint_m"] = _parser_nombre_fr(val)
                                elif "acceleration" in ent_lower:
                                    ligne["nb_accelerations"] = _parser_nombre_fr(val)
                                elif "deceleration" in ent_lower:
                                    ligne["nb_decelerations"] = _parser_nombre_fr(val)
                                elif "velocity" in ent_lower or "vmax" in ent_lower:
                                    ligne["vmax_kmh"] = _parser_nombre_fr(val)
                                elif "meterage" in ent_lower or "min" in ent_lower:
                                    ligne["meterage_par_minute"] = _parser_nombre_fr(val)
                                elif "duration" in ent_lower:
                                    ligne["duree_secondes"] = _parser_duree_hms(val) or _parser_nombre_fr(val)
                        lignes.append(ligne)
                    if lignes:
                        break
            except Exception:
                continue

    # Fallback lecture excel si le CSV échoue
    if not lignes:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
            df.columns = [str(c).strip().lower() for c in df.columns]
            col_nom = next((c for c in df.columns if "player" in c or "nom" in c or "athlete" in c), None)
            if col_nom:
                for _, row in df.iterrows():
                    nom_j = row[col_nom]
                    if pd.isna(nom_j): continue
                    ligne = {"nom_joueur": str(nom_j)}
                    for c in df.columns:
                        if "dist" in c and "sprint" not in c: ligne["distance_totale_m"] = _parser_nombre_fr(row[c])
                        elif "sprint" in c: ligne["distance_sprint_m"] = _parser_nombre_fr(row[c])
                        elif "acc" in c: ligne["nb_accelerations"] = _parser_nombre_fr(row[c])
                        elif "dec" in c: ligne["nb_decelerations"] = _parser_nombre_fr(row[c])
                        elif "max" in c or "vmax" in c: ligne["vmax_kmh"] = _parser_nombre_fr(row[c])
                    lignes.append(ligne)
        except Exception:
            pass

    return lignes

def enregistrer_rapport_gps(event_id: str, lignes: list, dict_athletes: dict):
    inseres = 0
    non_trouves = []
    for ligne in lignes:
        nom = str(ligne.get("nom_joueur", "")).strip()
        athlete_id = matcher_nom_athlete(nom, dict_athletes)
        if not athlete_id:
            non_trouves.append(nom)
            continue
        record = {
            "event_id": event_id, "athlete_id": athlete_id,
            **{k: ligne.get(k) for k in COLONNES_GPS_NUMERIQUES if ligne.get(k) is not None},
            "donnees_brutes": {k: v for k, v in ligne.items() if k != "nom_joueur"},
            "created_at": datetime.datetime.now().isoformat()
        }
        try:
            supabase.table("gps_reports").insert(record).execute()
            inseres += 1
        except Exception as e:
            non_trouves.append(f"{nom} (erreur DB: {e})")
    return inseres, non_trouves

def obtenir_rapports_gps(athlete_id: str = None, event_id: str = None):
    try:
        q = supabase.table("gps_reports").select("*, events(title, start_time)")
        if athlete_id: q = q.eq("athlete_id", athlete_id)
        if event_id: q = q.eq("event_id", event_id)
        return q.order("created_at", desc=True).execute().data or []
    except:
        return []
