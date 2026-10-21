import sqlite3
import pandas as pd
import numpy as np
import re
import unicodedata
import sys
import os

# --- Variables globales ---
FENETRE_JOURS = 30
DATE_COUPURE = pd.Timestamp("2011-11-09")
JOURS_ACTIF = 90

CODES_SERVICES = {"POST", "DOT", "M", "m", "D", "C2", "S", "B", "BANK CHARGES", "AMAZONFEE", "CRUK", "PADS", "ADJUST", "ADJUST2"}

REGLES = [
    ("Noël et saisonnier", ["CHRISTMAS", "XMAS", "SANTA", "REINDEER", "SNOW", "ADVENT", "EASTER", "HALLOWEEN", "ANGEL", "STOCKING", "BAUBLE", "TINSEL", "NATIVITY", "ROBIN", "FATHER CHRISTMAS", "ICICLE", "SLEIGH", "HOLLY"]),
    ("Bijoux et accessoires", ["NECKLACE", "BRACELET", "EARRING", "RING", "CHARM", "BEAD", "BROOCH", "HAIR", "PENDANT", "SCARF", "BANGLE", "NECKLET", "UMBRELLA", "PURSE", "WALLET", "HANDBAG", "LARIAT", "HAIRBAND", "BANDANA", "FAN", "RAIN MAC", "SHOE", "SOCK", "BAG CHARM", "SUNGLASSES", "GLOVES", "HAT", "SLIPPER", "BADGE", "KEYRING", "KEY RING"]),
    ("Bougies, lumières et parfums", ["CANDLE", "T-LIGHT", "TEA LIGHT", "TEALIGHT", "LIGHT", "LANTERN", "LAMP", "INCENSE", "OIL BURNER", "FRAGRANCE", "SCENT", "POTPOURRI", "LAMPSHADE", "CANDELABRA"]),
    ("Jouets, jeux et enfants", ["TOY", "GAME", "DOLL", "CHILDREN", "CHILD", "PUZZLE", "SPACEBOY", "DOLLY", "PLAYHOUSE", "PLAY", "TEDDY", "SKITTLES", "DOMINO", "BABY", "SOLDIER", "ROBOT", "MONEY BOX", "PUPPET", "STICKER", "CRAYON", "CLAY", "WRITING SET", "DRAWING", "SLATE", "KIDS", "BOYS", "GIRLS", "GIRLY", "DINOSAUR", "TOOL SET", "HELICOPTER", "PATCHES", "MODELLING", "JIGSAW", "BUBBLES", "KIT"]),
    ("Fête et anniversaire", ["PARTY", "BIRTHDAY", "BALLOON", "BUNTING", "CAKE CASE", "CAKE STAND", "PICNIC", "NAPKIN", "CONFETTI", "STRAW", "GARLAND", "WEDDING"]),
    ("Papeterie, cartes et emballage", ["CARD", "WRAP", "PAPER", "NOTEBOOK", "PENCIL", "PEN ", "RIBBON", "TAG", "ENVELOPE", "STATIONERY", "BOOK", "ERASER", "RUBBER", "RULER", "STAMP", "CALENDAR", "DIARY", "PARASOL", "BOX OF", "GIFT BAG", "TISSUE"]),
    ("Cuisine et art de la table", ["MUG", "CUP", "TEA", "BOWL", "PLATE", "CAKE", "CUTLERY", "JAR", "BOTTLE", "KITCHEN", "PANTRY", "SPOON", "APRON", "TEAPOT", "LUNCH", "BAKING", "JAM", "COASTER", "COFFEE", "BISCUIT", "JUG", "TRAY", "SALT", "PEPPER", "OVEN", "GLOVE", "TOWEL", "FORK", "KNIFE", "TUMBLER", "GLASS", "SPATULA", "COOKIE", "CAKESTAND", "PLATTER", "CHOPPING", "FRYING", "PAN", "LOLLY", "MOULD", "SWEETIE", "BASIN", "EGG WARMER", "TEAPOT", "SIEVE", "WHISK", "KETTLE", "TOAST", "BREAD", "CHOCOLATE", "MILK", "SUGAR", "EGG CUP", "PLACEMAT", "TEASPOON", "CASSEROLE", "DISH", "CAKE TIN"]),
    ("Sacs et rangement", ["BAG", "BOX", "BASKET", "STORAGE", "TIN", "DRAWER", "TRUNK", "CASE", "CABINET", "CHEST", "HOLDER", "ORGANISER", "RACK", "SHELF", "SHELVES", "CRATE", "HAMPER", "POUCH", "SUITCASE", "LUGGAGE", "BIN"]),
    ("Jardin et extérieur", ["GARDEN", "BIRD", "PLANT", "POT", "WATERING", "SEED", "OUTDOOR", "FLOWER POT", "TROWEL", "GNOME", "PARASOL", "WREATH", "FEATHER TREE", "BICYCLE", "BELL", "HAND WARMER", "WINDMILL", "BIRDHOUSE", "HERB", "MARKER", "BUCKET", "SPADE", "WINDSOCK"]),
    ("Décoration maison", ["FRAME", "MIRROR", "CLOCK", "CUSHION", "SIGN", "WALL", "DOORMAT", "HOOK", "VASE", "CURTAIN", "DECORATION", "ORNAMENT", "HANGING", "HEART", "FLOWER", "ROSE", "STAR", "BUTTERFLY", "METAL", "WOODEN", "WOOD", "CERAMIC", "SHELL", "PLAQUE", "DOOR", "HOME", "LOVE", "DESIGN", "SET OF", "FELT", "FLOCK", "PHOTO", "COVER", "BLANKET", "THROW", "RUG", "MAT", "TILE", "KNOB", "HANDLE", "HOOKS", "DRAWER KNOB", "FOB", "KEY", "STAND", "TIDY", "ASHTRAY", "CHALKBOARD", "PHOTOFRAME", "DISCO", "FRENCH", "SANDALWOOD", "SILK", "SCISSOR", "MAGNET", "NIGHT", "LED", "BELL", "WARMER"]),
]

def categoriser(code, description):
    """Renvoie la catégorie d'un produit à partir de son StockCode et de sa description."""
    code = str(code).strip()
    if code in CODES_SERVICES or code.upper().startswith("GIFT") or code.upper().startswith("DCGS"):
        if code.upper().startswith("GIFT"):
            return "Bons cadeaux"
        if code.upper().startswith("DCGS"):
            return "Autre"
        return "Frais et services"
    desc = str(description).upper()
    if "UNSALEABLE" in desc or "CARRIAGE" in desc or "DAMAGED" in desc:
        return "Frais et services"
    if "VOUCHER" in desc:
        return "Bons cadeaux"
    texte = " " + re.sub(r"[^A-Z0-9 \-]", " ", str(description).upper()) + " "
    for categorie, mots in REGLES:
        for mot in mots:
            if re.search(r"(?<![A-Z])" + re.escape(mot.strip()) + r"S?(?![A-Z])", texte):
                return categorie
    return "Autre"

def nom_colonne(c):
    c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
    return "part_" + c.lower().replace(" ", "_").replace(",", "").replace("'", "")

def build_data(chemin_entree="data/raw/Online Retail.xlsx", dossier_sortie="data/"):
    """Orchestre la création de la table d'analyse via SQLite et Pandas."""
    
    print("1. Lecture du fichier Excel...")
    try:
        brut = pd.read_excel(chemin_entree, sheet_name="Online Retail")
    except FileNotFoundError:
        print(f"ERREUR: Le fichier {chemin_entree} est introuvable. Placez-le dans data/raw/")
        return

    brut["InvoiceNo"] = brut["InvoiceNo"].astype(str)
    brut["StockCode"] = brut["StockCode"].astype(str)
    
    # --- TRANSITION OBLIGATOIRE PAR SQLITE ---
    print("2. Chargement dans SQLite...")
    db_path = os.path.join(dossier_sortie, "database.sqlite")
    conn = sqlite3.connect(db_path)
    
    # On exécute d'abord la création de la table brute
    with open("backend/sql/load_data.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
        
    # Envoi des données brutes vers SQLite
    brut.to_sql("online_retail_raw", conn, if_exists="replace", index=False)
    
    # Exécution de la création de la vue propre
    with open("backend/sql/create_features.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    
    print("3. Récupération des données nettoyées depuis SQLite...")
    ventes = pd.read_sql_query("SELECT * FROM ventes_nettoyees", conn)
    annulations = pd.read_sql_query("SELECT * FROM online_retail_raw WHERE InvoiceNo LIKE 'C%' AND CustomerID IS NOT NULL", conn)
    conn.close()
    
    # --- SUITE DU TRAITEMENT EN PANDAS ---
    print("4. Application de la logique métier (Catégories, Churn)...")
    ventes["InvoiceDate"] = pd.to_datetime(ventes["InvoiceDate"])
    ventes["date_jour"] = pd.to_datetime(ventes["date_jour"])
    annulations["InvoiceDate"] = pd.to_datetime(annulations["InvoiceDate"])
    annulations["date_jour"] = annulations["InvoiceDate"].dt.normalize()
    annulations["CustomerID"] = annulations["CustomerID"].astype(int)

    # Catégories
    desc_par_code = (ventes.dropna(subset=["Description"]).groupby("StockCode")["Description"].agg(lambda s: s.astype(str).value_counts().index[0]))
    table_produits = desc_par_code.rename("description").reset_index()
    table_produits["categorie"] = [categoriser(c, d) for c, d in zip(table_produits["StockCode"], table_produits["description"])]
    cat_par_code = dict(zip(table_produits["StockCode"], table_produits["categorie"]))
    ventes["categorie"] = ventes["StockCode"].map(cat_par_code).fillna("Frais et services")
    ventes = ventes[ventes["categorie"] != "Frais et services"]

    # Passé et futur
    derniere_date = ventes["InvoiceDate"].max().normalize()
    passe = ventes[ventes["date_jour"] <= DATE_COUPURE]
    futur = ventes[(ventes["date_jour"] > DATE_COUPURE) & (ventes["date_jour"] <= DATE_COUPURE + pd.Timedelta(days=FENETRE_JOURS))]

    # Agrégation par client
    fact = passe.groupby("InvoiceNo").agg(CustomerID=("CustomerID", "first"), date_jour=("date_jour", "first"), nb_articles=("Quantity", "sum"), montant=("montant", "sum")).reset_index()
    g = fact.groupby("CustomerID")
    clients = g.agg(nb_factures=("InvoiceNo", "nunique"), nb_jours_achat=("date_jour", "nunique"), nb_articles_total=("nb_articles", "sum"), depense_totale=("montant", "sum"), premier_achat=("date_jour", "min"), dernier_achat=("date_jour", "max"))
    
    # RFM et variables
    clients["recence_jours"] = (DATE_COUPURE - clients["dernier_achat"]).dt.days
    clients["anciennete_jours"] = (DATE_COUPURE - clients["premier_achat"]).dt.days
    clients["frequence_achat_mensuelle"] = clients["nb_factures"] / np.maximum(clients["anciennete_jours"] / 30.0, 1)
    clients["panier_moyen"] = clients["depense_totale"] / clients["nb_factures"]
    ecart = (clients["dernier_achat"] - clients["premier_achat"]).dt.days
    clients["intervalle_moyen_jours"] = np.where(clients["nb_jours_achat"] > 1, ecart / (clients["nb_jours_achat"] - 1), np.nan)

    # Activité récente
    for jours in (30, 90):
        recent = fact[fact["date_jour"] > DATE_COUPURE - pd.Timedelta(days=jours)].groupby("CustomerID")
        clients[f"nb_factures_{jours}j"] = recent["InvoiceNo"].nunique()
        clients[f"depense_{jours}j"] = recent["montant"].sum()
    for c in ["nb_factures_30j", "depense_30j", "nb_factures_90j", "depense_90j"]:
        clients[c] = clients[c].fillna(0)

    clients["mois_dernier_achat"] = clients["dernier_achat"].dt.month
    clients["jour_semaine_dernier_achat"] = clients["dernier_achat"].dt.dayofweek + 1
    clients["nb_produits_distincts"] = passe.groupby("CustomerID")["StockCode"].nunique()

    # Parts de catégories
    parts = passe.pivot_table(index="CustomerID", columns="categorie", values="montant", aggfunc="sum", fill_value=0)
    clients["categorie_principale"] = parts.idxmax(axis=1)
    parts = parts.div(parts.sum(axis=1), axis=0)
    parts.columns = [nom_colonne(c) for c in parts.columns]
    clients = clients.join(parts)

    clients["pays"] = passe.sort_values("InvoiceDate").groupby("CustomerID")["Country"].last()
    clients["nb_annulations"] = (annulations[annulations["date_jour"] <= DATE_COUPURE].groupby("CustomerID").size())
    clients["nb_annulations"] = clients["nb_annulations"].fillna(0).astype(int)

    # Churn et finalisation
    clients = clients.reset_index()
    clients = clients[clients["recence_jours"] <= JOURS_ACTIF].copy()
    clients["churn"] = (~clients["CustomerID"].isin(futur["CustomerID"].unique())).astype(int)
    clients = clients.drop(columns=["premier_achat", "dernier_achat"])

    print("5. Sauvegarde de la base clients...")
    clients.to_csv(f"{dossier_sortie}/base_clients_modelisation.csv", index=False, encoding="utf-8")
    print(f"Terminé ! Table finale générée : {clients.shape} dans {dossier_sortie}")

if __name__ == "__main__":
    build_data()