# Journal d'usage de l'IA

Exemple de journal pour le projet Online Retail. Le code final est réel : chaque ligne renvoie à un fichier de ce dépôt. Les prompts et les réponses de l'IA sont reconstitués.
Outils utilisés : Claude code

| # | Fichier ou étape | Le prompt (résumé) | Ce que l'IA a produit | Gardé | Corrigé, et pourquoi | Refusé, et pourquoi |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `backend/data.py` et `sql/*.sql` | « Crée l'arborescence et le pipeline de données pour Online Retail » | Scripts SQL et orchestration pandas/SQLite | L'architecture de base et le pipeline d'extraction SQLite respectant la stricte séparation backend/frontend. | | |
| 2 | `backend/train.py` | « Optimise le seuil de décision métier » | Seuil calculé sur `X_test`, `y_test` en supposant 100% de réussite promotionnelle | | Le calcul du seuil a été déplacé sur l'entraînement (`X_train`) : l'optimisation sur le test provoquait une fuite de données (data leakage). Ajout d'un taux de succès réaliste (30%). | |
| 3 | `backend/model.py` | « Instancie le modèle de régression logistique » | Régression logistique avec l'argument `class_weight='balanced'` | Le pipeline complet scikit-learn (avec imputer et scaler). | | Le poids `class_weight='balanced'` : refusé car il déforme les probabilités brutes, empêchant la stricte comparaison avec le seuil financier métier. |
| 4 | `backend/train.py` | « Trouve le meilleur seuil de rentabilité » | Boucle cherchant un optimum empirique par itération (trouvant ~60%) | | | La boucle empirique. Remplacée par l'équation bayésienne analytique (Coût / (Taux × Valeur) = 66,7%) car l'algorithme surapprenait sur le bruit de l'échantillon. |
| 5 | `frontend/app.py` | « Affiche les performances du modèle et la règle de décision » | Application Streamlit avec erreurs d'exécution et arrondis imprécis ("67%") | Le routage des pages et la structure des colonnes (UI). | Remplacement par un formatage exact (`{regle['seuil']:.1%}`) pour lier dynamiquement le texte aux manipulations des curseurs de la barre latérale. | |

### Bilan en 3 lignes
- **Ce que l'IA nous a fait gagner :** le squelette de l'application Streamlit et la structure d'intégration de la base SQLite, codés en quelques minutes.
- **L'erreur qui nous aurait coûté le plus cher :** l'optimisation du seuil de décision sur le jeu de test (fuite de données). Le modèle affichait un gain illusoire de près de 10 000 €, que nous aurions validé à tort.
- **Ce que nous ne lui confierions pas sans relecture :** le calibrage des probabilités. L'IA a initialement faussé les prédictions avec une pondération artificielle et cherché un seuil empirique au lieu d'appliquer la stricte équation des coûts du client.