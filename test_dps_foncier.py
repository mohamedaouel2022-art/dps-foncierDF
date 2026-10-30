"""Tests du moteur DPS Foncier.

Les valeurs attendues ont été recalculées à la main.
"""

import pytest

from dps_foncier import (
    Operation,
    cours_action_nouvelle,
    dilution_apport_immeuble,
    parite_nouvelles_actions,
    simulation_associe,
    terp,
    valeur_droit,
    valeur_droit_periode,
)


@pytest.fixture
def op():
    # 1 action nouvelle pour 4 anciennes, à 15 contre un cours de 20
    return Operation(
        actions_anciennes=1_000_000,
        cours_cum=20.0,
        prix_souscription=15.0,
        parite_nouvelles=1,
        parite_anciennes=4,
    )


def test_actions_nouvelles(op):
    assert parite_nouvelles_actions(op) == 250_000


def test_cours_theorique(op):
    # (1 000 000 x 20 + 250 000 x 15) / 1 250 000 = 19
    assert terp(op) == pytest.approx(19.0)


def test_valeur_droit(op):
    assert valeur_droit(op) == pytest.approx(1.0)


def test_exercer_et_vendre_sont_neutres_au_cours_theorique(op):
    r = simulation_associe(op, actions_detenues=10_000)
    assert r["exercer"]["gain_ou_perte"] == pytest.approx(0.0)
    assert r["vendre"]["gain_ou_perte"] == pytest.approx(0.0)


def test_laisser_expirer_fait_perdre_la_valeur_des_droits(op):
    r = simulation_associe(op, actions_detenues=10_000)
    assert r["expirer"]["gain_ou_perte"] == pytest.approx(-10_000.0)


def test_participation_exercer_conserve_le_pourcentage(op):
    r = simulation_associe(op, actions_detenues=10_000)
    assert r["participation_initiale"] == pytest.approx(0.01)
    assert r["exercer"]["participation_finale"] == pytest.approx(0.01)


def test_participation_vendre_est_diluee(op):
    r = simulation_associe(op, actions_detenues=10_000)
    assert r["vendre"]["participation_finale"] == pytest.approx(0.008)
    assert r["expirer"]["participation_finale"] == pytest.approx(0.008)


def test_vendre_au_dessus_de_la_valeur_theorique_est_avantageux(op):
    r = simulation_associe(op, actions_detenues=10_000, prix_droit_marche=1.2)
    assert r["vendre"]["gain_ou_perte"] == pytest.approx(2_000.0)


def test_vendre_sous_la_valeur_theorique_est_defavorable(op):
    r = simulation_associe(op, actions_detenues=10_000, prix_droit_marche=0.8)
    assert r["vendre"]["gain_ou_perte"] == pytest.approx(-2_000.0)


def test_apport_immeuble_surevalue():
    r = dilution_apport_immeuble(
        actions_anciennes=1_000_000,
        cours=20.0,
        prix_emission=20.0,
        valeur_declaree=5_000_000,
        valeur_reelle=3_500_000,
    )
    assert r["actions_emises_a_l_apporteur"] == pytest.approx(250_000)
    assert r["part_apporteur"] == pytest.approx(0.2)
    assert r["valeur_par_action_apres"] == pytest.approx(18.8)
    assert r["perte_par_action_pour_les_autres"] == pytest.approx(1.2)
    assert r["perte_totale_autres_associes"] == pytest.approx(1_200_000)
    assert r["ecart_valeur_declaree_reelle"] == pytest.approx(1_500_000)


def test_apport_immeuble_evalue_correctement_ne_dilue_pas():
    r = dilution_apport_immeuble(1_000_000, 20.0, 20.0, 5_000_000, 5_000_000)
    assert r["perte_par_action_pour_les_autres"] == pytest.approx(0.0)


def test_parametres_invalides():
    with pytest.raises(ValueError):
        Operation(0, 20.0, 15.0, 1, 4)
    with pytest.raises(ValueError):
        Operation(1000, 20.0, -1.0, 1, 4)
    with pytest.raises(ValueError):
        Operation(1000, 20.0, 15.0, 1, 0)


def test_actions_detenues_superieures_au_capital(op):
    with pytest.raises(ValueError):
        simulation_associe(op, actions_detenues=2_000_000)


# --- Exemples du document de la Bourse de Tunis (BVMT, mise à jour mars 2009) ---

@pytest.fixture
def wifak():
    # Exemple n°1 : 1 action nouvelle pour 2 anciennes à 6,500 DT, cours 8,000 DT, D = 0,350 DT
    return Operation(1_000_000, 8.0, 6.5, 1, 2, difference_jouissance=0.35)


def test_bvmt_exemple_1_droit_au_detachement(wifak):
    # 1/3 x (8,000 - 6,500 - 0,350) = 0,3833. Le document affiche 0,390, valeur arrondie
    # qui ne correspond pas à sa propre formule.
    assert valeur_droit(wifak) == pytest.approx(1.15 / 3)
    assert terp(wifak) == pytest.approx(8.0 - 1.15 / 3)


def test_bvmt_exemple_1_droit_pendant_la_periode(wifak):
    # 1/2 x (8,030 - 6,500 - 0,350) = 0,590 : valeur exacte du document
    assert valeur_droit_periode(wifak, 8.03) == pytest.approx(0.59)


def test_bvmt_action_nouvelle_non_assimilee():
    assert cours_action_nouvelle(8.03, 0.35) == pytest.approx(7.68)


def test_difference_de_jouissance_reduit_la_valeur_du_droit():
    sans = Operation(1_000_000, 20.0, 15.0, 1, 4)
    avec = Operation(1_000_000, 20.0, 15.0, 1, 4, difference_jouissance=0.5)
    assert valeur_droit(avec) == pytest.approx(valeur_droit(sans) - 0.2 * 0.5)


def test_exercer_et_vendre_restent_neutres_avec_difference_de_jouissance(wifak):
    r = simulation_associe(wifak, actions_detenues=10_000)
    assert r["exercer"]["gain_ou_perte"] == pytest.approx(0.0, abs=1e-2)
    assert r["vendre"]["gain_ou_perte"] == pytest.approx(0.0, abs=1e-2)
    assert r["expirer"]["gain_ou_perte"] == pytest.approx(-10_000 * 1.15 / 3, abs=1e-2)


def test_difference_de_jouissance_negative_refusee():
    with pytest.raises(ValueError):
        Operation(1000, 20.0, 15.0, 1, 4, difference_jouissance=-0.1)
