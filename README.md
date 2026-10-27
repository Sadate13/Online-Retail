# Fidélisation client : prédire le réachat (Online Retail)

## 1. Question business

Quels clients actifs ont le moins de probabilité de racheter dans les 30 jours ?
Le but est de leur envoyer en priorité un code de réduction par e-mail, avec un budget limité.

## 2. Données et cible

- **Source :** jeu de données Online Retail (UCI), ventes d'un e-commerçant britannique du 1er décembre 2010 au 9 décembre 2011. Les montants sont en livres sterling (£).
- **Date de référence :** 9 novembre 2011. Toutes les variables sont calculées avec les achats faits jusqu'à cette date.
- **Client actif :** client ayant acheté au moins une fois dans les 90 jours avant le 9 novembre 2011.
- **Cible (`churn`) :** 1 si le client n'achète rien entre le 10 novembre et le 9 décembre 2011, 0 sinon.
- **Base finale :** une ligne par client, 2 592 clients actifs, dont 57,5 % avec `churn = 1`.

Nettoyage : sur 541 909 lignes, 391 009 sont conservées. Sont retirées les lignes sans numéro de client, les annulations, les doublons, les prix ou quantités invalides, et les frais qui ne sont pas des produits.

La description de chaque variable est dans `docs/dictionnaire_variables.pdf`.

## 3. Modèle et décision

**Modèle :** régression logistique. Elle donne pour chaque client la probabilité de ne pas racheter. Elle est simple et ses poids se lisent. Une forêt aléatoire et un gradient boosting donnent des résultats proches (AUC autour de 0,74), le modèle le plus simple est donc gardé.

**Découpage :** 80 % des clients pour l'entraînement, 20 % pour le test, avec la même part de churn dans chaque jeu. La graine est fixée (42). Le seuil de décision est choisi sur l'entraînement, le test sert uniquement à mesurer.

**Règle de décision.** Les valeurs ci-dessous sont des hypothèses (fichier `backend/config.py`) :

| Hypothèse | Valeur |
|---|---|
| Coût d'un code de réduction | 10 £ |
| Achat futur d'un client retenu | 50 £ |
| Taux de réussite du code | 30 % |

- Client qui part et reçoit le code : gain espéré de 0,30 × 50 − 10 = **+5 £**.
- Client qui serait resté et reçoit le code : perte de **−10 £**.
- Le code est rentable si la probabilité de départ dépasse 10 / (0,30 × 50), soit **66,7 %**.

Dans l'application, ces trois valeurs peuvent être modifiées et le seuil se recalcule.

## 4. Résultats

Mesurés sur les 519 clients du jeu de test :

| | Envoyer à tous (référence) | Règle « dernier achat » | Régression logistique |
|---|---|---|---|
| AUC | non applicable | 0,61 | **0,74** |
| Clients contactés | 519 | non applicable | 260 |
| Part des contactés qui ne rachètent pas | 57 % | non applicable | 74 % |
| Gain espéré | −720 £ | non applicable | **+280 £** |

Le seuil retenu sur l'entraînement est de 0,62. L'AUC vaut 0,5 pour le hasard et 1 pour un classement parfait. Le gain espéré applique les hypothèses du paragraphe 3 : ce n'est pas un gain mesuré sur de vrais envois.

## 5. Lancer le projet

Python 3.10 ou plus, dans un environnement virtuel activé. La base `data/base_clients_modelisation.csv` est déjà dans le dépôt.

```bash
pip install -r requirements.txt
python -m backend.train
pytest
streamlit run frontend/app.py
```

L'application a quatre écrans : Décision (un client), Campagne (liste des clients à contacter), Exploration (graphiques) et Le modèle (performances, variables, limites).

## 6. Architecture du dépôt

```
backend/            logique métier, aucun import de Streamlit
  config.py         chemins, graine, hypothèses (coût du code, achat futur, taux de réussite)
  sql/*.sql         requêtes SQL versionnées
  data.py           données brutes -> SQLite -> table d'analyse
  model.py          pipeline de la régression logistique, gain et seuil
  train.py          entraîne, évalue et sauvegarde le modèle
  service.py        seule interface appelée par le frontend
frontend/app.py     application Streamlit : affichage et saisie uniquement
tests/              tests pytest
docs/               note de cadrage, Data Quality Card, Model Card, note de synthèse,
                    slides, journal d'usage de l'IA, dictionnaire des variables
data/raw/           données brutes, jamais modifiées
data/               base d'analyse base_clients_modelisation.csv
requirements.txt    versions fixées
```

## 7. Limites

- Le modèle est testé sur une seule période (10 novembre au 9 décembre 2011), juste avant Noël. Les résultats peuvent être différents sur un autre mois.
- Le coût du code, l'achat futur et le taux de réussite sont des hypothèses, pas des mesures. Le modèle prédit qui risque de ne pas racheter, pas si le code les fera rester.
- Le test compte 519 clients : le gain espéré peut varier de plusieurs dizaines de livres selon le tirage des clients.
- Environ un quart des lignes d'origine n'ont pas de numéro de client et sont exclues. Seuls les clients actifs (achat dans les 90 jours) sont pris en compte.
- Le modèle utilise uniquement le comportement d'achat : il n'y a pas d'âge, de revenu ni de raison de départ.
- Les données couvrent un an : il n'y a pas de test sur une autre année.