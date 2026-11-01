"""Tests sur les données : table d'analyse, nettoyage SQL, catégories."""
import sqlite3

import joblib
import pandas as pd
import pytest

from backend.config import DATA_PATH, MODEL_SAVE_PATH
from backend.data import JOURS_ACTIF, categoriser


@pytest.fixture(scope="module")
def table():
    return pd.read_csv(DATA_PATH)


def test_une_ligne_par_client(table):
    # Attrape une jointure qui duplique des clients.
    assert len(table) == 2592
    assert table["CustomerID"].is_unique


def test_cible_binaire_et_taux_de_churn_attendu(table):
    assert set(table["churn"]) == {0, 1}
    assert table["churn"].mean() == pytest.approx(0.575, abs=0.01)


def test_seulement_des_clients_actifs(table):
    # Client actif = au moins un achat dans les 90 jours avant la date de référence.
    assert table["recence_jours"].between(0, JOURS_ACTIF).all()


def test_aucune_variable_interdite_dans_le_modele(modele_entraine):
    # La cible, l'identifiant et les variables de date exclues ne doivent pas servir au modèle.
    colonnes = joblib.load(MODEL_SAVE_PATH)["colonnes_entrainement"]
    interdites = {"churn", "CustomerID", "mois_dernier_achat", "jour_semaine_dernier_achat"}
    assert interdites.isdisjoint(colonnes)


def test_sql_retire_annulations_et_lignes_invalides():
    conn = sqlite3.connect(":memory:")
    with open("backend/sql/load_data.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    lignes = [
        ("536365", "A", "MUG", 2, "2011-01-10 10:00:00", 3.0, 17850.0, "United Kingdom"),  # gardée
        ("C536379", "A", "MUG", -1, "2011-01-10 10:00:00", 3.0, 17850.0, "United Kingdom"),  # annulation
        ("536366", "A", "MUG", 2, "2011-01-10 10:00:00", 3.0, None, "United Kingdom"),  # sans client
        ("536367", "A", "MUG", 0, "2011-01-10 10:00:00", 3.0, 17850.0, "United Kingdom"),  # quantité nulle
        ("536368", "A", "MUG", 2, "2011-01-10 10:00:00", 0.0, 17850.0, "United Kingdom"),  # prix nul
    ]
    conn.executemany("INSERT INTO online_retail_raw VALUES (?, ?, ?, ?, ?, ?, ?, ?)", lignes)
    with open("backend/sql/create_features.sql", encoding="utf-8") as f:
        conn.executescript(f.read())

    ventes = pd.read_sql_query("SELECT * FROM ventes_nettoyees", conn)
    conn.close()

    assert ventes["InvoiceNo"].tolist() == ["536365"]
    assert ventes["montant"].iloc[0] == pytest.approx(6.0)
    assert ventes["date_jour"].iloc[0] == "2011-01-10"


@pytest.mark.parametrize("code, description, attendu", [
    ("POST", "POSTAGE", "Frais et services"),
    ("GIFT_0001_20", "Dotcomgiftshop Gift Voucher £20.00", "Bons cadeaux"),
    ("22086", "PAPER CHAIN KIT 50'S CHRISTMAS", "Noël et saisonnier"),
    ("21212", "PACK OF 72 RETROSPOT CAKE CASES", "Fête et anniversaire"),
    ("37370", "RETRO COFFEE MUGS ASSORTED", "Cuisine et art de la table"),
])
def test_categoriser(code, description, attendu):
    assert categoriser(code, description) == attendu
