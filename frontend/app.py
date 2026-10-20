import streamlit as st
import pandas as pd
import numpy as np
# Remarque : Plus tard, nous importerons le backend ici :
# import backend.service as service

# Configuration de la page
st.set_page_config(page_title="Prédiction Churn - Online Retail", layout="wide")

# Menu de navigation sur le côté
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller vers :", ["1. Décision (Recommandation)", "2. Exploration des données", "3. Explication du Modèle"])

st.title("Système de Fidélisation Client - Online Retail")

# ==========================================
# ÉCRAN 1 : DÉCISION (Le cœur de l'app métier)
# ==========================================
if page == "1. Décision (Recommandation)":
    st.header("Action Recommandée par Client")
    st.write("Saisissez l'ID d'un client pour savoir s'il faut lui envoyer une promotion.")

    # Zone de saisie
    customer_id_input = st.text_input("ID du Client (ex: 12346, 17850)", "")

    if st.button("Analyser ce client"):
        if customer_id_input:
            # TODO: Ici, nous appellerons le vrai modèle plus tard.
            # prediction = service.predict_client(customer_id_input)
            
            # --- FAUSSES DONNÉES (MOCK) POUR LE FRONTEND ---
            # On simule la réponse du backend
            simulated_prob = np.random.rand() # Probabilité de churn entre 0 et 1
            seuil = 0.6 # Le seuil de rentabilité défini dans config.py
            
            st.subheader(f"Résultats pour le client {customer_id_input}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Probabilité de ne pas racheter (Churn)", f"{simulated_prob*100:.1f}%")
            
            with col2:
                if simulated_prob > seuil:
                    st.error("🚨 Risque de churn élevé.")
                    st.success("✅ Action recommandée : ENVOYER CODE PROMO (-10%)")
                else:
                    st.info("🟢 Client fidèle.")
                    st.warning("❌ Action recommandée : NE RIEN ENVOYER (Économie du coût de la promo)")
                    
        else:
            st.warning("Veuillez entrer un ID client valide.")

# ==========================================
# ÉCRAN 2 : EXPLORATION
# ==========================================
elif page == "2. Exploration des données":
    st.header("Analyse Globale des Clients")
    st.write("Cet écran affichera les segments clients et les statistiques globales.")
    
    # --- FAUSSES DONNÉES (MOCK) ---
    st.write("*Données simulées en attendant le backend*")
    mock_data = pd.DataFrame({
        'Segment': ['VIP', 'Récents', 'À risque', 'Perdus'],
        'Nombre de clients': [450, 1200, 800, 1500]
    })
    st.bar_chart(mock_data.set_index('Segment'))
    
    # On peut imaginer d'autres graphiques ici (évolution CA, etc.)

# ==========================================
# ÉCRAN 3 : LE MODÈLE
# ==========================================
elif page == "3. Explication du Modèle":
    st.header("Performance et Interprétation du Modèle")
    st.write("Comment le modèle prend-il ses décisions ?")
    
    # --- FAUSSES DONNÉES (MOCK) ---
    st.subheader("Variables les plus importantes")
    mock_importance = pd.DataFrame({
        'Variable': ['Récence (Jours depuis dernier achat)', 'Fréquence (Nb de commandes)', 'Montant Total', 'Nb retours'],
        'Importance (%)': [45, 30, 15, 10]
    }).sort_values(by='Importance (%)', ascending=True)
    
    st.bar_chart(mock_importance.set_index('Variable'))
    
    st.subheader("Limites actuelles")
    st.write("- Le modèle se base uniquement sur l'historique d'achat, aucune donnée démographique n'est disponible.")
    st.write("- Les comportements d'achat festifs (Noël) peuvent fausser les prédictions mensuelles classiques.")