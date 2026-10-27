"""
Interface Streamlit : affichage et saisie uniquement.
Tous les calculs (probabilités, seuil, gains) sont faits dans backend/service.py.
Lancement : streamlit run frontend/app.py
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import altair as alt
import pandas as pd
import streamlit as st

import backend.service as service

DEVISE = "£"  # les montants du jeu de données Online Retail sont en livres sterling
PAGES = ["1. Décision", "2. Campagne", "3. Exploration", "4. Le modèle"]

st.set_page_config(page_title="Fidélisation client - Online Retail", layout="wide")

# ---------------------------------------------------------------- Noms lisibles des variables
LIBELLES = {
    "recence_jours": "Jours depuis le dernier achat",
    "anciennete_jours": "Ancienneté (jours)",
    "nb_factures": "Nombre de factures",
    "nb_jours_achat": "Nombre de jours d'achat",
    "nb_articles_total": "Articles achetés (total)",
    "depense_totale": "Dépense totale",
    "panier_moyen": "Panier moyen",
    "frequence_achat_mensuelle": "Fréquence d'achat (par mois)",
    "intervalle_moyen_jours": "Délai moyen entre deux achats",
    "nb_factures_30j": "Factures sur les 30 derniers jours",
    "depense_30j": "Dépense sur les 30 derniers jours",
    "nb_factures_90j": "Factures sur les 90 derniers jours",
    "depense_90j": "Dépense sur les 90 derniers jours",
    "nb_produits_distincts": "Produits différents achetés",
    "nb_annulations": "Annulations",
    "categorie_principale": "Catégorie principale",
    "pays": "Pays",
    "proba_churn": "Probabilité de ne pas racheter",
    "gain_espere": f"Gain espéré ({DEVISE})",
    "CustomerID": "Client",
}


def libelle(nom):
    if nom in LIBELLES:
        return LIBELLES[nom]
    if nom.startswith("part_"):
        return "Part des achats : " + nom[5:].replace("_", " ")
    if nom.startswith("categorie_principale_"):
        return "Catégorie principale : " + nom[len("categorie_principale_"):]
    if nom.startswith("pays_"):
        return "Pays : " + nom[5:]
    if nom.startswith("missingindicator_"):
        return "Délai entre achats non calculable"
    return nom


def montant(x):
    return f"{x:,.0f} {DEVISE}".replace(",", " ")


# ---------------------------------------------------------------- Graphiques
def barres_verticales(df, titre_y="Part de clients qui ne rachètent pas"):
    return alt.Chart(df).mark_bar(color="#555555").encode(
        x=alt.X("groupe:N", sort=list(df["groupe"]), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("part_churn:Q", title=titre_y, axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
        tooltip=[alt.Tooltip("groupe:N", title="Groupe"),
                 alt.Tooltip("part_churn:Q", title="Part", format=".1%"),
                 alt.Tooltip("nb_clients:Q", title="Clients")],
    ).properties(height=280)


def barres_horizontales(df, x, y, titre_x):
    """Barres rouges (augmente le risque) ou bleues (le diminue), dans l'ordre du tableau."""
    return alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{x}:Q", title=titre_x),
        y=alt.Y(f"{y}:N", sort=list(df[y]), title=None),
        color=alt.condition(alt.datum[x] > 0, alt.value("#b03a2e"), alt.value("#2e6da4")),
    ).properties(height=30 * len(df) + 40)


# ---------------------------------------------------------------- Chargement (mis en cache)
@st.cache_data
def charger_ids():
    return service.get_liste_ids()


@st.cache_data
def charger_exploration():
    return service.get_exploration()


@st.cache_data
def charger_coefficients():
    return service.get_coefficients()


@st.cache_data
def charger_metriques():
    return service.get_metriques()


# ---------------------------------------------------------------- Barre latérale
hyp = service.get_hypotheses()
st.sidebar.title("Fidélisation client")
page = st.sidebar.radio("Navigation", PAGES)

st.sidebar.markdown("---")
st.sidebar.subheader("Hypothèses de calcul")
st.sidebar.caption("Ces valeurs ne viennent pas des données : modifie-les pour voir l'effet sur la décision.")
taux_succes = st.sidebar.slider(
    "Taux de réussite du code", 0.10, 1.00, float(hyp["taux_succes"]), 0.05,
    help="Part des clients sur le point de partir qui restent grâce au code.")
cout_promo = st.sidebar.slider(f"Coût du code ({DEVISE})", 1.0, 30.0, float(hyp["cout_promo"]), 1.0)
valeur_retenue = st.sidebar.slider(
    f"Achat futur d'un client retenu ({DEVISE})", 10.0, 200.0, float(hyp["valeur_retenue"]), 5.0)

regle = service.calculer_seuil(taux_succes, cout_promo, valeur_retenue)
if regle["rentable"]:
    st.sidebar.success(f"Seuil de rentabilité : {regle['seuil']:.1%}")
else:
    st.sidebar.error("Avec ces hypothèses, le code n'est rentable pour aucun client.")

st.title("Fidélisation client - Online Retail")

# ================================================================ 1. DÉCISION
if page == PAGES[0]:
    st.header("Décision pour un client")
    st.write("Choisis un client actif. L'application donne la probabilité qu'il ne rachète pas "
             "dans les 30 jours et l'action recommandée.")

    client = st.selectbox("Numéro du client", charger_ids(), index=None,
                          placeholder="Choisir ou taper un numéro")
    if client is None:
        st.info("Aucun client choisi.")
    else:
        r = service.analyser_client(client, taux_succes, cout_promo, valeur_retenue)
        if r.get("erreur"):
            st.error(r["erreur"])
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Probabilité de ne pas racheter", f"{r['proba_churn']:.1%}")
            c2.metric("Seuil de rentabilité", f"{r['seuil']:.1%}" if r["rentable"] else "Jamais atteint")
            c3.metric("Gain espéré si on envoie le code", f"{r['gain_espere']:+.1f} {DEVISE}")
            st.progress(min(max(r["proba_churn"], 0.0), 1.0))

            if r["envoyer"]:
                st.success("Action recommandée : envoyer le code promo.")
            elif not r["rentable"]:
                st.warning("Action recommandée : ne rien envoyer. Avec ces hypothèses, "
                           "le code n'est rentable pour aucun client.")
            else:
                st.info("Action recommandée : ne rien envoyer. La probabilité de départ "
                        "est sous le seuil de rentabilité.")

            onglet_profil, onglet_facteurs, onglet_verif = st.tabs(
                ["Profil du client", "Pourquoi ce score ?", "Vérification"])

            with onglet_profil:
                p = r["profil"]
                a, b, c, d = st.columns(4)
                a.metric(libelle("recence_jours"), f"{p['recence_jours']:.0f} j")
                b.metric(libelle("nb_factures"), f"{p['nb_factures']:.0f}")
                c.metric(libelle("depense_totale"), montant(p["depense_totale"]))
                d.metric(libelle("panier_moyen"), montant(p["panier_moyen"]))
                e, f, g, h = st.columns(4)
                e.metric(libelle("anciennete_jours"), f"{p['anciennete_jours']:.0f} j")
                f.metric(libelle("nb_factures_90j"), f"{p['nb_factures_90j']:.0f}")
                g.metric(libelle("categorie_principale"), p["categorie_principale"])
                h.metric(libelle("pays"), p["pays"])

            with onglet_facteurs:
                st.write("Effet de chaque variable sur le score de ce client, par rapport à un client moyen. "
                         "Rouge : augmente le risque de ne pas racheter. Bleu : le diminue.")
                effets = pd.concat([r["facteurs"]["hausse"], r["facteurs"]["baisse"]])
                if effets.empty:
                    st.write("Aucun effet à afficher.")
                else:
                    tableau = pd.DataFrame({"variable": [libelle(n) for n in effets.index],
                                            "effet": effets.values})
                    st.altair_chart(barres_horizontales(tableau, "effet", "variable", "Effet sur le score"),
                                    use_container_width=True)

            with onglet_verif:
                st.write("La période de test est passée, donc on connaît ce qui s'est réellement produit "
                         "pour ce client. Cela permet de vérifier le modèle.")
                if r["churn_reel"] == 1:
                    st.write("Ce client **n'a pas racheté** dans les 30 jours qui ont suivi le 9 novembre 2011.")
                else:
                    st.write("Ce client **a racheté** dans les 30 jours qui ont suivi le 9 novembre 2011.")
                st.caption("Le modèle a été entraîné sur une partie des clients : pour ceux-là, "
                           "la vérification est moins parlante que pour les clients du jeu de test.")

# ================================================================ 2. CAMPAGNE
elif page == PAGES[1]:
    st.header("Campagne : clients à contacter")
    st.write("Clients pour lesquels envoyer le code a un gain espéré positif, du plus risqué au moins risqué.")

    _, total = service.liste_cibles(taux_succes, cout_promo, valeur_retenue)
    if total["nb_clients"] == 0:
        st.warning("Avec ces hypothèses, aucun client n'est rentable à contacter. "
                   "Modifie les hypothèses dans la barre latérale.")
    else:
        budget = st.number_input("Nombre maximum de codes à envoyer", min_value=1,
                                 max_value=int(total["nb_clients"]), value=int(total["nb_clients"]), step=10)
        cibles, bilan = service.liste_cibles(taux_succes, cout_promo, valeur_retenue, budget_max=budget)

        c1, c2, c3 = st.columns(3)
        c1.metric("Clients contactés", f"{bilan['nb_clients']}")
        c2.metric("Coût des codes", montant(bilan["cout_total"]))
        c3.metric("Gain espéré", montant(bilan["gain_total"]))
        st.caption("Gain espéré calculé avec les hypothèses de la barre latérale. "
                   "Les scores portent sur tous les clients de la base, y compris ceux qui ont servi "
                   "à entraîner le modèle.")

        affichage = cibles.copy()
        affichage["proba_churn"] = affichage["proba_churn"] * 100
        affichage = affichage.rename(columns=libelle)
        st.dataframe(
            affichage, hide_index=True, use_container_width=True,
            column_config={libelle("proba_churn"): st.column_config.ProgressColumn(
                libelle("proba_churn"), format="%.0f %%", min_value=0, max_value=100)})

        csv = cibles.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button("Télécharger la liste (CSV)", data=csv,
                           file_name="clients_a_contacter.csv", mime="text/csv")

# ================================================================ 3. EXPLORATION
elif page == PAGES[2]:
    st.header("Exploration des clients")
    expl = charger_exploration()
    if expl is None:
        st.error("Impossible de charger les données.")
    else:
        r = expl["resume"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Clients actifs", f"{r['nb_clients']}")
        c2.metric("Part qui ne rachète pas (churn)", f"{r['taux_churn']:.1%}")
        c3.metric("Panier moyen", montant(r["panier_moyen"]))
        c4.metric("Dépense moyenne par client", montant(r["depense_moyenne"]))
        st.caption("Clients ayant acheté dans les 90 jours avant le 9 novembre 2011. "
                   "Le churn est mesuré sur les 30 jours suivants.")

        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Selon le délai depuis le dernier achat")
            st.altair_chart(barres_verticales(expl["par_recence"]), use_container_width=True)
        with g2:
            st.subheader("Selon le nombre de factures")
            st.altair_chart(barres_verticales(expl["par_factures"]), use_container_width=True)

        st.subheader("Selon la catégorie principale")
        st.caption("Catégories avec au moins 20 clients.")
        st.altair_chart(barres_verticales(expl["par_categorie"]), use_container_width=True)

        with st.expander("Voir les données"):
            st.dataframe(expl["donnees"], hide_index=True, use_container_width=True)

# ================================================================ 4. LE MODÈLE
elif page == PAGES[3]:
    st.header("Le modèle")
    st.write("Le modèle est une régression logistique. Elle calcule, pour chaque client, la probabilité "
             "de ne pas racheter dans les 30 jours à partir de son historique d'achats.")

    st.subheader("1. Performances sur des clients jamais vus")
    m = charger_metriques()
    if m is None:
        st.info("Les performances ne sont pas enregistrées avec le modèle. "
                "Relance `python -m backend.train`.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AUC du modèle", f"{m['auc_test']:.2f}")
        c2.metric("AUC de la règle « dernier achat »", f"{m['auc_reference_recence']:.2f}")
        c3.metric("Gain espéré : envoi à tous", montant(m["gain_baseline"]))
        c4.metric("Gain espéré : modèle", montant(m["gain_modele"]))
        st.write(f"Le test porte sur {m['nb_test']} clients. Avec un seuil de {m['seuil_optimal']:.0%}, "
                 f"le modèle cible {m['nb_clients_cibles']} clients, dont "
                 f"{m['part_vrais_partants_cibles']:.0%} ne rachètent vraiment pas "
                 f"(contre {m['taux_churn_test']:.0%} dans l'ensemble des clients).")
        st.caption("L'AUC mesure si le modèle place un client qui part au-dessus d'un client qui reste : "
                   "0,5 correspond au hasard, 1 à un classement parfait. Les gains sont calculés avec les "
                   "hypothèses par défaut, pas avec celles de la barre latérale.")

    st.subheader("2. Variables les plus importantes")
    coefs = charger_coefficients()
    top = coefs.head(10).copy()
    top["variable"] = top["variable"].map(libelle)
    st.altair_chart(barres_horizontales(top, "poids", "variable", "Poids dans le modèle"),
                    use_container_width=True)
    st.caption("Rouge : la variable augmente le risque de ne pas racheter. Bleu : elle le diminue. "
               "Les variables sont mises à la même échelle, donc leurs poids se comparent. "
               "Certaines variables sont proches (par exemple le nombre de factures et le nombre de jours "
               "d'achat) : leurs poids se compensent en partie et ne se lisent pas un par un.")
    with st.expander("Toutes les variables"):
        tout = coefs.copy()
        tout["variable"] = tout["variable"].map(libelle)
        st.dataframe(tout.rename(columns={"variable": "Variable", "poids": "Poids"}),
                     hide_index=True, use_container_width=True)

    st.subheader("3. Comment la décision est prise")
    st.write("Si on envoie le code à un client dont la probabilité de ne pas racheter est p :")
    st.latex(r"\text{gain espéré} = p \times \text{taux de réussite} \times \text{achat futur} - \text{coût du code}")
    if regle["rentable"]:
        st.write(f"Le gain est positif quand p dépasse coût / (taux × achat futur) = "
                 f"{cout_promo:.0f} / ({taux_succes:.2f} × {valeur_retenue:.0f}) = **{regle['seuil']:.1%}**. "
                 "Le code est envoyé aux clients au-dessus de ce seuil.")
    else:
        st.write(f"Avec un taux de réussite de {taux_succes:.0%}, le gain espéré est négatif même pour un "
                 "client qui partira à coup sûr : aucun code n'est envoyé.")

    st.subheader("4. Limites")
    st.markdown(
        "- Le modèle est testé sur une seule période (du 10 novembre au 9 décembre 2011), juste avant Noël. "
        "Rien ne garantit les mêmes résultats sur un autre mois.\n"
        f"- Le coût du code ({cout_promo:.0f} {DEVISE}), l'achat futur ({valeur_retenue:.0f} {DEVISE}) et le taux de "
        "réussite sont des hypothèses, pas des mesures. Le modèle prédit qui risque de partir, "
        "pas si le code les fera rester.\n"
        f"- Le test ne compte que {m['nb_test'] if m else 'quelques centaines de'} clients : les gains en euros "
        "peuvent varier de plusieurs dizaines d'euros d'un tirage à l'autre.\n"
        "- Seuls les clients identifiés (environ 25 % des lignes d'origine n'ont pas de numéro de client) "
        "et actifs sur les 90 derniers jours sont pris en compte.\n"
        "- Le modèle ne voit que le comportement d'achat : pas d'âge, de revenu ni de motif de départ.")