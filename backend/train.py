"""
Script d'entraînement du modèle.
Lancement : python -m backend.train
"""
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from backend.config import DATA_PATH, MODEL_SAVE_PATH, RANDOM_SEED, SEUIL_THEORIQUE
from backend.model import creer_pipeline, calculer_gain_metier, optimiser_seuil

def entrainer():
    print(f"1. Chargement des données depuis {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    y = df['churn']
    colonnes_a_exclure = ['CustomerID', 'churn', 'mois_dernier_achat', 'jour_semaine_dernier_achat']
    X = df.drop(columns=colonnes_a_exclure)
    
    colonnes_categorielles = ['pays', 'categorie_principale']
    colonnes_numeriques = [col for col in X.columns if col not in colonnes_categorielles]

    print("2. Séparation des données (Train/Test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    print("3. Entraînement de la Régression Logistique (Pipeline complet)...")
    pipeline = creer_pipeline(colonnes_numeriques, colonnes_categorielles)
    pipeline.fit(X_train, y_train)

    # Le seuil de décision vient du calcul de rentabilité (coût du code, gain d'un client retenu).
    # C'est le même que celui utilisé par l'application avec les hypothèses par défaut.
    seuil = SEUIL_THEORIQUE
    print(f"\nSeuil de rentabilité (calculé avec les coûts) : {seuil:.3f}")

    # Pour comparaison : seuil trouvé par essais sur le jeu d'entraînement
    probabilites_train = pipeline.predict_proba(X_train)[:, 1]
    seuil_empirique = optimiser_seuil(y_train, probabilites_train)
    print(f"Seuil trouvé par essais sur l'entraînement (comparaison) : {seuil_empirique:.2f}")
    
    print("\n--- ÉVALUATION (Sur le jeu de test) ---")
    probabilites_test = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (probabilites_test >= seuil).astype(int)
    
    baseline_pred = np.ones(len(y_test))
    gain_baseline, moyen_baseline = calculer_gain_metier(y_test, baseline_pred)
    gain_modele, moyen_modele = calculer_gain_metier(y_test, y_pred)
    
    print(f"Baseline (Envoi massif) : Gain espéré = {gain_baseline:.2f} | Gain moyen par cible = {moyen_baseline:.2f}")
    print(f"Modèle (Seuil {seuil:.3f})  : Gain espéré = {gain_modele:.2f} | Gain moyen par cible = {moyen_modele:.2f}")

    # Indicateurs enregistrés avec le modèle : l'écran "Le modèle" de l'application les affiche
    metriques = {
        'auc_test': float(roc_auc_score(y_test, probabilites_test)),
        'auc_reference_recence': float(roc_auc_score(y_test, X_test['recence_jours'])),
        'gain_baseline': float(gain_baseline),
        'gain_modele': float(gain_modele),
        'nb_test': int(len(y_test)),
        'taux_churn_test': float(y_test.mean()),
        'seuil_optimal': float(seuil),                 # nom conservé car l'application l'utilise
        'seuil_empirique_train': float(seuil_empirique),
        'nb_clients_cibles': int(y_pred.sum()),
        'part_vrais_partants_cibles': float(y_test[y_pred == 1].mean()),
    }

    objet_a_sauvegarder = {
        'pipeline': pipeline,
        'seuil_optimal': seuil,
        'colonnes_entrainement': X.columns.tolist(),
        'metriques': metriques
    }
    joblib.dump(objet_a_sauvegarder, MODEL_SAVE_PATH)
    print("\nModèle sauvegardé. Terminé !")

if __name__ == "__main__":
    entrainer()