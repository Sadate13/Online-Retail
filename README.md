# Système de Fidélisation Client - Prédiction de Réachat (Online Retail)

Ce projet de Data Mining utilise un modèle d'apprentissage supervisé pour prédire le comportement d'achat des clients, accompagné d'une interface de décision pour le métier.

## 1. La question business

Le budget alloué aux campagnes de relance et aux codes promotionnels étant limité, il est important de savoir **quels clients actifs ont le moins de probabilité de racheter le mois prochain**, afin de les cibler en priorité avec une offre de rétention ?

*Objectif : Le système CRM enverra automatiquement un e-mail avec un code de réduction aux clients identifiés (prédiction d'absence d'achat), permettant d'optimiser le budget promotionnel en ciblant les clients avec la bonne probabilité.*

## 2. Les résultats chiffrés



## 3. Comment lancer le projet

Le projet est conçu pour être lancé en 4 commandes maximum à partir de la racine du dépôt :

```bash
# 1. Créer et activer l'environnement virtuel (selon OS)
python -m venv .venv
.\.venv\Scripts\Activate.ps1  

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Entraîner le modèle (crée la base de données et le fichier modèle)
python -m backend.train

# 4. Lancer l'interface utilisateur
streamlit run frontend/app.py