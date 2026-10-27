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

# Vrai Positif (VP) : On cible un client sur le départ. 
# On paie la promo (-10€), et on a 30% de chance de gagner 50€.
# Espérance de gain = (0.30 * 50) - 10 = 15 - 10 = +5€
GAIN_VP = (TAUX_SUCCES * VALEUR_RETENUE) - COUT_PROMO

# Faux Positif (FP) : Client fidèle ciblé à tort. On perd la promo.
COUT_FP = -COUT_PROMO  # -10€

# Vrai Négatif / Faux Négatif
GAIN_VN = 0.0
COUT_FN = 0.0