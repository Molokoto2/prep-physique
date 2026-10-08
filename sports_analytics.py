import os
import io
import csv
import re
import json
import datetime
import unicodedata
import pandas as pd
from supabase import create_client, Client

# ==========================================
# CONNEXION SUPABASE
# ==========================================
# IMPORTANT (sécurité) :
# La clé secrète ne doit JAMAIS être écrite en dur dans ce fichier.
# Elle est lue depuis les variables d'environnement, ou depuis
# .streamlit/secrets.toml si vous lancez l'app avec Streamlit.
#
# .streamlit/secrets.toml :
#   SUPABASE_URL = "https://xxxx.supabase.co"
#   SUPABASE_KEY = "sb_secret_...."
#
# Sous Windows (invite de commande), avant de lancer le logiciel :
#   set SUPABASE_URL=https://xxxx.supabase.co
#   set SUPABASE_KEY=sb_secret_....
#
# Pensez à régénérer votre clé dans Supabase (Project Settings > API)
# si l'ancienne a déjà été partagée ou committée quelque part.

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
    raise RuntimeError(
        "SUPABASE_KEY manquante. Définissez-la en variable d'environnement ou dans "
        ".streamlit/secrets.toml avant de lancer le logiciel. "
        "Régénérez votre clé Supabase si l'ancienne a été exposée."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================================
# AUTHENTIFICATION & GESTION DES COMPTES
# ==========================================
# Rôles gérés : "coach" et "athlete". Un compte (Supabase Auth + ligne
# dans "profiles") est indispensable pour se connecter au logiciel ou
# à l'application mobile.

def connexion(email: str, password: str):
    """
    Tente une connexion. Renvoie (session, profile, erreur).
    - En cas de succès : (session, profile_dict, None)
    - En cas d'échec    : (None, None, "message d'erreur")
    """
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if not res.user:
            return None, None, "Identifiants invalides."
        profile_res = supabase.table("profiles").select("*").eq("id", res.user.id).single().execute()
        profile = profile_res.data
        if not profile:
            return None, None, "Compte authentifié mais aucun profil associé (contactez l'administrateur)."
        return res.session, profile, None
    except Exception as e:
        msg = str(e)
        if "Invalid login credentials" in msg:
            return None, None, "E-mail ou mot de passe incorrect."
        return None, None, f"Erreur de connexion : {msg}"


def deconnexion():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass


def creer_compte(email: str, password: str, full_name: str, role: str, team_id: str = None):
    """
    Crée un compte de connexion (Supabase Auth) + un profil ("coach" ou "athlete").
    """
    if role not in ("coach", "athlete"):
        return False, "Rôle invalide (doit être 'coach' ou 'athlete')."
    try:
        res = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name}
        })
        if res.user:
            user_id = res.user.id
            supabase.table("profiles").upsert({
                "id": user_id,
                "full_name": full_name,
                "role": role,
                "team_id": team_id if team_id else None
            }).execute()
            return True, f"Compte {role} créé avec succès pour {full_name} !"
        return False, "Erreur : impossible de créer l'utilisateur."
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg or "already been registered" in error_msg:
            return False, f"L'adresse {email} existe déjà sur Supabase."
        return False, f"Erreur lors de la création du compte : {error_msg}"


def modifier_compte(user_id: str, full_name: str = None, role: str = None,
                     team_id=None, new_password: str = None, new_email: str = None):
    """Met à jour le profil et/ou les identifiants de connexion d'un compte existant."""
    try:
        auth_updates = {}
        if new_password:
            auth_updates["password"] = new_password
        if new_email:
            auth_updates["email"] = new_email
        if auth_updates:
            supabase.auth.admin.update_user_by_id(user_id, auth_updates)

        profile_updates = {}
        if full_name is not None:
            profile_updates["full_name"] = full_name
        if role is not None:
            profile_updates["role"] = role
        if team_id is not None:
            profile_updates["team_id"] = team_id if team_id != "" else None
        if profile_updates:
            supabase.table("profiles").update(profile_updates).eq("id", user_id).execute()

        return True, "Compte mis à jour avec succès."
    except Exception as e:
        return False, f"Erreur lors de la mise à jour : {e}"


def supprimer_compte(user_id: str):
    """Supprime définitivement le profil ET le compte de connexion associé."""
    try:
        supabase.table("profiles").delete().eq("id", user_id).execute()
        supabase.auth.admin.delete_user(user_id)
        return True, "Compte supprimé définitivement."
    except Exception as e:
        return False, f"Erreur lors de la suppression : {e}"


def lister_comptes():
    """Renvoie tous les profils (coachs + athlètes) pour l'écran de gestion des comptes."""
    try:
        return supabase.table("profiles").select("*").order("role").execute().data or []
    except Exception as e:
        print(f"Erreur récupération des comptes : {e}")
        return []


# ==========================================
# GESTION DES QUESTIONNAIRES & AUTOMATION
# ==========================================

def configurer_questionnaire_automatique(questionnaire_id: str, timing: str, minutes: int, exclure_athlete_ids: list = None):
    supabase.table("questionnaires").update({
        "is_auto_assign": True,
        "trigger_timing": timing,
        "trigger_minutes": minutes
    }).eq("id", questionnaire_id).execute()

    supabase.table("questionnaire_exclusions").delete().eq("questionnaire_id", questionnaire_id).execute()
    if exclure_athlete_ids:
        exclusions = [{"questionnaire_id": questionnaire_id, "athlete_id": a_id} for a_id in exclure_athlete_ids]
        supabase.table("questionnaire_exclusions").insert(exclusions).execute()


def supprimer_questionnaire(questionnaire_id: str):
    return supabase.table("questionnaires").delete().eq("id", questionnaire_id).execute()


def definir_type_questionnaire(questionnaire_id: str, type_questionnaire: str):
    """Change le type d'un questionnaire ('pre_event' = avant séance, 'post_event' = après séance)."""
    supabase.table("questionnaires").update({"type": type_questionnaire}).eq("id", questionnaire_id).execute()


def obtenir_fichiers_evenement(event_id: str):
    """Récupère les documents (PDF/images) publiés pour une séance donnée."""
    try:
        return supabase.table("session_files").select("*").eq("event_id", event_id).order("created_at", desc=True).execute().data or []
    except Exception as e:
        print(f"Erreur récupération fichiers de la séance : {e}")
        return []


def definir_minutes_avant(questionnaire_id: str, minutes: int):
    """Définit le délai (en minutes) avant le début de la séance auquel un questionnaire Pre-Event s'ouvre."""
    supabase.table("questionnaires").update({"trigger_minutes": int(minutes)}).eq("id", questionnaire_id).execute()


def definir_minutes_apres(questionnaire_id: str, minutes: int):
    """Définit la durée (en minutes) pendant laquelle un questionnaire Post-Event (RPE) reste ouvert après la fin de la séance."""
    supabase.table("questionnaires").update({"post_window_minutes": int(minutes)}).eq("id", questionnaire_id).execute()


def assigner_questionnaire(questionnaire_id: str, athlete_id: str, event_id: str = None):
    """
    Assigne un questionnaire à un athlète : soit pour TOUTES ses séances
    (event_id=None), soit pour UNE séance précise (event_id fourni).
    Remplace une assignation identique existante au lieu de planter sur une
    contrainte d'unicité (suppression puis recréation).
    """
    try:
        req = supabase.table("questionnaire_assignments").delete().eq(
            "questionnaire_id", questionnaire_id
        ).eq("athlete_id", athlete_id)
        req = req.is_("event_id", None) if event_id is None else req.eq("event_id", event_id)
        req.execute()
    except Exception:
        pass
    supabase.table("questionnaire_assignments").insert({
        "questionnaire_id": questionnaire_id,
        "athlete_id": athlete_id,
        "event_id": event_id,
        "is_active": True,
    }).execute()


def obtenir_assignations():
    """Renvoie toutes les lignes de la table questionnaire_assignments."""
    try:
        return supabase.table("questionnaire_assignments").select("*").execute().data or []
    except Exception as e:
        print(f"Erreur récupération des assignations : {e}")
        return []


def questionnaire_disponible_pour(questionnaire_id: str, athlete_id: str, event_id: str, assignations: list) -> bool:
    """
    Détermine si un questionnaire doit être proposé à un athlète pour une séance
    donnée. Si ce questionnaire n'a AUCUNE assignation configurée nulle part, il
    est considéré ouvert à tous par défaut (pour ne rien bloquer si le coach n'a
    jamais utilisé la fonction d'assignation). Dès qu'au moins une assignation
    existe pour ce questionnaire, seuls les athlètes/séances explicitement
    assignés (toutes séances, ou cette séance précise) y ont accès.
    """
    assignations_q = [a for a in assignations if a.get("questionnaire_id") == questionnaire_id]
    if not assignations_q:
        return True
    for a in assignations_q:
        if a.get("athlete_id") != athlete_id:
            continue
        if a.get("event_id") is None or a.get("event_id") == event_id:
            return True
    return False


# ==========================================
# GESTION DES PROFILS & ÉQUIPES
# ==========================================

def ajouter_athlete_manual(email: str, password: str, full_name: str, team_id: str = None):
    # Conservé pour compatibilité ; utilise désormais creer_compte() en interne.
    return creer_compte(email, password, full_name, role="athlete", team_id=team_id)


def modifier_athlete(athlete_id: str, new_name: str, new_team_id: str = None):
    data = {"full_name": new_name, "team_id": new_team_id if new_team_id else None}
    return supabase.table("profiles").update(data).eq("id", athlete_id).execute()


def supprimer_profil_athlete(athlete_id: str):
    return supabase.table("profiles").delete().eq("id", athlete_id).execute()


def creer_equipe(nom_equipe: str):
    return supabase.table("teams").insert({"name": nom_equipe}).execute()


def supprimer_equipe(team_id: str):
    return supabase.table("teams").delete().eq("id", team_id).execute()


# ==========================================
# BLESSURES / DISPONIBILITÉ
# ==========================================
# Une question de questionnaire peut être marquée comme "injury_flag"
# (Oui/Non). La dernière réponse à une telle question fait foi pour
# déterminer si un athlète est actuellement "disponible" ou
# "en réathlétisation".

FORMAT_BLESSURE = "injury_flag"


def enregistrer_reponse_evenement(athlete_id: str, event_id: str, questionnaire_id: str, nouvelles_reponses: dict, rpe_score: float = None):
    """
    Enregistre (ou complète) la réponse aux questionnaires d'un athlète pour une
    séance donnée. La base n'autorise qu'UNE seule ligne par (athlete_id, event_id) :
    les nouvelles réponses sont donc fusionnées avec celles déjà présentes
    (ex : Wellness répondu avant la séance, puis RPE après), sans écraser les
    anciennes. Le questionnaire_id d'origine est conservé (utile pour la
    détection de blessure, qui se base sur le premier questionnaire lié).
    """
    try:
        existant = supabase.table("questionnaire_responses").select("*").eq(
            "athlete_id", athlete_id
        ).eq("event_id", event_id).execute().data
        deja = existant[0] if existant else None

        reponses_existantes = (deja or {}).get("answers") or {}
        if isinstance(reponses_existantes, str):
            try:
                reponses_existantes = json.loads(reponses_existantes)
            except Exception:
                reponses_existantes = {}

        reponses_fusionnees = dict(reponses_existantes)
        reponses_fusionnees.update(nouvelles_reponses)

        payload = {
            "athlete_id": athlete_id,
            "event_id": event_id,
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
    """Renvoie la réponse déjà enregistrée pour cet athlète et cette séance (ou None)."""
    try:
        res = supabase.table("questionnaire_responses").select("*").eq(
            "athlete_id", athlete_id
        ).eq("event_id", event_id).execute().data
        return res[0] if res else None
    except Exception as e:
        print(f"Erreur récupération réponse événement : {e}")
        return None


def obtenir_reponses_avec_definitions():
    """Réponses aux questionnaires, avec la définition des questions jointe (pour retrouver les questions blessure)."""
    try:
        res = supabase.table("questionnaire_responses").select(
            "id, athlete_id, rpe_score, answers, submitted_at, questionnaire_id, questionnaires(questions)"
        ).order("submitted_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        print(f"Erreur lors de la récupération des réponses (avec définitions) : {e}")
        return []


def calculer_statut_disponibilite(profiles: list, responses: list):
    """
    Détermine, pour chaque athlète, son statut de disponibilité à partir de
    la dernière réponse connue à une question de type "injury_flag".

    Renvoie { athlete_id: {"statut": "disponible" | "blesse", "depuis": "YYYY-MM-DD" | None} }
    Par défaut (aucune réponse blessure trouvée) : "disponible".
    """
    statuts = {
        p["id"]: {"statut": "disponible", "depuis": None}
        for p in profiles if p.get("role") == "athlete"
    }
    dernieres = {}  # athlete_id -> (date_str, valeur_reponse)

    for r in responses:
        athlete_id = r.get("athlete_id")
        if athlete_id not in statuts:
            continue

        answers = r.get("answers", {})
        if isinstance(answers, str):
            try:
                answers = json.loads(answers)
            except Exception:
                answers = {}
        if not isinstance(answers, dict):
            continue

        questionnaire = r.get("questionnaires") or {}
        questions_def = questionnaire.get("questions", []) if isinstance(questionnaire, dict) else []
        labels_blessure = [q.get("label") for q in questions_def if q.get("format") == FORMAT_BLESSURE]

        for lbl in labels_blessure:
            if lbl in answers:
                date_rep = r.get("submitted_at", "") or ""
                prev = dernieres.get(athlete_id)
                if prev is None or date_rep > prev[0]:
                    dernieres[athlete_id] = (date_rep, answers[lbl])

    for athlete_id, (date_rep, valeur) in dernieres.items():
        est_blesse = str(valeur).strip().lower() in ("oui", "yes", "true", "1")
        statuts[athlete_id] = {
            "statut": "blesse" if est_blesse else "disponible",
            "depuis": date_rep[:10] if date_rep else None,
        }

    return statuts


# ==========================================
# RAPPORTS GPS
# ==========================================
# Le club utilise toujours le même gabarit d'export (système GPS type
# Catapult/Titan) : des lignes d'en-tête (Date, Heure...), puis un tableau
# avec une colonne "Player Name" et une colonne "Period Name". On ne garde
# que les lignes où Period Name = "Session".
#
# Colonnes du fichier -> clé interne utilisée dans le logiciel.
COLONNES_GPS_CATAPULT = {
    "Acceleration Efforts": "nb_accelerations",
    "Deceleration Efforts": "nb_decelerations",
    "Duration": "duree_secondes",
    "Distance": "distance_totale_m",
    "Max Velocity": "vmax_kmh",
    "Meterage Per Minute": "meterage_par_minute",
    "Sprint Distance": "distance_sprint_m",
    "HI Distance": "distance_haute_intensite_m",
    "High Speed Distance": "distance_haute_vitesse_m",
}

# Métriques numériques GPS utilisées dans l'analytique.
COLONNES_GPS_NUMERIQUES = [
    "distance_totale_m", "distance_haute_intensite_m", "distance_haute_vitesse_m",
    "distance_sprint_m", "nb_accelerations", "nb_decelerations",
    "vmax_kmh", "meterage_par_minute", "duree_secondes",
]

PERIODE_A_CONSERVER = "session"


def _normaliser_entete(txt) -> str:
    return str(txt).strip().lower()


def _cle_nom(s: str) -> str:
    """
    Normalise un nom pour la comparaison : sans accents, sans ponctuation,
    insensible à la casse et à l'ordre des mots (ex: "Loic DUFAU." et
    "Loïc Dufau" donnent la même clé).
    """
    s = str(s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z\s]", " ", s)
    return " ".join(sorted(s.upper().split()))


def matcher_nom_athlete(nom_fichier: str, dict_athletes: dict):
    """Retrouve l'athlete_id dont le nom correspond (accents/majuscules/ordre ignorés)."""
    cle_cherchee = _cle_nom(nom_fichier)
    if not cle_cherchee:
        return None
    for nom, athlete_id in dict_athletes.items():
        if _cle_nom(nom) == cle_cherchee:
            return athlete_id
    return None


def _parser_nombre_fr(val):
    """Convertit un nombre au format français ('9149,37') en float."""
    if val is None:
        return None
    val = str(val).strip().strip('"')
    if val == "":
        return None
    val = val.replace(" ", "").replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return None


def _parser_duree_hms(val):
    """Convertit une durée 'HH:MM:SS' en nombre de secondes."""
    if not val:
        return None
    m = re.match(r"^(\d+):(\d{2}):(\d{2})$", str(val).strip().strip('"'))
    if not m:
        return None
    h, mn, s = (int(x) for x in m.groups())
    return h * 3600 + mn * 60 + s


def _lire_rapport_catapult(texte: str):
    """Parse le gabarit fixe du club (voir en-tête du module) et ne garde que la période 'Session'."""
    lignes_brutes = texte.splitlines()
    idx_entete = next(
        (i for i, l in enumerate(lignes_brutes) if "Player Name" in l and "Period Name" in l),
        None
    )
    if idx_entete is None:
        raise ValueError("En-tête 'Player Name' / 'Period Name' introuvable dans le fichier.")

    reader = csv.reader(lignes_brutes[idx_entete:], delimiter=";")
    entetes = [e.strip().strip('"') for e in next(reader)]

    try:
        idx_nom = entetes.index("Player Name")
        idx_periode = entetes.index("Period Name")
    except ValueError:
        raise ValueError("Colonnes 'Player Name' ou 'Period Name' manquantes dans l'en-tête du fichier.")

    idx_colonnes = {col: entetes.index(col) for col in COLONNES_GPS_CATAPULT if col in entetes}
    colonnes_absentes = [col for col in COLONNES_GPS_CATAPULT if col not in entetes]

    lignes = []
    for row in reader:
        if len(row) <= max(idx_nom, idx_periode):
            continue
        if row[idx_periode].strip().strip('"').lower() != PERIODE_A_CONSERVER:
            continue
        nom_joueur = row[idx_nom].strip().strip('"')
        if not nom_joueur:
            continue

        ligne = {"nom_joueur": nom_joueur}
        for col_fichier, cle_interne in COLONNES_GPS_CATAPULT.items():
            idx_col = idx_colonnes.get(col_fichier)
            if idx_col is None or idx_col >= len(row):
                continue
            valeur_brute = row[idx_col]
            ligne[cle_interne] = _parser_duree_hms(valeur_brute) if cle_interne == "duree_secondes" else _parser_nombre_fr(valeur_brute)
        lignes.append(ligne)

    if colonnes_absentes:
        print(f"⚠️ Colonnes GPS attendues mais absentes du fichier : {colonnes_absentes}")

    return lignes


def _lire_fichier_gps_generique(file_bytes: bytes, nom_fichier: str = ""):
    """
    Repli utilisé si le fichier n'a pas le gabarit fixe du club : lecture
    Excel/CSV "à colonnes libres" en devinant les intitulés courants.
    """
    mapping_generique = {
        "joueur": "nom_joueur", "athlete": "nom_joueur", "athlète": "nom_joueur",
        "nom": "nom_joueur", "nom du joueur": "nom_joueur", "player name": "nom_joueur",
        "distance totale (m)": "distance_totale_m", "distance": "distance_totale_m",
        "distance (m)": "distance_totale_m",
        "distance haute intensité (m)": "distance_haute_intensite_m", "hi distance": "distance_haute_intensite_m",
        "distance sprint (m)": "distance_sprint_m", "sprint distance": "distance_sprint_m",
        "accélérations": "nb_accelerations", "acceleration efforts": "nb_accelerations",
        "décélérations": "nb_decelerations", "deceleration efforts": "nb_decelerations",
        "vmax (km/h)": "vmax_kmh", "max velocity": "vmax_kmh",
        "meterage per minute": "meterage_par_minute",
        "high speed distance": "distance_haute_vitesse_m",
        "duration": "duree_secondes",
    }

    df = None
    erreurs = []
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    except Exception as e:
        erreurs.append(f"xlsx (openpyxl) : {e}")
    if df is None:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
        except ImportError:
            erreurs.append("xls (xlrd) : le paquet 'xlrd' n'est pas installé (pip install xlrd)")
        except Exception as e:
            erreurs.append(f"xls (xlrd) : {e}")
    if df is None:
        for encodage in ("utf-8", "cp1252", "latin1"):
            for sep in (",", ";", "\t"):
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding=encodage, engine="python")
                    if df.shape[1] > 1:
                        break
                    df = None
                except Exception as e:
                    erreurs.append(f"csv (sep='{sep}', encodage='{encodage}') : {e}")
            if df is not None:
                break
    if df is None:
        raise ValueError(
            "Format de fichier non reconnu (ni gabarit GPS du club, ni .xlsx, ni .xls, ni .csv exploitable). "
            f"Nom du fichier : '{nom_fichier}'. Détails techniques : " + " | ".join(erreurs)
        )

    df.columns = [_normaliser_entete(c) for c in df.columns]
    lignes = []
    for _, row in df.iterrows():
        ligne = {}
        for col in df.columns:
            cle = mapping_generique.get(col)
            val = row[col]
            if pd.isna(val):
                val = None
            if cle and val is not None:
                if cle == "duree_secondes":
                    ligne[cle] = _parser_duree_hms(val) if isinstance(val, str) else val
                elif cle != "nom_joueur":
                    try:
                        ligne[cle] = float(str(val).replace(",", "."))
                    except (ValueError, TypeError):
                        pass
                else:
                    ligne[cle] = val
        if ligne.get("nom_joueur"):
            lignes.append(ligne)
    return lignes


def lire_fichier_gps(file_bytes: bytes, nom_fichier: str = ""):
    """
    Point d'entrée unique pour lire un rapport GPS. Détecte automatiquement
    le gabarit fixe du club (export CSV Catapult/Titan) ; si le fichier n'a
    pas ce format, se rabat sur une lecture Excel/CSV générique.
    """
    texte = None
    for encodage in ("utf-8-sig", "cp1252", "latin1"):
        try:
            texte = file_bytes.decode(encodage)
            break
        except UnicodeDecodeError:
            continue

    if texte and "Player Name" in texte and "Period Name" in texte:
        return _lire_rapport_catapult(texte)

    return _lire_fichier_gps_generique(file_bytes, nom_fichier)


def enregistrer_rapport_gps(event_id: str, lignes: list, dict_athletes: dict):
    """
    Associe chaque ligne GPS à un athlete_id (par correspondance de nom,
    insensible aux accents/majuscules/ordre) et l'insère dans "gps_reports".
    Renvoie (nb_inseres, [noms_non_reconnus]).
    """
    inseres = 0
    non_trouves = []
    for ligne in lignes:
        nom = str(ligne.get("nom_joueur", "")).strip()
        athlete_id = matcher_nom_athlete(nom, dict_athletes)
        if not athlete_id:
            non_trouves.append(nom)
            continue
        record = {
            "event_id": event_id,
            "athlete_id": athlete_id,
            "distance_totale_m": ligne.get("distance_totale_m"),
            "distance_haute_intensite_m": ligne.get("distance_haute_intensite_m"),
            "distance_haute_vitesse_m": ligne.get("distance_haute_vitesse_m"),
            "distance_sprint_m": ligne.get("distance_sprint_m"),
            "nb_accelerations": ligne.get("nb_accelerations"),
            "nb_decelerations": ligne.get("nb_decelerations"),
            "vmax_kmh": ligne.get("vmax_kmh"),
            "meterage_par_minute": ligne.get("meterage_par_minute"),
            "duree_secondes": ligne.get("duree_secondes"),
            "donnees_brutes": {k: v for k, v in ligne.items() if k != "nom_joueur"},
            "created_at": datetime.datetime.now().isoformat(),
        }
        try:
            supabase.table("gps_reports").insert(record).execute()
            inseres += 1
        except Exception as e:
            print(f"Erreur insertion GPS pour {nom} : {e}")
            non_trouves.append(f"{nom} (erreur DB)")
    return inseres, non_trouves


def obtenir_rapports_gps(athlete_id: str = None, event_id: str = None):
    """Récupère les rapports GPS, éventuellement filtrés par athlète et/ou séance."""
    try:
        q = supabase.table("gps_reports").select("*, events(title, start_time)")
        if athlete_id:
            q = q.eq("athlete_id", athlete_id)
        if event_id:
            q = q.eq("event_id", event_id)
        return q.order("created_at", desc=True).execute().data or []
    except Exception as e:
        print(f"Erreur lors de la récupération des rapports GPS : {e}")
        return []


# ==========================================
# LECTURE DES DONNÉES
# ==========================================

def obtenir_reponses_brutes_athlete(athlete_id):
    """
    Récupère toutes les réponses brutes aux questionnaires d'un athlète spécifique.
    """
    try:
        # Requête sans .order() pour éviter le plantage TypeError sur la librairie Python
        res = supabase.table("questionnaire_responses").select(
            "id, rpe_score, answers, submitted_at, events(title)"
        ).eq("athlete_id", athlete_id).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Erreur lors de la récupération des réponses : {e}")
        return []


def obtenir_donnees_wellness_graphique(athlete_id):
    """
    Récupère et prépare les données RPE et Wellness d'un athlète pour l'affichage graphique.
    """
    try:
        res = supabase.table("questionnaire_responses").select(
            "submitted_at, rpe_score"
        ).eq("athlete_id", athlete_id).execute()

        if not res.data:
            return {"dates": [], "rpe": []}

        dates = []
        rpe_scores = []

        for item in res.data:
            sub_date = item.get("submitted_at")
            rpe = item.get("rpe_score")
            if sub_date and rpe is not None:
                # Formatage de la date (YYYY-MM-DD)
                dates.append(sub_date[:10])
                rpe_scores.append(float(rpe))

        return {"dates": dates, "rpe": rpe_scores}
    except Exception as e:
        print(f"Erreur lors de la récupération des données graphiques : {e}")
        return {"dates": [], "rpe": []}
