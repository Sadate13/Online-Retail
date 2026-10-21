-- Création de la table brute pour accueillir les données de Online Retail.xlsx
-- Cette table correspond exactement aux colonnes du fichier source.

CREATE TABLE IF NOT EXISTS online_retail_raw (
    InvoiceNo TEXT,
    StockCode TEXT,
    Description TEXT,
    Quantity INTEGER,
    InvoiceDate TEXT,  -- Stocké comme texte au format ISO 8601 (YYYY-MM-DD HH:MM:SS)
    UnitPrice REAL,
    CustomerID REAL,   -- Parfois vide ou flottant dans l'Excel
    Country TEXT
);