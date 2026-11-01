# Data Quality Card : Online Retail (UCI)

> D'après Gebru et al. (2021), *Datasheets for Datasets*. Chaque défaut a un chiffre et un traitement.
> Les chiffres viennent de la base SQLite construite par `python -m backend.data`.

## Identité

| Question | Réponse |
|---|---|
| Unité d'observation | **Fichier brut** : une ligne de facture (un produit dans une commande). **Table d'analyse** : un client actif. |
| Source, licence, lien | Online Retail, UCI Machine Learning Repository (Chen, 2015), CC BY 4.0 : https://archive.ics.uci.edu/dataset/352/online+retail |
| Période et population | Ventes d'un e-commerçant britannique de cadeaux, du 1er décembre 2010 au 9 décembre 2011. Clients surtout professionnels (grossistes), 38 pays, 89 % des lignes identifiées viennent du Royaume-Uni. |
| Taille | Brut : 541 909 lignes × 8 colonnes. Table d'analyse : 2 592 clients × 32 colonnes. |
| Cible | `churn` = 1 si le client actif n'achète rien du 10 novembre au 9 décembre 2011, 0 sinon. 57,5 % de 1. Construite en pandas à partir des ventes nettoyées en SQL. |
| Client actif | Au moins un achat dans les 90 jours avant le 9 novembre 2011 (date de référence). Sur 4 086 clients ayant acheté avant cette date, 2 592 sont actifs. |

## Défauts trouvés et ce qu'on en fait

| Défaut | Combien | Comment on l'a vu | Ce qu'on en fait, et pourquoi |
|---|---|---|---|
| Numéro client manquant | 135 080 lignes sur 541 909 (24,9 %) | `WHERE CustomerID IS NULL` en SQL | **Lignes retirées** (vue `ventes_nettoyees`) : impossible de rattacher l'achat à un client. Biais possible, voir plus bas. |
| Annulations (facture commençant par « C ») | 9 288 lignes (1,7 %), 3 836 factures | `WHERE InvoiceNo LIKE 'C%'` | **Retirées des ventes**, mais comptées par client dans `nb_annulations` (8 905 lignes rattachées à un client). |
| Quantité nulle ou négative hors annulation | 1 336 lignes (0,2 %) | `WHERE Quantity <= 0` | Retirées : corrections de stock, pas des ventes. |
| Prix nul ou négatif | 2 517 lignes (0,5 %), dont 40 avec un numéro client | `WHERE UnitPrice <= 0` | Retirées : cadeaux, ajustements comptables. |
| Frais et services (port, frais bancaires, commissions Amazon…) | 1 688 lignes après nettoyage (0,4 %) | Codes produit (`POST`, `M`, `BANK CHARGES`…) et descriptions, fonction `categoriser` | Retirées : ce ne sont pas des produits. |
| Doublons exacts | 5 192 lignes (1,3 % des lignes propres) | `GROUP BY` sur toutes les colonnes, `HAVING COUNT(*) > 1` | **Gardés** dans la version actuelle. Effet mesuré : en les retirant, l'AUC reste 0,75 et le nombre de codes 224, le gain espéré passe de +310 £ à +295 £. Décision de l'équipe : garder le code tel quel et le signaler comme limite. |
| Description manquante | 1 454 lignes (0,3 %), toutes sans numéro client | `IS NULL` | Disparaissent avec le filtre sur le numéro client. |
| Valeurs extrêmes | Quantité jusqu'à 80 995 sur une ligne, prix unitaire jusqu'à 8 142,75 £, dépense totale d'un client jusqu'à 247 886 £ (médiane : 935 £) | `MAX()`, `describe()` | **Gardées** : ce sont de vrais gros clients professionnels. La standardisation dans le pipeline limite leur poids. |
| Manquants dans la table d'analyse | `intervalle_moyen_jours` vide pour 681 clients sur 2 592 (26 %) : un seul jour d'achat, l'intervalle n'existe pas | `isna().sum()` | Remplacé par la médiane **et** une colonne indicatrice « intervalle non calculable », dans le pipeline (apprise sur l'entraînement uniquement). |
| Classes | 57,5 % de churn, 42,5 % de réachat | `mean()` | Déséquilibre faible : split stratifié, pas de rééquilibrage. |

Données nettoyées : 397 884 lignes après les filtres SQL, puis 396 196 lignes après le retrait des frais et services.

## Les pièges pour le modèle

| Question | Réponse |
|---|---|
| Risque de **fuite** | Toutes les variables sont calculées avec les achats **jusqu'au 9 novembre 2011** ; la cible regarde **après**. `mois_dernier_achat` et `jour_semaine_dernier_achat` sont exclues du modèle (effet calendrier lié à la date de coupure). `CustomerID` et `churn` sont exclus. Un test vérifie que ces colonnes ne sont pas utilisées. |
| Variables sensibles | Aucune donnée sur l'âge, le sexe ou l'origine. Le **pays** est utilisé : il peut défavoriser des clients étrangers, voir l'équité dans la Model Card. |
| Biais de sélection | 25 % des lignes n'ont pas de numéro client (achats non identifiés, peut-être des particuliers) : le modèle ne vaut que pour les clients identifiés. Seuls les clients actifs (achat dans les 90 jours) sont étudiés. |
| Données personnelles | Le numéro client est un identifiant pseudonyme, sans nom ni adresse. Jeu de données public sous licence CC BY 4.0. |

## Ce qu'on attend des données

- **Les variables les plus utiles** : la régularité d'achat (nombre de jours d'achat, intervalle entre deux achats) et l'activité récente (factures sur 30 et 90 jours), parce qu'un client fidèle a des habitudes.
- **Ce que les données ne permettent pas de dire** : pourquoi un client part (pas d'enquête de satisfaction), si un code promo le fera rester (aucune campagne passée dans les données), ni comment le modèle se comporte en dehors de la période avant Noël 2011.
