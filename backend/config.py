"""
Fichier de configuration du projet.
Contient les chemins, la seed et les paramètres métier (coûts).
"""

RANDOM_SEED = 42
DATA_PATH = "data/base_clients_modelisation.csv"
MODEL_SAVE_PATH = "backend/modele_logistique.pkl"

# --- Hypothèses Métier (Matrice des Coûts) ---
COUT_PROMO = 10.0      # Coût d'envoi du code promo
VALEUR_RETENUE = 50.0  # Valeur d'un client sauvé
TAUX_SUCCES = 0.30     # HYPOTHÈSE : La promo parvient à retenir 30% des clients ciblés

GAIN_VP = (TAUX_SUCCES * VALEUR_RETENUE) - COUT_PROMO
COUT_FP = -COUT_PROMO
GAIN_VN = 0.0
COUT_FN = 0.0

# Seuil de rentabilité : cibler un client est rentable si sa probabilité de churn dépasse ce seuil
# (10 / 15 = 0,667 avec les valeurs ci-dessus)
SEUIL_THEORIQUE = -COUT_FP / (GAIN_VP - COUT_FP)