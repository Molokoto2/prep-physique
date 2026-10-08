import pandas as pd
import io
from datetime import datetime
from supabase import create_client, Client
import os

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
    
    # Trouver la colonne du nom du joueur et la colonne de la période
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

    # Filtrer uniquement sur les lignes où la période contient "Session" (si la colonne existe)
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

        ligne_data = {
            "player_name": nom_joueur,
            "distance_totale_m": get_val(["Distance", "Total Distance"]),
            "distance_haute_intensite_m": get_val(["High Intensity", "High-Intensity", "HI Distance"]),
            "distance_haute_vitesse_m": get_val(["High Speed", "Speed Distance"]),
            "distance_sprint_m": get_val(["Sprint"]),
            "nb_accelerations": get_val(["Accel"]),
            "nb_decelerations": get_val(["Decel"]),
            "vmax_kmh": get_val(["Vmax", "Max Velocity", "Speed Max"]),
            "meterage_par_minute": get_val(["Meterage", "m/min", "Distance per minute"]),
            "duree_secondes": get_val(["Duration", "Time"])
        }
        lignes_extraites.append(ligne_data)

    return lignes_extraites

def matcher_nom_athlete(nom_fichier, dict_athletes):
    """
    Retrouve l'ID Supabase d'un athlète de manière ultra-souple (insensible à la casse,
    aux espaces multiples, et à l'ordre Nom/Prénom).
    """
    if not nom_fichier:
        return None
    
    # Nettoyer et normaliser le nom du fichier
    nom_propre = " ".join(str(nom_fichier).strip().lower().split())
    
    # 1. Correspondance exacte
    for nom_db, uuid in dict_athletes.items():
        if " ".join(nom_db.strip().lower().split()) == nom_propre:
            return uuid
            
    # 2. Correspondance inversée ou par ensemble de mots (Prénom Nom vs Nom Prénom)
    mots_fichier = set(nom_propre.split())
    for nom_db, uuid in dict_athletes.items():
        mots_db = set(nom_db.strip().lower().split())
        if mots_fichier and mots_fichier == mots_db:
            return uuid
            
    # 3. Correspondance partielle forte (si les mots clés du nom en base sont dans le fichier)
    for nom_db, uuid in dict_athletes.items():
        mots_db = [m for m in nom_db.strip().lower().split() if len(m) > 2]
        if mots_db and all(m in nom_propre for m in mots_db):
            return uuid
            
    return None

def enregistrer_rapport_gps(event_id, lignes, dict_athletes):
    """
    Enregistre en base de données les lignes GPS pour tous les joueurs reconnus.
    """
    n_inseres = 0
    non_trouves = []
    
    event_date_str = datetime.now().isoformat()
    try:
        ev_res = supabase.table("events").select("start_time").eq("id", event_id).execute()
        if ev_res.data and ev_res.data[0].get("start_time"):
            event_date_str = ev_res.data[0]["start_time"]
    except Exception:
        pass

    for l in lignes:
        p_name = l.pop("player_name", None)
        if "session_date" in l:
            l.pop("session_date")
            
        athlete_id = matcher_nom_athlete(p_name, dict_athletes)
        
        if athlete_id:
            l["event_id"] = event_id
            l["athlete_id"] = athlete_id
            l["recorded_at"] = event_date_str

            try:
                # Supprimer l'ancien rapport s'il existe pour éviter les doublons
                supabase.table("gps_reports").delete().eq("event_id", event_id).eq("athlete_id", athlete_id).execute()
                # Insérer le nouveau rapport
                supabase.table("gps_reports").insert(l).execute()
                n_inseres += 1
            except Exception as ex:
                print(f"Erreur Supabase insertion GPS : {ex}")
        else:
            if p_name and p_name not in non_trouves:
                non_trouves.append(p_name)
                
    return n_inseres, non_trouves

def obtenir_rapports_gps():
    try:
        res = supabase.table("gps_reports").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []

# Fonctions annexes d'authentification et gestion de comptes
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

def modifier_compte(user_id, full_name, role, team_id=None):
    try:
        data = {"full_name": full_name, "role": role, "team_id": team_id}
        supabase.table("profiles").update(data).eq("id", user_id).execute()
        return True, "Compte mis à jour."
    except Exception as e:
        return False, str(e)

def supprimer_compte(user_id):
    try:
        supabase.table("profiles").delete().eq("id", user_id).execute()
        return True, "Compte supprimé."
    except Exception as e:
        return False, str(e)

def lister_comptes():
    try:
        res = supabase.table("profiles").select("*, teams(name)").execute()
        return res.data if res.data else []
    except:
        return []

def ajouter_athlete_manual(full_name, team_id=None):
    pass

def modifier_athlete(athlete_id, full_name, team_id=None):
    try:
        supabase.table("profiles").update({"full_name": full_name, "team_id": team_id}).eq("id", athlete_id).execute()
        return True
    except:
        return False

def supprimer_profil_athlete(athlete_id):
    try:
        supabase.table("profiles").delete().eq("id", athlete_id).execute()
        return True
    except:
        return False

def creer_equipe(name):
    try:
        supabase.table("teams").insert({"name": name}).execute()
        return True
    except:
        return False

def supprimer_equipe(team_id):
    try:
        supabase.table("teams").delete().eq("id", team_id).execute()
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
        aid = p["id"]
        statuts[aid] = {"statut": "disponible", raison: ""}
    return statuts

def enregistrer_reponse_evenement(athlete_id, event_id, questionnaire_id, answers, rpe=None):
    try:
        data = {
            "athlete_id": athlete_id,
            "event_id": event_id,
            "questionnaire_id": questionnaire_id,
            "answers": answers,
            "submitted_at": datetime.now().isoformat()
        }
        if rpe is not None:
            data["rpe"] = rpe
        supabase.table("questionnaire_responses").upsert(data, on_conflict="athlete_id,event_id,questionnaire_id").execute()
        return True, None
    except Exception as e:
        return False, str(e)

def obtenir_reponse_evenement(athlete_id, event_id):
    try:
        res = supabase.table("questionnaire_responses").select("*").eq("athlete_id", athlete_id).eq("event_id", event_id).execute()
        if res.data:
            return res.data[0]
    except:
        pass
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

def assigner_questionnaire(questionnaire_id, athlete_id, event_id=None):
    try:
        data = {"questionnaire_id": questionnaire_id, "athlete_id": athlete_id, "event_id": event_id}
        supabase.table("questionnaire_assignments").insert(data).execute()
    except:
        pass

def obtenir_assignations():
    try:
        res = supabase.table("questionnaire_assignments").select("*").execute()
        return res.data if res.data else []
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
