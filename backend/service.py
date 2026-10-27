"""
Service métier (API interne).
Seule interface autorisée à être appelée par le frontend (app.py).
"""
import pandas as pd
import joblib
import os
from backend.config import DATA_PATH, MODEL_SAVE_PATH

# Variable globale pour stocker le modèle en mémoire sans le recharger à chaque clic
_modele_data = None

def _charger_modele():
    """Charge le modèle en mémoire s'il n'y est pas déjà."""
    global _modele_data
    if _modele_data is None:
        if not os.path.exists(MODEL_SAVE_PATH):
            raise FileNotFoundError(f"Le modèle {MODEL_SAVE_PATH} est introuvable. Lancez 'python -m backend.train'.")
        _modele_data = joblib.load(MODEL_SAVE_PATH)
    return _modele_data

def get_client_info(customer_id):
    """Récupère les informations brutes d'un client depuis la base."""
    try:
        df = pd.read_csv(DATA_PATH)
        client = df[df['CustomerID'] == int(customer_id)]
        if client.empty:
            return None
        return client
    except Exception as e:
        print(f"Erreur de lecture des données: {e}")
        return None

def predict_client(customer_id):
    """
    Fait une prédiction de churn pour un client donné.
    Retourne un dictionnaire avec la probabilité, le seuil et l'action recommandée.
    """
    try:
        modele_data = _charger_modele()
        pipeline = modele_data['pipeline']
        seuil_optimal = modele_data['seuil_optimal']
        colonnes_entrainement = modele_data['colonnes_entrainement']
    except Exception as e:
        return {"erreur": f"Erreur lors du chargement du modèle : {str(e)}"}

    # 1. Récupérer les données du client
    client_data = get_client_info(customer_id)
    if client_data is None:
        return {"erreur": f"Le client ID {customer_id} est introuvable dans la base active."}

    # 2. Préparer les données
    # On gère les valeurs nulles comme lors de l'entraînement
    client_data['intervalle_moyen_jours'] = client_data['intervalle_moyen_jours'].fillna(0)
    X_client = client_data[colonnes_entrainement]

    # 3. Faire la prédiction
    proba_churn = pipeline.predict_proba(X_client)[0][1] # Probabilité de la classe 1 (Churn)
    
    # 4. Appliquer la règle de décision basée sur le seuil métier
    prediction = 1 if proba_churn >= seuil_optimal else 0

    return {
        "erreur": None,
        "customer_id": customer_id,
        "proba_churn": proba_churn,
        "seuil_optimal": seuil_optimal,
        "prediction": prediction,
        "action": "ENVOYER CODE PROMO" if prediction == 1 else "NE RIEN ENVOYER"
    }

def get_all_clients():
    """Récupère l'ensemble de la base clients pour l'exploration globale."""
    try:
        df = pd.read_csv(DATA_PATH)
        return df
    except Exception as e:
        print(f"Erreur de lecture : {e}")
        return None


# =====================================================================
from functools import lru_cache

import numpy as np
import pandas as pd

from backend import config

COLONNES_PROFIL = ["recence_jours", "nb_factures", "depense_totale", "panier_moyen",
                   "anciennete_jours", "nb_factures_90j", "categorie_principale", "pays"]


# ---------------------------------------------------------------- Règle de décision
def get_hypotheses():
    """Valeurs de départ des hypothèses métier (définies dans config.py)."""
    return {"cout_promo": config.COUT_PROMO,
            "valeur_retenue": config.VALEUR_RETENUE,
            "taux_succes": config.TAUX_SUCCES}


def calculer_seuil(taux_succes, cout_promo, valeur_retenue):
    """Le code est rentable pour un client si sa probabilité de churn p dépasse coût / (taux x valeur)."""
    seuil = cout_promo / (taux_succes * valeur_retenue)
    return {"seuil": seuil,
            "rentable": seuil < 1,
            "gain_vrai_partant": taux_succes * valeur_retenue - cout_promo}


def gain_espere_envoi(proba, taux_succes, cout_promo, valeur_retenue):
    """Gain espéré en envoyant le code à un client dont la probabilité de churn est `proba`."""
    return proba * taux_succes * valeur_retenue - cout_promo


# ---------------------------------------------------------------- Scores des clients
def _preparer_X(df, colonnes):
    X = df[colonnes].copy()
    return X


def _noms_variables(pipeline):
    """Noms des variables après transformation, sans les préfixes 'num__' et 'cat__'."""
    return [n.split("__", 1)[-1] for n in pipeline.named_steps["preprocessor"].get_feature_names_out()]


@lru_cache(maxsize=1)
def _table_scores():
    """Tous les clients avec leur probabilité de churn (calculée une seule fois)."""
    df = get_all_clients()
    if df is None:
        return None
    objet = _charger_modele()
    table = df.copy()
    X = _preparer_X(table, objet["colonnes_entrainement"])
    table["proba_churn"] = objet["pipeline"].predict_proba(X)[:, 1]
    return table


def get_liste_ids():
    table = _table_scores()
    return [] if table is None else sorted(table["CustomerID"].astype(int).tolist())


def _facteurs(ligne, n=5):
    """Contribution de chaque variable au score d'un client, par rapport à un client moyen."""
    objet = _charger_modele()
    pipeline = objet["pipeline"]
    X = _preparer_X(ligne, objet["colonnes_entrainement"])
    Z = pipeline.named_steps["preprocessor"].transform(X)
    Z = Z.toarray() if hasattr(Z, "toarray") else np.asarray(Z)
    contributions = pd.Series(Z[0] * pipeline.named_steps["classifier"].coef_[0],
                              index=_noms_variables(pipeline))
    contributions = contributions[contributions != 0]
    return {"hausse": contributions[contributions > 0].sort_values(ascending=False).head(n),
            "baisse": contributions[contributions < 0].sort_values().head(n)}


def analyser_client(customer_id, taux_succes, cout_promo, valeur_retenue):
    """Tout ce qu'il faut pour l'écran Décision : probabilité, action, gain espéré, profil, facteurs."""
    try:
        cid = int(customer_id)
    except (TypeError, ValueError):
        return {"erreur": "Le numéro de client doit être un nombre entier."}
    table = _table_scores()
    if table is None:
        return {"erreur": "Les données clients sont introuvables."}
    ligne = table[table["CustomerID"] == cid]
    if ligne.empty:
        return {"erreur": f"Le client {cid} n'est pas dans la liste des clients actifs."}

    proba = float(ligne["proba_churn"].iloc[0])
    regle = calculer_seuil(taux_succes, cout_promo, valeur_retenue)
    gain = gain_espere_envoi(proba, taux_succes, cout_promo, valeur_retenue)
    return {"proba_churn": proba,
            "seuil": regle["seuil"],
            "rentable": regle["rentable"],
            "gain_espere": gain,
            "envoyer": gain > 0,
            "profil": {c: ligne[c].iloc[0] for c in COLONNES_PROFIL},
            "facteurs": _facteurs(ligne),
            "churn_reel": int(ligne["churn"].iloc[0])}


def liste_cibles(taux_succes, cout_promo, valeur_retenue, budget_max=None):
    """Clients à contacter (gain espéré positif), du plus risqué au moins risqué, limités au budget."""
    table = _table_scores().copy()
    table["gain_espere"] = gain_espere_envoi(table["proba_churn"], taux_succes, cout_promo, valeur_retenue)
    cibles = table[table["gain_espere"] > 0].sort_values("proba_churn", ascending=False)
    if budget_max is not None:
        cibles = cibles.head(int(budget_max))
    colonnes = ["CustomerID", "proba_churn", "gain_espere", "recence_jours", "nb_factures",
                "depense_totale", "categorie_principale", "pays"]
    bilan = {"nb_clients": len(cibles),
             "cout_total": len(cibles) * cout_promo,
             "gain_total": float(cibles["gain_espere"].sum())}
    return cibles[colonnes].reset_index(drop=True), bilan


# ---------------------------------------------------------------- Exploration et modèle
def _part_churn(df, groupes, min_clients=1):
    t = (df.groupby(groupes, observed=True)["churn"].agg(part_churn="mean", nb_clients="size")
           .reset_index().rename(columns={groupes.name: "groupe"}))
    t["groupe"] = t["groupe"].astype(str)
    return t[t["nb_clients"] >= min_clients].reset_index(drop=True)


def get_exploration():
    df = get_all_clients()
    if df is None:
        return None
    recence = pd.cut(df["recence_jours"], [-1, 14, 30, 60, 90],
                     labels=["0 à 14 jours", "15 à 30 jours", "31 à 60 jours", "61 à 90 jours"])
    factures = pd.cut(df["nb_factures"], [0, 1, 2, 4, 9, 100000],
                      labels=["1", "2", "3 à 4", "5 à 9", "10 ou plus"])
    par_categorie = _part_churn(df, df["categorie_principale"], min_clients=20)
    par_categorie = par_categorie.sort_values("part_churn", ascending=False).reset_index(drop=True)
    return {"resume": {"nb_clients": len(df), "taux_churn": float(df["churn"].mean()),
                       "panier_moyen": float(df["panier_moyen"].mean()),
                       "depense_moyenne": float(df["depense_totale"].mean())},
            "par_recence": _part_churn(df, recence),
            "par_factures": _part_churn(df, factures),
            "par_categorie": par_categorie,
            "donnees": df}


def get_metriques():
    """Indicateurs de performance enregistrés à l'entraînement (None s'ils sont absents)."""
    return _charger_modele().get("metriques")


def get_coefficients():
    """Poids de chaque variable dans la régression logistique, du plus fort au plus faible."""
    pipeline = _charger_modele()["pipeline"]
    t = pd.DataFrame({"variable": _noms_variables(pipeline),
                      "poids": pipeline.named_steps["classifier"].coef_[0]})
    return t.sort_values("poids", key=abs, ascending=False).reset_index(drop=True)