"""Tests sur la logique métier : seuil de rentabilité, gains, liste de clients à contacter."""
import pytest

from backend import config, service
from backend.model import calculer_gain_metier


def test_seuil_de_rentabilite_par_defaut():
    # 10 / (0,30 x 50) = 2/3
    regle = service.calculer_seuil(0.30, 10.0, 50.0)
    assert regle["seuil"] == pytest.approx(2 / 3)
    assert regle["rentable"]
    assert regle["gain_vrai_partant"] == pytest.approx(5.0)


def test_meme_seuil_dans_config_et_dans_le_service():
    # Le seuil ne doit pas avoir deux valeurs à deux endroits du code.
    regle = service.calculer_seuil(config.TAUX_SUCCES, config.COUT_PROMO, config.VALEUR_RETENUE)
    assert config.SEUIL_THEORIQUE == pytest.approx(regle["seuil"])


def test_code_jamais_rentable_si_trop_cher():
    # 0,10 x 50 = 5 £ de gain maximum, pour un code à 10 £ : on n'envoie à personne.
    assert not service.calculer_seuil(0.10, 10.0, 50.0)["rentable"]


def test_gain_espere_nul_au_seuil_et_positif_au_dessus():
    assert service.gain_espere_envoi(2 / 3, 0.30, 10.0, 50.0) == pytest.approx(0.0)
    assert service.gain_espere_envoi(0.9, 0.30, 10.0, 50.0) > 0
    assert service.gain_espere_envoi(0.5, 0.30, 10.0, 50.0) < 0


def test_gain_de_campagne_sur_un_petit_exemple():
    y_vrai = [1, 0, 1, 0]
    y_predit = [1, 1, 0, 0]
    # partant contacté : +5 ; resté contacté : -10 ; les autres : 0
    gain_total, gain_moyen = calculer_gain_metier(y_vrai, y_predit)
    assert gain_total == pytest.approx(-5.0)
    assert gain_moyen == pytest.approx(-2.5)


def test_liste_cibles_rentable_triee_et_limitee_au_budget(modele_entraine):
    cibles, bilan = service.liste_cibles(0.30, 10.0, 50.0, budget_max=50)
    assert len(cibles) == bilan["nb_clients"] <= 50
    assert (cibles["gain_espere"] > 0).all()
    assert cibles["proba_churn"].is_monotonic_decreasing
    assert bilan["cout_total"] == pytest.approx(len(cibles) * 10.0)


def test_analyser_client_refuse_un_identifiant_invalide(modele_entraine):
    assert service.analyser_client("abc", 0.30, 10.0, 50.0)["erreur"]
    assert service.analyser_client(1, 0.30, 10.0, 50.0)["erreur"]


def test_analyser_client_donne_une_decision_coherente(modele_entraine):
    client = service.get_liste_ids()[0]
    r = service.analyser_client(client, 0.30, 10.0, 50.0)
    assert 0 <= r["proba_churn"] <= 1
    assert r["envoyer"] == (r["proba_churn"] > r["seuil"])
