# Système de Fidélisation Client - Prédiction de Réachat (Online Retail)

Ce projet de Data Mining utilise un modèle d'apprentissage supervisé pour prédire le comportement d'achat des clients, accompagné d'une interface de décision pour le métier.

## 1. La question business

Le budget alloué aux campagnes de relance et aux codes promotionnels étant limité, il est important de savoir **quels clients actifs ont le moins de probabilité de racheter le mois prochain**, afin de les cibler en priorité avec une offre de rétention ?

*Objectif : Le système CRM enverra automatiquement un e-mail avec un code de réduction aux clients identifiés (prédiction d'absence d'achat), permettant d'optimiser le budget promotionnel en ciblant les clients avec la bonne probabilité.*

## 2. Le choix du modèle

Nous avons opté pour un modèle de **Régression Logistique**. Le jeu de données final, après nettoyage, ne contenant qu'environ 2 500 clients actifs, ce modèle linéaire simple est idéal. Il permet d'éviter le surapprentissage (overfitting) qui pourrait survenir avec des modèles plus complexes (comme le Random Forest) sur de petits échantillons. De plus, il offre une excellente interprétabilité pour le métier grâce à l'analyse des poids (coefficients) attribués à chaque variable.

## 3. Comment lancer le projet

Le projet est conçu pour être lancé en 4 commandes maximum à partir de la racine du dépôt :

```bash
# 1. Créer et activer l'environnement virtuel (selon OS)
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Sur Windows
# source .venv/bin/activate   # Sur Linux/Mac

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Entraîner le modèle (crée la base de données et le fichier modèle)
python -m backend.train

# 4. Lancer l'interface utilisateur
streamlit run frontend/app.py