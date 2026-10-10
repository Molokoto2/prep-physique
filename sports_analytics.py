import pandas as pd
import io
import json
import re
import unicodedata
import difflib
from datetime import datetime, timedelta
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
    """Convertit une durée (ex: '01:14:10', '14:10') en minutes décimales."""
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
        return float(val_str.replace(",", "."))
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
    """Minuscules, sans accents ni ponctuation, espaces nettoyés ('Loïc DUFAU.' -> 'loic dufau')."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s).lower()
    return " ".join(s.split())

def matcher_nom_athlete(nom_fichier, dict_athletes):
    """
    Retrouve l'athlete_id correspondant à un nom du fichier GPS.
    Insensible aux accents, aux majuscules, à la ponctuation et à l'ordre Nom/Prénom.
    """
    nom_propre = _norm_nom(nom_fichier)
    if not nom_propre:
        return None
    base = {nom: _norm_nom(nom) for nom in dict_athletes}

    # 1. Correspondance exacte
    for nom_db, n in base.items():
        if n == nom_propre:
            return dict_athletes[nom_db]

    # 2. Mêmes mots dans un ordre différent (ex : "BARGUIN Axel" / "Axel Barguin")
    mots_fichier = set(nom_propre.split())
    for nom_db, n in base.items():
        if mots_fichier and mots_fichier == set(n.split()):
            return dict_athletes[nom_db]

    # 3. Tous les mots (>2 lettres) du profil sont présents dans le nom du fichier
    for nom_db, n in base.items():
        mots_db = [m for m in n.split() if len(m) > 2]
        if mots_db and all(m in mots_fichier for m in mots_db):
            return dict_athletes[nom_db]

    # 4. Petite faute de frappe (ex : "Barguinn")
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
    """Construit la ligne à insérer : nombres propres (entiers pour les comptages)."""
    rec = {"event_id": event_id, "athlete_id": athlete_id, "recorded_at": date_seance}
    for col in COLONNES_GPS_NUMERIQUES:
        val = ligne.get(col)
        try:
            val = float(val)
            if val != val:  # NaN
                val = 0.0
        except (TypeError, ValueError):
            val = 0.0
        rec[col] = int(round(val)) if col in COLONNES_GPS_ENTIERES else round(val, 2)
    return rec


def _inserer_gps_en_s_adaptant(record):
    """
    Insère une ligne dans gps_reports en s'adaptant à la table réelle de Supabase :
    - colonne inexistante  -> on retire cette colonne et on réessaie (elle est signalée) ;
    - colonne de type entier -> on arrondit tous les nombres et on réessaie.
    Renvoie (ok, colonnes_ignorees, message_erreur).
    """
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
                # Postgres cite la valeur fautive : on n'arrondit que la/les colonne(s) concernée(s).
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
    """
    Enregistre les lignes GPS des joueurs reconnus dans la table gps_reports.
    Un ré-import pour la même séance REMPLACE les données du joueur (pas de doublons).
    Renvoie un dictionnaire :
      inseres, importes (noms), non_trouves, erreurs, colonnes_ignorees, verifie
    """
    resultat = {"inseres": 0, "importes": [], "non_trouves": [], "erreurs": [],
                "colonnes_ignorees": [], "verifie": None}

    date_seance = datetime.now().isoformat()
    events_par_athlete = {}  # athlete_id -> id de SA séance (même titre + même horaire)
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
            # "recorded_at" est facultative (la date est lue depuis la séance) : pas d'alerte pour elle.
            if c != "recorded_at" and c not in resultat["colonnes_ignorees"]:
                resultat["colonnes_ignorees"].append(c)
        if ok:
            resultat["inseres"] += 1
            resultat["importes"].append(p_name)
            ids_importes.add(athlete_id)
        else:
            resultat["erreurs"].append(f"{p_name} : {erreur}")

    # Vérification : relit la base pour confirmer que les lignes y sont vraiment
    if ids_importes:
        try:
            rel = supabase.table("gps_reports").select("athlete_id").in_("event_id", list(ids_events_utilises)).execute().data or []
            resultat["verifie"] = len([r for r in rel if r.get("athlete_id") in ids_importes])
        except Exception as e:
            resultat["erreurs"].append(f"Vérification impossible : {e}")
    return resultat


def obtenir_rapports_gps(athlete_id=None, event_id=None):
    """
    Rapports GPS (optionnellement filtrés), enrichis avec le titre et la date de la séance.
    Les séances sont lues séparément (aucune jointure Supabase nécessaire).
    """
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
    """
    Calcule le statut de disponibilité de chaque athlète en évaluant 
    les réponses aux questionnaires et les retours médicaux.[cite: 7]
    """
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
    """Toutes les lignes de réponses d'un athlète."""
    try:
        return supabase.table("questionnaire_responses").select("*").eq("athlete_id", athlete_id).execute().data or []
    except Exception as e:
        print(f"Erreur lecture des réponses : {e}")
        return []

def enregistrer_reponse_evenement(athlete_id, event_id, questionnaire_id, answers, rpe=None):
    """
    Enregistre (ou complète) les réponses d'un athlète pour une séance.
    S'adapte à la base : une ligne par questionnaire, ou une seule ligne par (athlète, séance)
    (dans ce cas les réponses sont fusionnées). La colonne "rpe" est facultative.
    """
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
    """Réponse d'un athlète pour une séance (réponses de tous les questionnaires fusionnées)."""
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
    """Questionnaire RPE (1-10) automatique de chaque séance (créé s'il n'existe pas encore)."""
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

def obtenir_assignations():
    try:
        res = supabase.table("questionnaire_assignments").select("*").execute()
        return res.data if res.data else []
    except:
        return []

def obtenir_fichiers_evenement(event_id):
    try:
        res = supabase.table("session_files").select("*").eq("event_id", event_id).execute()
        return res.data if res.data else []
    except:
        return []


# =====================================================================
# DATES FRANÇAISES
# =====================================================================
def parse_dt(valeur):
    """Texte ISO / date / datetime -> datetime naïf (ou None)."""
    if not valeur:
        return None
    try:
        if isinstance(valeur, datetime):
            return valeur.replace(tzinfo=None)
        return datetime.fromisoformat(str(valeur).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def fmt_date_fr(valeur, avec_heure=False):
    """'2026-10-08T15:00:00' -> '08/10/2026' (ou '08/10/2026 15:00')."""
    d = parse_dt(valeur)
    if not d:
        return str(valeur or "")[:16]
    return d.strftime("%d/%m/%Y %H:%M" if avec_heure else "%d/%m/%Y")


def cle_seance(ev):
    """Une « séance » = même titre + même horaire (une ligne `events` par athlète)."""
    return (ev.get("title") or "Séance", str(ev.get("start_time") or ""), str(ev.get("end_time") or ""))


def groupes_seances(events):
    groupes = {}
    for ev in events:
        groupes.setdefault(cle_seance(ev), []).append(ev)
    return groupes


# =====================================================================
# MISE À JOUR / INSERTION AVEC REPLI (colonnes facultatives)
# =====================================================================
def inserer_avec_repli(table, lignes, champs_optionnels):
    """Insère ; si une colonne facultative n'existe pas encore, réessaie sans elle.
    Renvoie (donnees_inserees, champs_ignores, erreur)."""
    try:
        res = supabase.table(table).insert(lignes).execute()
        return res.data or [], [], None
    except Exception as e1:
        presents = [c for c in champs_optionnels if any(c in l for l in lignes)]
        if not presents:
            return [], [], str(e1)
        try:
            allegees = [{k: v for k, v in l.items() if k not in champs_optionnels} for l in lignes]
            res = supabase.table(table).insert(allegees).execute()
            return res.data or [], presents, None
        except Exception as e2:
            return [], [], str(e2)


def maj_avec_repli(table, donnees, ids, champs_optionnels):
    """Met à jour plusieurs lignes (par id). Renvoie (ok, champs_ignores, erreur)."""
    try:
        supabase.table(table).update(donnees).in_("id", ids).execute()
        return True, [], None
    except Exception as e1:
        presents = [c for c in champs_optionnels if c in donnees]
        if not presents:
            return False, [], str(e1)
        try:
            allege = {k: v for k, v in donnees.items() if k not in champs_optionnels}
            supabase.table(table).update(allege).in_("id", ids).execute()
            return True, presents, None
        except Exception as e2:
            return False, [], str(e2)


# =====================================================================
# QUESTIONNAIRE AUTOMATIQUE « PRÉSENCE & BLESSURES »
# =====================================================================
FORMAT_DOULEUR = "pain_text"
FORMAT_PRESENCE = "presence"
TITRE_PRESENCE_AUTO = "Présence & Blessures (Auto)"
LABEL_PRESENCE = "Présence à la séance"
LABEL_BLESSURE_PRES = "Blessure (m'empêche de m'entraîner) ?"
LABEL_DOULEUR_PRES = "Douleur musculaire : zone concernée (écrire « non » si aucune)"
LABELS_PRESENCE = (LABEL_PRESENCE, LABEL_BLESSURE_PRES, LABEL_DOULEUR_PRES)

MOTS_CLES_DOULEUR = ("douleur", "courbature", "gêne", "pain")
REPONSES_SANS_DOULEUR = {
    "", "non", "no", "aucune", "aucun", "rien", "ras", "r.a.s", "néant", "neant", "none", "n/a", "na",
    "nan", "null", "-", "--", "0", "nope", "pas de douleur", "aucune douleur", "rien à signaler", "rien a signaler",
}


def est_questionnaire_auto(q):
    return bool(q) and q.get("title") in (TITRE_RPE_AUTO, TITRE_PRESENCE_AUTO)


def obtenir_ou_creer_presence_auto():
    """Questionnaire de présence (présence / blessure / douleur) ajouté à chaque séance."""
    try:
        ex = supabase.table("questionnaires").select("*").eq("title", TITRE_PRESENCE_AUTO).execute().data
        if ex:
            return ex[0]
        ins = supabase.table("questionnaires").insert({
            "title": TITRE_PRESENCE_AUTO,
            "type": "pre_event",
            "questions": [
                {"label": LABEL_PRESENCE, "format": FORMAT_PRESENCE},
                {"label": LABEL_BLESSURE_PRES, "format": FORMAT_BLESSURE},
                {"label": LABEL_DOULEUR_PRES, "format": FORMAT_DOULEUR},
            ],
        }).execute().data
        return ins[0] if ins else None
    except Exception as e:
        print(f"Erreur questionnaire présence auto : {e}")
        return None


def question_est_douleur(q):
    fmt = q.get("format")
    if fmt == FORMAT_DOULEUR:
        return True
    if fmt in (None, "text"):
        lbl = str(q.get("label", "")).lower()
        return any(m in lbl for m in MOTS_CLES_DOULEUR)
    return False


def reponse_douleur_significative(valeur):
    """True si la réponse décrit vraiment une douleur (ni vide, ni « non », ni « rien »...)."""
    txt = str(valeur if valeur is not None else "").strip().lower().strip(" .!?;,:")
    if txt in REPONSES_SANS_DOULEUR:
        return False
    mots = txt.split()
    if mots and mots[0] in ("non", "pas", "aucune", "aucun", "rien") and len(mots) <= 4:
        return False
    return True


def _est_oui(v):
    return str(v).strip().lower() in ("oui", "yes", "true", "1", "1.0")


def est_blesse(answers):
    """Blessure « Oui » ou douleur localisée (réponses de la page Présence & Blessures)."""
    answers = answers or {}
    return _est_oui(answers.get(LABEL_BLESSURE_PRES)) or reponse_douleur_significative(answers.get(LABEL_DOULEUR_PRES))


def _raison_blessure(answers):
    if _est_oui(answers.get(LABEL_BLESSURE_PRES)):
        return "Blessure"
    return f"Douleur : {str(answers.get(LABEL_DOULEUR_PRES)).strip()}"


def statut_presence(answers):
    """
    ('disponible' | 'absent' | 'indispo' | 'sans_reponse', raison)
    - disponible : présent, sans blessure ni douleur            -> compté dans l'effectif de la séance
    - absent     : répond Présence = Non (raison = blessure / douleur si blessé)
    - indispo    : PRÉSENT mais avec blessure ou douleur        -> présent en réathlétisation
    - sans_reponse : n'a pas encore répondu
    """
    answers = answers or {}
    presence = answers.get(LABEL_PRESENCE)
    if presence in (None, ""):
        return "sans_reponse", "Pas encore répondu"
    blesse = est_blesse(answers)
    if not _est_oui(presence):
        return "absent", (_raison_blessure(answers) if blesse else "Absent")
    if blesse:
        return "indispo", _raison_blessure(answers)
    return "disponible", ""


def obtenir_reponses_events(event_ids):
    """{event_id: réponses fusionnées (tous questionnaires)}"""
    res = {}
    ids = [i for i in event_ids if i]
    for i in range(0, len(ids), 80):
        try:
            rows = supabase.table("questionnaire_responses").select("*").in_("event_id", ids[i:i + 80]).execute().data or []
        except Exception as e:
            print(f"Erreur lecture réponses : {e}")
            rows = []
        for r in rows:
            res.setdefault(r.get("event_id"), {}).update(_lire_answers(r.get("answers")))
    return res


def calculer_effectif(events_groupe, reponses_par_event, noms):
    """
    Effectif d'une séance : listes de joueurs
    disponible (présents) / absent / indispo (présents en réathlétisation) / sans_reponse.
    Chaque joueur : {athlete_id, nom, raison, blesse}.
    """
    out = {"disponible": [], "absent": [], "indispo": [], "sans_reponse": []}
    for ev in events_groupe:
        answers = reponses_par_event.get(ev.get("id"), {})
        statut, raison = statut_presence(answers)
        out[statut].append({"athlete_id": ev.get("athlete_id"), "nom": noms.get(ev.get("athlete_id"), "?"),
                            "raison": raison, "blesse": est_blesse(answers)})
    for lst in out.values():
        lst.sort(key=lambda x: x["nom"])
    return out


def resume_effectif(eff):
    """Chiffres clés : présents, absents (dont blessés), présents en réathlétisation, sans réponse."""
    return {"presents": len(eff["disponible"]), "absents": len(eff["absent"]),
            "absents_blesses": len([x for x in eff["absent"] if x["blesse"]]),
            "rehab": len(eff["indispo"]), "sans_reponse": len(eff["sans_reponse"])}


# =====================================================================
# ASSIGNATIONS DES QUESTIONNAIRES
# =====================================================================
def assigner_questionnaire(questionnaire_id, athlete_id, event_id=None):
    """Assigne un questionnaire (sans doublon). Renvoie (ok, erreur)."""
    try:
        existantes = supabase.table("questionnaire_assignments").select("*").eq(
            "questionnaire_id", questionnaire_id).eq("athlete_id", athlete_id).execute().data or []
        if any(a.get("event_id") == event_id for a in existantes):
            return True, None
        supabase.table("questionnaire_assignments").insert(
            {"questionnaire_id": questionnaire_id, "athlete_id": athlete_id, "event_id": event_id}).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def supprimer_assignation(assignation):
    try:
        if assignation.get("id"):
            supabase.table("questionnaire_assignments").delete().eq("id", assignation["id"]).execute()
        else:
            q = supabase.table("questionnaire_assignments").delete().eq(
                "questionnaire_id", assignation["questionnaire_id"]).eq("athlete_id", assignation["athlete_id"])
            q = q.eq("event_id", assignation["event_id"]) if assignation.get("event_id") else q.is_("event_id", "null")
            q.execute()
        return True, None
    except Exception as e:
        return False, str(e)


def questionnaire_disponible_pour(q_id, athlete_id, event_id, assignations):
    """
    Sans aucune assignation, le questionnaire est ouvert à tous.
    Sinon il n'est proposé qu'aux athlètes assignés (toutes leurs séances, ou la séance précise).
    """
    lignes = [a for a in (assignations or []) if a.get("questionnaire_id") == q_id]
    if not lignes:
        return True
    return any(a.get("athlete_id") == athlete_id and a.get("event_id") in (None, event_id) for a in lignes)


# =====================================================================
# ALERTES COACH
# =====================================================================
LIBELLES_GPS = {
    "distance_totale_m": "Distance totale (m)",
    "distance_haute_intensite_m": "Distance haute intensité (m)",
    "distance_haute_vitesse_m": "Distance haute vitesse (m)",
    "distance_sprint_m": "Distance sprint (m)",
    "nb_accelerations": "Accélérations",
    "nb_decelerations": "Décélérations",
    "vmax_kmh": "Vmax (km/h)",
    "meterage_par_minute": "Distance par minute (m/min)",
    "duree_secondes": "Durée (min)",
}
METRIQUES_GPS_ALERTES = [m for m in COLONNES_GPS_NUMERIQUES if m != "duree_secondes"]


def extraire_rpe(answers, rpe_colonne=None):
    """RPE d'une réponse (colonne rpe, sinon une réponse dont l'intitulé contient « rpe »)."""
    try:
        if rpe_colonne not in (None, ""):
            return float(rpe_colonne)
    except (ValueError, TypeError):
        pass
    for k, v in (answers or {}).items():
        if "rpe" in str(k).lower():
            try:
                return float(v)
            except (ValueError, TypeError):
                continue
    return None


def _moyenne_ecart_type(valeurs):
    n = len(valeurs)
    m = sum(valeurs) / n
    s = (sum((x - m) ** 2 for x in valeurs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    return m, s


def _inhabituel(v, historique, n_min, z_min, plancher_s, diff_min):
    """Renvoie (moyenne, z) si v s'écarte nettement de l'historique, sinon None."""
    if len(historique) < n_min:
        return None
    m, s = _moyenne_ecart_type(historique)
    z = (v - m) / max(s, plancher_s(m))
    if abs(z) >= z_min and abs(v - m) >= diff_min(m):
        return m, z
    return None


def obtenir_donnees_alertes(coach_id=None):
    """Séances du coach + réponses + GPS (historique complet, nécessaire aux comparaisons)."""
    try:
        events = supabase.table("events").select("*").execute().data or []
    except Exception as e:
        print(f"Erreur lecture séances (alertes) : {e}")
        events = []
    if coach_id:
        events = [e for e in events if e.get("coach_id") in (None, coach_id)]
    ids = [e["id"] for e in events]
    reponses, gps = [], []
    for i in range(0, len(ids), 80):
        try:
            reponses += supabase.table("questionnaire_responses").select("*").in_("event_id", ids[i:i + 80]).execute().data or []
        except Exception as e:
            print(f"Erreur lecture réponses (alertes) : {e}")
        try:
            gps += supabase.table("gps_reports").select("*").in_("event_id", ids[i:i + 80]).execute().data or []
        except Exception as e:
            print(f"Erreur lecture GPS (alertes) : {e}")
    def _lire(table, cols):
        try:
            return supabase.table(table).select(cols).execute().data or []
        except Exception:
            return []
    return {"events": events, "reponses": reponses, "gps": gps,
            "questionnaires": _lire("questionnaires", "id, title, type, questions"),
            "profils": _lire("profiles", "id, full_name, role, team_id"),
            "equipes": _lire("teams", "id, name")}


def calculer_alertes(donnees, jours=30, seuil_rpe_joueur=2.0, seuil_rpe_equipe=2.0, maintenant=None):
    """
    Liste des alertes (la plus urgente d'abord) :
    douleur, blessure, rpe_joueur, rpe_equipe, wellness_stat (réponse inhabituelle), gps_stat (GPS inhabituel).
    """
    from collections import defaultdict
    now = maintenant or datetime.now()
    limite = now - timedelta(days=int(jours))
    events = donnees["events"]
    ev_by_id = {e["id"]: e for e in events}
    noms = {p["id"]: p.get("full_name", "Athlète") for p in donnees["profils"]}
    team_de = {p["id"]: p.get("team_id") for p in donnees["profils"]}
    equipes = {t["id"]: t.get("name", "Équipe") for t in donnees["equipes"]}

    defs_pre = {}
    for q in donnees["questionnaires"]:
        if q.get("type") == "pre_event":
            for qq in (q.get("questions") or []):
                if qq.get("label"):
                    defs_pre[qq["label"]] = qq

    parsed = []
    for r in donnees["reponses"]:
        ev = ev_by_id.get(r.get("event_id"))
        if ev and parse_dt(ev.get("start_time")):
            parsed.append((r, ev, _lire_answers(r.get("answers"))))

    # Historiques numériques du wellness
    hist_perso = defaultdict(list)    # (athlete, question) -> [(date, valeur, id_reponse)]
    hist_groupe = defaultdict(list)   # (séance, question)  -> [(athlete, valeur)]
    for r, ev, answers in parsed:
        for label, val in answers.items():
            qd = defs_pre.get(label)
            if qd and qd.get("format") in ("scale", "number") and label not in LABELS_PRESENCE:
                try:
                    v = float(val)
                except (ValueError, TypeError):
                    continue
                hist_perso[(r.get("athlete_id"), label)].append((parse_dt(ev["start_time"]), v, r["id"]))
                hist_groupe[(cle_seance(ev), label)].append((r.get("athlete_id"), v))

    def _base(aid, ev):
        return {"athlete": noms.get(aid, "Athlète inconnu"), "athlete_id": aid, "event_id": ev.get("id"),
                "seance": ev.get("title") or "Séance", "date": fmt_date_fr(ev.get("start_time"), True),
                "tri": str(ev.get("start_time") or "")}

    alertes = []
    for r, ev, answers in parsed:
        dt_ev = parse_dt(ev["start_time"])
        if dt_ev < limite:
            continue
        aid = r.get("athlete_id")
        base = _base(aid, ev)

        for label, val in answers.items():
            qd = defs_pre.get(label)
            if not qd:
                continue
            fmt = qd.get("format")
            if question_est_douleur(qd):
                if reponse_douleur_significative(val):
                    alertes.append({**base, "cle": f"douleur|{r['id']}|{label}", "type": "douleur", "gravite": "haute",
                                    "message": f"Douleur musculaire déclarée : « {str(val).strip()} »"})
            elif fmt == FORMAT_BLESSURE:
                if _est_oui(val):
                    alertes.append({**base, "cle": f"blessure|{r['id']}|{label}", "type": "blessure", "gravite": "haute",
                                    "message": "Blessure déclarée (réponse « Oui »)"})
            elif fmt in ("scale", "number") and label not in LABELS_PRESENCE:
                try:
                    v = float(val)
                except (ValueError, TypeError):
                    continue
                raisons = []
                perso = [x[1] for x in hist_perso[(aid, label)] if x[2] != r["id"] and x[0] < dt_ev]
                res = _inhabituel(v, perso, 5, 2.0, lambda m: 0.5, lambda m: 1.0)
                if res:
                    raisons.append(f"très différente de ses réponses habituelles (moyenne {res[0]:.1f})")
                groupe = [x[1] for x in hist_groupe[(cle_seance(ev), label)] if x[0] != aid]
                res = _inhabituel(v, groupe, 5, 2.5, lambda m: 0.5, lambda m: 1.5)
                if res:
                    raisons.append(f"très éloignée du reste du groupe (moyenne {res[0]:.1f})")
                if raisons:
                    alertes.append({**base, "cle": f"wellness_stat|{r['id']}|{label}", "type": "wellness_stat", "gravite": "moyenne",
                                    "message": f"Réponse extrême : « {label} » = {v:g}, " + " ; ".join(raisons)})

        rpe, cible = extraire_rpe(answers, r.get("rpe")), ev.get("target_rpe")
        if rpe is not None and cible is not None:
            try:
                ecart = rpe - float(cible)
                if abs(ecart) >= seuil_rpe_joueur:
                    alertes.append({**base, "cle": f"rpe_joueur|{r['id']}", "type": "rpe_joueur", "gravite": "moyenne",
                                    "message": f"RPE {rpe:g} pour un RPE cible de {float(cible):g} ({ecart:+.1f}) : "
                                               + ("séance ressentie plus dure que prévu" if ecart > 0 else "séance ressentie plus facile que prévu")})
            except (ValueError, TypeError):
                pass

    # RPE moyen du groupe vs cible
    groupes = defaultdict(list)
    for r, ev, answers in parsed:
        rpe = extraire_rpe(answers, r.get("rpe"))
        if rpe is not None and parse_dt(ev["start_time"]) >= limite:
            groupes[cle_seance(ev)].append((ev, r, rpe))
    for cle, items in groupes.items():
        if len(items) < 2:
            continue
        cibles = [e.get("target_rpe") for e, _, _ in items if e.get("target_rpe") is not None]
        if not cibles:
            continue
        cible = float(cibles[0])
        moyenne = sum(x[2] for x in items) / len(items)
        ecart = moyenne - cible
        if abs(ecart) >= seuil_rpe_equipe:
            teams = {team_de.get(r.get("athlete_id")) for _, r, _ in items}
            nom_g = equipes.get(next(iter(teams))) if len(teams) == 1 and None not in teams else None
            ev0 = items[0][0]
            alertes.append({"cle": f"rpe_equipe|{cle[0]}|{cle[1]}", "type": "rpe_equipe", "gravite": "moyenne",
                            "athlete": f"Équipe {nom_g}" if nom_g else f"Groupe ({len(items)} joueurs)", "athlete_id": None,
                            "event_id": ev0.get("id"), "seance": cle[0], "date": fmt_date_fr(ev0.get("start_time"), True),
                            "tri": str(ev0.get("start_time") or ""),
                            "message": f"RPE moyen {moyenne:.1f} pour un RPE cible de {cible:g} ({ecart:+.1f}) : "
                                       + ("séance plus dure que prévu pour le groupe" if ecart > 0 else "séance plus facile que prévu pour le groupe")})

    # GPS inhabituel
    gps_perso = defaultdict(list)
    gps_groupe = defaultdict(list)
    gps_rows = []
    for g in donnees["gps"]:
        ev = ev_by_id.get(g.get("event_id"))
        if not ev or not parse_dt(ev.get("start_time")):
            continue
        gps_rows.append((g, ev))
        for m in METRIQUES_GPS_ALERTES:
            try:
                v = float(g.get(m))
            except (ValueError, TypeError):
                continue
            gps_perso[(g.get("athlete_id"), m)].append((parse_dt(ev["start_time"]), v, g.get("id")))
            gps_groupe[(cle_seance(ev), m)].append((g.get("athlete_id"), v))
    for g, ev in gps_rows:
        dt_ev = parse_dt(ev["start_time"])
        if dt_ev < limite:
            continue
        aid = g.get("athlete_id")
        for m in METRIQUES_GPS_ALERTES:
            try:
                v = float(g.get(m))
            except (ValueError, TypeError):
                continue
            raisons = []
            perso = [x[1] for x in gps_perso[(aid, m)] if x[2] != g.get("id") and x[0] < dt_ev]
            res = _inhabituel(v, perso, 4, 2.0, lambda mm: 0.05 * abs(mm), lambda mm: 0.2 * abs(mm))
            if res:
                raisons.append(f"très différent de ses valeurs habituelles (moyenne {res[0]:.1f})")
            groupe = [x[1] for x in gps_groupe[(cle_seance(ev), m)] if x[0] != aid]
            res = _inhabituel(v, groupe, 5, 2.5, lambda mm: 0.05 * abs(mm), lambda mm: 0.25 * abs(mm))
            if res:
                raisons.append(f"très éloigné du reste du groupe (moyenne {res[0]:.1f})")
            if raisons:
                alertes.append({**_base(aid, ev), "cle": f"gps_stat|{g.get('id')}|{m}", "type": "gps_stat", "gravite": "moyenne",
                                "message": f"GPS inhabituel : {LIBELLES_GPS[m]} = {v:g}, " + " ; ".join(raisons)})

    ordre = {"haute": 0, "moyenne": 1}
    alertes.sort(key=lambda a: a["tri"], reverse=True)
    alertes.sort(key=lambda a: ordre.get(a["gravite"], 2))
    return alertes


# =====================================================================
# DONNÉES D'ANALYSE (tableaux prêts à filtrer / tracer)
# =====================================================================
def _date_obj(valeur):
    d = parse_dt(valeur)
    return d.date() if d else None


def construire_df_reponses(reponses, events_by_id, noms):
    """Une ligne par réponse : Joueur, Séance, Date (jour de la séance), Question, Valeur, Valeur_num."""
    rows = []
    for r in reponses:
        ev = events_by_id.get(r.get("event_id"), {})
        d = _date_obj(ev.get("start_time")) or _date_obj(r.get("submitted_at"))
        for k, v in _lire_answers(r.get("answers")).items():
            try:
                vn = float(v)
            except (ValueError, TypeError):
                vn = float("nan")
            rows.append({
                "Joueur": noms.get(r.get("athlete_id"), "Athlète inconnu"), "athlete_id": r.get("athlete_id"),
                "event_id": r.get("event_id"), "Séance": ev.get("title") or "—", "DateObj": d,
                "Date": d.strftime("%d/%m/%Y") if d else "", "Question": str(k),
                "Valeur": (f"{vn:g}" if vn == vn else str(v)), "Valeur_num": vn,
            })
    return pd.DataFrame(rows, columns=["Joueur", "athlete_id", "event_id", "Séance", "DateObj", "Date", "Question", "Valeur", "Valeur_num"])


def construire_df_gps(rapports, events_by_id, noms):
    """Une ligne par rapport GPS ; la durée est convertie de secondes en minutes."""
    rows = []
    for g in rapports:
        ev = events_by_id.get(g.get("event_id"), {})
        d = _date_obj(ev.get("start_time") or g.get("seance_date"))
        ligne = {"Joueur": noms.get(g.get("athlete_id"), "Athlète inconnu"), "athlete_id": g.get("athlete_id"),
                 "event_id": g.get("event_id"), "Séance": ev.get("title") or g.get("seance_titre") or "Séance",
                 "DateObj": d, "Date": d.strftime("%d/%m/%Y") if d else ""}
        for m in COLONNES_GPS_NUMERIQUES:
            v = g.get(m)
            if m == "duree_secondes" and v is not None:
                try:
                    v = round(float(v) / 60.0, 1)
                except (ValueError, TypeError):
                    pass
            ligne[LIBELLES_GPS[m]] = v
        rows.append(ligne)
    base = ["Joueur", "athlete_id", "event_id", "Séance", "DateObj", "Date"] + [LIBELLES_GPS[m] for m in COLONNES_GPS_NUMERIQUES]
    df = pd.DataFrame(rows, columns=base)
    for m in COLONNES_GPS_NUMERIQUES:
        df[LIBELLES_GPS[m]] = pd.to_numeric(df[LIBELLES_GPS[m]], errors="coerce")
    return df


def filtrer_periode(df, debut=None, fin=None):
    if df is None or df.empty or (debut is None and fin is None):
        return df
    masque = df["DateObj"].notna()
    if debut is not None:
        masque &= df["DateObj"] >= debut
    if fin is not None:
        masque &= df["DateObj"] <= fin
    return df[masque]


def stats_par_question(df, afficher_joueur=False):
    """
    Une ligne par question : moyenne / min / max pour les réponses numériques,
    et les dernières réponses pour les questions texte (douleurs, commentaires...).
    """
    cols = ["Question", "Type", "Moyenne", "Min", "Max", "Nb réponses", "Réponses texte"]
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    base = df[~df["Question"].isin((LABEL_PRESENCE, LABEL_BLESSURE_PRES))]
    lignes = []
    for q, g in base.groupby("Question", sort=True):
        num = g[g["Valeur_num"].notna()]
        txt = g[g["Valeur_num"].isna()]
        if q == LABEL_DOULEUR_PRES:
            txt = txt[txt["Valeur"].apply(reponse_douleur_significative)]
        if len(num) and len(num) >= len(txt):
            lignes.append({"Question": q, "Type": "Numérique", "Moyenne": round(float(num["Valeur_num"].mean()), 2),
                           "Min": round(float(num["Valeur_num"].min()), 2), "Max": round(float(num["Valeur_num"].max()), 2),
                           "Nb réponses": int(len(num)), "Réponses texte": ""})
        elif len(txt):
            recents = txt.sort_values("DateObj", ascending=False, na_position="last").head(6)
            liste = [f"{r['Valeur']}" + (f" ({r['Joueur']})" if afficher_joueur else "") for _, r in recents.iterrows()]
            lignes.append({"Question": q, "Type": "Texte", "Moyenne": None, "Min": None, "Max": None,
                           "Nb réponses": int(len(txt)), "Réponses texte": " · ".join(liste)})
    return pd.DataFrame(lignes, columns=cols)


def reponses_texte(df):
    """Toutes les réponses texte (hors présence / blessure Oui-Non, hors « aucune douleur »)."""
    if df is None or df.empty:
        return pd.DataFrame()
    t = df[df["Valeur_num"].isna() & ~df["Question"].isin((LABEL_PRESENCE, LABEL_BLESSURE_PRES))]
    masque = ~((t["Question"] == LABEL_DOULEUR_PRES) & ~t["Valeur"].apply(reponse_douleur_significative))
    return t[masque]


def table_rpe_vs_cible(df_resp, events_by_id):
    """RPE réalisé (moyenne par séance) comparé au RPE cible prévu sur la séance."""
    cols = ["Séance", "Date", "DateObj", "RPE réalisé", "RPE cible", "Écart", "Nb réponses"]
    if df_resp is None or df_resp.empty:
        return pd.DataFrame(columns=cols)
    rpe = df_resp[df_resp["Question"].str.lower().str.contains("rpe") & df_resp["Valeur_num"].notna()]
    rows = {}
    for _, r in rpe.iterrows():
        ev = events_by_id.get(r["event_id"], {})
        cle = cle_seance(ev) if ev else (r["Séance"], str(r["event_id"]), "")
        d = rows.setdefault(cle, {"Séance": r["Séance"], "Date": r["Date"], "DateObj": r["DateObj"], "vals": [], "cibles": []})
        d["vals"].append(r["Valeur_num"])
        if ev.get("target_rpe") is not None:
            try:
                d["cibles"].append(float(ev["target_rpe"]))
            except (ValueError, TypeError):
                pass
    out = []
    for d in rows.values():
        reel = round(sum(d["vals"]) / len(d["vals"]), 2)
        cible = d["cibles"][0] if d["cibles"] else None
        out.append({"Séance": d["Séance"], "Date": d["Date"], "DateObj": d["DateObj"], "RPE réalisé": reel,
                    "RPE cible": cible, "Écart": round(reel - cible, 2) if cible is not None else None,
                    "Nb réponses": len(d["vals"])})
    df = pd.DataFrame(out, columns=cols)
    return df.sort_values("DateObj") if not df.empty else df


LIBELLE_CIBLE = "🎯 RPE cible"


def construire_df_cible(events_by_id, noms, debut=None, fin=None):
    """Une ligne par séance ayant un RPE cible (même format que construire_df_reponses)."""
    rows = []
    for ev in events_by_id.values():
        if ev.get("target_rpe") is None:
            continue
        d = _date_obj(ev.get("start_time"))
        if not d or (debut and d < debut) or (fin and d > fin):
            continue
        try:
            v = float(ev["target_rpe"])
        except (ValueError, TypeError):
            continue
        rows.append({"Joueur": noms.get(ev.get("athlete_id"), ""), "athlete_id": ev.get("athlete_id"), "event_id": ev.get("id"),
                     "Séance": ev.get("title") or "—", "DateObj": d, "Date": d.strftime("%d/%m/%Y"),
                     "Question": LIBELLE_CIBLE, "Valeur": f"{v:g}", "Valeur_num": v})
    return pd.DataFrame(rows, columns=["Joueur", "athlete_id", "event_id", "Séance", "DateObj", "Date", "Question", "Valeur", "Valeur_num"])
