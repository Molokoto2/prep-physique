import pandas as pd
import io
import json
import re
import unicodedata
import difflib
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
            "duree_secondes": int(round(duree_minutes * 60))
        }
        lignes_extraites.append(ligne_data)

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

    for nom_db, n in base.items():
        mots_db = [m for m in n.split() if len(m) > 2]
        if mots_db and all(m in mots_fichier for m in mots_db):
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

COLONNES_GPS_ENTIERES = ("nb_accelerations", "nb_decelerations", "duree_secondes")

def _preparer_record_gps(ligne, event_id, athlete_id, date_seance):
    rec = {"event_id": event_id, "athlete_id": athlete_id, "recorded_at": date_seance}
    for col in COLONNES_GPS_NUMERIQUES:
        val = ligne.get(col)
        try:
            val = float(val)
            if val != val:
                val = 0.0
        except (TypeError, ValueError):
            val = 0.0
        rec[col] = int(round(val)) if col in COLONNES_GPS_ENTIERES else round(val, 2)
    return rec

def _inserer_gps_en_s_adaptant(record):
    rec = dict(record)
    ignorees = []
    arrondi_fait = False
    for _ in range(15):
        try:
            supabase.table("gps_reports").insert(rec).execute()
            return True, ignorees, None
        except Exception as e:
            msg = str(e)
            m = (re.search(r"Could not find the '([^']+)' column", msg)
                 or re.search(r'column "([^"]+)" of relation "gps_reports" does not exist', msg))
            if m:
                col = m.group(1)
                if col in rec and col not in ("event_id", "athlete_id"):
                    rec.pop(col)
                    ignorees.append(col)
                    continue
            if "invalid input syntax for type integer" in msg:
                m = re.search(r'type integer: "([^"]+)"', msg)
                fautives = [k for k, v in rec.items()
                            if isinstance(v, float) and m and (str(v) == m.group(1) or f"{v:g}" == m.group(1))]
                if fautives:
                    for k in fautives:
                        rec[k] = int(round(rec[k]))
                    continue
                if not arrondi_fait:
                    rec = {k: (int(round(v)) if isinstance(v, float) else v) for k, v in rec.items()}
                    arrondi_fait = True
                    continue
            return False, ignorees, msg
    return False, ignorees, "Trop de tentatives d'adaptation."

def enregistrer_rapport_gps(event_id, lignes, dict_athletes):
    resultat = {"inseres": 0, "importes": [], "non_trouves": [], "erreurs": [],
                "colonnes_ignorees": [], "verifie": None}

    date_seance = datetime.now().isoformat()
    events_par_athlete = {}
    try:
        ev_res = supabase.table("events").select("title, start_time").eq("id", event_id).execute()
        if ev_res.data:
            ev0 = ev_res.data[0]
            if ev0.get("start_time"):
                date_seance = ev0["start_time"]
            if ev0.get("title") and ev0.get("start_time"):
                freres = supabase.table("events").select("id, athlete_id").eq("title", ev0["title"]).eq("start_time", ev0["start_time"]).execute().data or []
                events_par_athlete = {e["athlete_id"]: e["id"] for e in freres if e.get("athlete_id")}
    except Exception:
        pass

    ids_importes = set()
    ids_events_utilises = set()
    for l in lignes:
        p_name = l.get("player_name")
        athlete_id = matcher_nom_athlete(p_name, dict_athletes)
        if not athlete_id:
            if p_name and p_name not in resultat["non_trouves"]:
                resultat["non_trouves"].append(p_name)
            continue

        event_cible = events_par_athlete.get(athlete_id, event_id)
        ids_events_utilises.add(event_cible)
        try:
            supabase.table("gps_reports").delete().eq("event_id", event_cible).eq("athlete_id", athlete_id).execute()
        except Exception:
            pass

        record = _preparer_record_gps(l, event_cible, athlete_id, date_seance)
        ok, ignorees, erreur = _inserer_gps_en_s_adaptant(record)
        for c in ignorees:
            if c != "recorded_at" and c not in resultat["colonnes_ignorees"]:
                resultat["colonnes_ignorees"].append(c)
        if ok:
            resultat["inseres"] += 1
            resultat["importes"].append(p_name)
            ids_importes.add(athlete_id)
        else:
            resultat["erreurs"].append(f"{p_name} : {erreur}")

    if ids_importes:
        try:
            rel = supabase.table("gps_reports").select("athlete_id").in_("event_id", list(ids_events_utilises)).execute().data or []
            resultat["verifie"] = len([r for r in rel if r.get("athlete_id") in ids_importes])
        except Exception as e:
            resultat["erreurs"].append(f"Vérification impossible : {e}")
    return resultat

def obtenir_rapports_gps(athlete_id=None, event_id=None):
    try:
        q = supabase.table("gps_reports").select("*")
        if athlete_id:
            q = q.eq("athlete_id", athlete_id)
        if event_id:
            q = q.eq("event_id", event_id)
        rapports = q.execute().data or []
    except Exception as e:
        print(f"Erreur lecture gps_reports : {e}")
        return []

    ids_events = list({r.get("event_id") for r in rapports if r.get("event_id")})
    events = {}
    for i in range(0, len(ids_events), 80):
        try:
            for ev in supabase.table("events").select("id, title, start_time").in_("id", ids_events[i:i + 80]).execute().data or []:
                events[ev["id"]] = ev
        except Exception as e:
            print(f"Erreur lecture des séances GPS : {e}")

    for r in rapports:
        ev = events.get(r.get("event_id"), {})
        r["seance_titre"] = ev.get("title") or "Séance"
        r["seance_date"] = ev.get("start_time") or r.get("recorded_at") or r.get("created_at") or ""
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
        statuts[aid] = {"statut": "disponible", "raison": ""}
    return statuts

def _lire_answers(valeur):
    if isinstance(valeur, str):
        try:
            valeur = json.loads(valeur)
        except Exception:
            return {}
    return valeur if isinstance(valeur, dict) else {}

def obtenir_reponses_athlete(athlete_id):
    try:
        return supabase.table("questionnaire_responses").select("*").eq("athlete_id", athlete_id).execute().data or []
    except Exception as e:
        print(f"Erreur lecture des réponses : {e}")
        return []

def enregistrer_reponse_evenement(athlete_id, event_id, questionnaire_id, answers, rpe=None):
    def _maj(ligne, fusion):
        data = {"answers": fusion, "submitted_at": datetime.now().isoformat()}
        if rpe is not None:
            data["rpe"] = rpe
        try:
            supabase.table("questionnaire_responses").update(data).eq("id", ligne["id"]).execute()
        except Exception:
            if "rpe" not in data:
                raise
            data.pop("rpe")
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
        try:
            try:
                supabase.table("questionnaire_responses").insert(data).execute()
            except Exception as e1:
                if "rpe" in data and "rpe" in str(e1) and "duplicate" not in str(e1).lower():
                    data.pop("rpe")
                    supabase.table("questionnaire_responses").insert(data).execute()
                else:
                    raise
        except Exception as e2:
            msg = str(e2).lower()
            if lignes and ("duplicate" in msg or "23505" in msg or "unique" in msg):
                fusion = _lire_answers(lignes[0].get("answers"))
                fusion.update(answers)
                _maj(lignes[0], fusion)
            else:
                raise
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
    except Exception:
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
    except Exception as e:
        print(f"Erreur questionnaire RPE auto : {e}")
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
