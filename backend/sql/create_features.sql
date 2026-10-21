-- Création d'une table nettoyée à partir des données brutes

CREATE VIEW IF NOT EXISTS ventes_nettoyees AS
SELECT 
    InvoiceNo,
    StockCode,
    Description,
    Quantity,
    InvoiceDate,
    UnitPrice,
    CAST(CustomerID AS INTEGER) AS CustomerID,
    Country,
    (Quantity * UnitPrice) AS montant,
    DATE(InvoiceDate) AS date_jour
FROM online_retail_raw
WHERE 
    CustomerID IS NOT NULL 
    AND Quantity > 0 
    AND UnitPrice > 0
    AND InvoiceNo NOT LIKE 'C%'; -- Exclut les factures d'annulation