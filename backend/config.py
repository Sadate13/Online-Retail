"""
Fichier de configuration du projet : TOUS les réglages sont ici.
Chemins (à partir de la racine du dépôt), graine, période étudiée et hypothèses métier.
"""
from pathlib import Path

import pandas as pd

# --- Chemins (indépendants de l'ordinateur et du dossier de lancement) ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_DONNEES = RACINE / "data"
FICHIER_BRUT = DOSSIER_DONNEES / "raw" / "Online Retail.xlsx"
FICHIER_SQLITE = DOSSIER_DONNEES / "database.sqlite"
DATA_PATH = DOSSIER_DONNEES / "base_clients_modelisation.csv"
DOSSIER_SQL = RACINE / "backend" / "sql"
MODEL_SAVE_PATH = RACINE / "backend" / "modele_logistique.pkl"

RANDOM_SEED = 42

# --- Période étudiée ---
DATE_COUPURE = pd.Timestamp("2011-11-09")  # date de référence : variables calculées jusqu'à cette date
FENETRE_JOURS = 30                         # cible : aucun achat dans les 30 jours qui suivent
JOURS_ACTIF = 90                           # client actif : au moins un achat dans les 90 jours avant

# --- Hypothèses métier (matrice des coûts) ---
COUT_PROMO = 10.0      # Coût d'envoi du code promo
VALEUR_RETENUE = 50.0  # Achat futur d'un client retenu
TAUX_SUCCES = 0.30     # HYPOTHÈSE : la promo retient 30 % des clients ciblés qui allaient partir

GAIN_VP = (TAUX_SUCCES * VALEUR_RETENUE) - COUT_PROMO
COUT_FP = -COUT_PROMO
GAIN_VN = 0.0
COUT_FN = 0.0

# Seuil de rentabilité : cibler un client est rentable si sa probabilité de churn dépasse ce seuil
# (10 / 15 = 0,667 avec les valeurs ci-dessus)
SEUIL_THEORIQUE = -COUT_FP / (GAIN_VP - COUT_FP)
