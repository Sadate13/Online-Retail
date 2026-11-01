"""Test de démarrage de l'application Streamlit."""
import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["1. Décision", "2. Campagne", "3. Exploration", "4. Le modèle"]


@pytest.mark.parametrize("page", PAGES)
def test_chaque_ecran_s_affiche_sans_erreur(modele_entraine, page):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception
    assert app.title[0].value == "Fidélisation client - Online Retail"
