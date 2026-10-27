"""
Définition du modèle d'apprentissage supervisé (Régression Logistique)
et de la logique d'évaluation métier.
"""
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from backend.config import RANDOM_SEED, GAIN_VP, COUT_FP, GAIN_VN, COUT_FN

def creer_pipeline(colonnes_numeriques, colonnes_categorielles):
    """Crée le pipeline de transformation et le modèle."""
    
    # Imputation et mise à l'échelle pour les variables numériques
    num_pipe = Pipeline([
        ('imputation', SimpleImputer(strategy='median', add_indicator=True)),
        ('echelle', StandardScaler())
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipe, colonnes_numeriques),
            ('cat', OneHotEncoder(handle_unknown='ignore'), colonnes_categorielles)
        ])
    
    # Régression logistique pure (sans déformation des probabilités)
    modele = LogisticRegression(random_state=RANDOM_SEED, max_iter=1000)
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', modele)
    ])
    
    return pipeline

def calculer_gain_metier(y_vrai, y_predit):
    """
    Calcule le gain espéré de la campagne basé sur la matrice des coûts.
    """
    gain_total = 0
    for vrai, predit in zip(y_vrai, y_predit):
        if predit == 1 and vrai == 1:
            gain_total += GAIN_VP
        elif predit == 1 and vrai == 0:
            gain_total += COUT_FP
        elif predit == 0 and vrai == 0:
            gain_total += GAIN_VN
        elif predit == 0 and vrai == 1:
            gain_total += COUT_FN
            
    nb_cibles = sum(y_predit)
    gain_moyen_par_cible = gain_total / nb_cibles if nb_cibles > 0 else 0
    
    return gain_total, gain_moyen_par_cible

def optimiser_seuil(y_vrai, probabilites):
    """
    Trouve le seuil de probabilité qui maximise le gain espéré avec un pas fin.
    """
    meilleur_seuil = 0.5
    meilleur_gain = -float('inf')
    
    # Recherche fine par pas de 1%
    for seuil_test in [x / 100.0 for x in range(5, 96)]:
        y_pred_test = (probabilites >= seuil_test).astype(int)
        gain, _ = calculer_gain_metier(y_vrai, y_pred_test)
        
        if gain > meilleur_gain:
            meilleur_gain = gain
            meilleur_seuil = seuil_test
            
    return meilleur_seuil