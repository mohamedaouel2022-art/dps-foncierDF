"""Tests du module juridique tunisien."""

import pytest

from droit_tunisien import (
    ATTENTION,
    BLOQUANT,
    REFERENCES,
    OperationJuridique,
    analyser,
    rapport_texte,
)


def trouver(alertes, theme, gravite=None):
    return [a for a in alertes if a.theme == theme and (gravite is None or a.gravite == gravite)]


def sa_numeraire(**kw):
    base = dict(forme="SA", liberation="numeraire", age_tenue=True,
                publication_jort=True, delai_souscription_jours=15)
    base.update(kw)
    return OperationJuridique(**base)


def test_delai_sa_trop_court():
    alertes = analyser(sa_numeraire(delai_souscription_jours=10))
    bloquants = trouver(alertes, "Délai", BLOQUANT)
    assert len(bloquants) == 1
    assert "CSC art. 301" in bloquants[0].references


def test_delai_sa_quinze_jours_accepte():
    assert not trouver(analyser(sa_numeraire()), "Délai")


def test_delai_sarl_vingt_et_un_jours():
    op = dict(forme="SARL", liberation="numeraire", age_tenue=True)
    assert trouver(analyser(OperationJuridique(delai_souscription_jours=20, **op)), "Délai", BLOQUANT)
    assert not trouver(analyser(OperationJuridique(delai_souscription_jours=21, **op)), "Délai")


def test_delai_non_renseigne():
    alertes = analyser(sa_numeraire(delai_souscription_jours=None))
    assert trouver(alertes, "Délai", ATTENTION)


def test_publication_jort_manquante():
    alertes = analyser(sa_numeraire(publication_jort=False))
    assert trouver(alertes, "Publicité", BLOQUANT)


def test_decision_assemblee_manquante():
    alertes = analyser(sa_numeraire(age_tenue=False))
    assert trouver(alertes, "Décision", BLOQUANT)


def test_suppression_dps_sans_rapport_des_commissaires():
    alertes = analyser(sa_numeraire(dps_supprime=True, rapport_conseil=True, rapport_cac=False))
    b = trouver(alertes, "Suppression du DPS", BLOQUANT)
    assert len(b) == 1
    assert "commissaires aux comptes" in b[0].message
    assert "CSC art. 300" in b[0].references


def test_suppression_dps_avec_les_deux_rapports():
    alertes = analyser(sa_numeraire(dps_supprime=True, rapport_conseil=True, rapport_cac=True))
    assert not trouver(alertes, "Suppression du DPS", BLOQUANT)


def test_apport_en_nature_sans_commissaire():
    op = OperationJuridique(forme="SA", liberation="nature", age_tenue=True)
    alertes = analyser(op)
    assert len(trouver(alertes, "Apport en nature", BLOQUANT)) == 2  # commissaire et approbation


def test_evaluation_reduite_sans_accord_apporteur():
    op = OperationJuridique(forme="SA", liberation="nature", age_tenue=True,
                            commissaire_apports=True, evaluation_approuvee=True,
                            evaluation_reduite_par_age=True, accord_apporteur=False)
    b = trouver(analyser(op), "Apport en nature", BLOQUANT)
    assert len(b) == 1
    assert "accord exprès" in b[0].message


def test_ecart_de_valeur_au_dessus_du_seuil():
    op = OperationJuridique(forme="SA", liberation="nature", age_tenue=True,
                            commissaire_apports=True, evaluation_approuvee=True,
                            valeur_declaree=5_000_000, valeur_expertisee=3_500_000)
    a = trouver(analyser(op), "Évaluation", ATTENTION)
    assert len(a) == 1
    assert "43%" in a[0].message


def test_ecart_de_valeur_sous_le_seuil():
    op = OperationJuridique(forme="SA", liberation="nature", age_tenue=True,
                            commissaire_apports=True, evaluation_approuvee=True,
                            valeur_declaree=3_600_000, valeur_expertisee=3_500_000)
    assert not trouver(analyser(op), "Évaluation")


def test_immeuble_immatricule_sans_inscription_ni_acte():
    op = sa_numeraire(apport_immeuble=True, immeuble_immatricule=True)
    b = trouver(analyser(op), "Droit foncier", BLOQUANT)
    assert len(b) == 2
    refs = {r for a in b for r in a.references}
    assert {"CSC art. 3", "CDR art. 305"} <= refs


def test_immeuble_immatricule_dossier_complet():
    op = sa_numeraire(apport_immeuble=True, immeuble_immatricule=True,
                      acte_forme_legale=True, inscription_livre_foncier_prevue=True)
    assert not trouver(analyser(op), "Droit foncier")


def test_immeuble_non_immatricule():
    a = trouver(analyser(sa_numeraire(apport_immeuble=True, immeuble_immatricule=False)),
                "Droit foncier", ATTENTION)
    assert len(a) == 1 and "CDR art. 317 et 318" in a[0].references


def test_immeuble_statut_inconnu():
    assert trouver(analyser(sa_numeraire(apport_immeuble=True)), "Droit foncier", ATTENTION)


def test_reserve_fonciere_et_droit_de_priorite():
    op = sa_numeraire(apport_immeuble=True, immeuble_immatricule=False, immeuble_en_reserve_fonciere=True)
    assert trouver(analyser(op), "Droit de priorité d'achat", ATTENTION)
    op.droit_priorite_purge = True
    assert not trouver(analyser(op), "Droit de priorité d'achat")


def test_acquereur_etranger_sans_autorisation_et_terre_agricole():
    op = sa_numeraire(apport_immeuble=True, immeuble_immatricule=False,
                      acquereur_etranger=True, terre_agricole=True)
    assert len(trouver(analyser(op), "Acquisition par un étranger", BLOQUANT)) == 2


def test_acquereur_etranger_avec_autorisation():
    op = sa_numeraire(apport_immeuble=True, immeuble_immatricule=False,
                      acquereur_etranger=True, autorisation_gouverneur=True)
    assert not trouver(analyser(op), "Acquisition par un étranger")


def test_sci_signale_la_forme():
    op = OperationJuridique(forme="SCI", age_tenue=True)
    assert trouver(analyser(op), "Forme", ATTENTION)


def test_souscription_incomplete():
    assert trouver(analyser(sa_numeraire(taux_souscription=0.5)), "Souscription", ATTENTION)
    info = trouver(analyser(sa_numeraire(taux_souscription=0.8, limitation_prevue=True)), "Souscription")
    assert info and info[0].gravite == "INFO"
    assert trouver(analyser(sa_numeraire(taux_souscription=0.97)), "Souscription")[0].gravite == "INFO"


def test_dossier_complet_sans_bloquant():
    op = OperationJuridique(
        forme="SA", liberation="nature", age_tenue=True, capital_libere=True, dps_supprime=True,
        rapport_conseil=True, rapport_cac=True, commissaire_apports=True,
        evaluation_approuvee=True, apport_immeuble=True, immeuble_immatricule=True,
        acte_forme_legale=True, inscription_livre_foncier_prevue=True,
    )
    assert not [a for a in analyser(op) if a.gravite == BLOQUANT]


def test_tri_des_alertes_par_gravite():
    op = sa_numeraire(delai_souscription_jours=5, apport_immeuble=True)
    ordre = [a.gravite for a in analyser(op)]
    assert ordre == sorted(ordre, key=["BLOQUANT", "ATTENTION", "INFO"].index)


def test_toutes_les_references_citees_existent():
    op = OperationJuridique(
        forme="SA", liberation="mixte", dps_supprime=True, apport_immeuble=True,
        immeuble_immatricule=True, immeuble_en_reserve_fonciere=True,
        acquereur_etranger=True, terre_agricole=True, cession_titres_immobiliers=True,
        taux_souscription=0.5, valeur_declaree=2, valeur_expertisee=1,
    )
    sarl = OperationJuridique(forme="SARL", liberation="mixte", dps_supprime=True)
    for a in analyser(op) + analyser(sarl):
        for ref in a.references:
            assert ref in REFERENCES, ref


def test_formes_invalides():
    with pytest.raises(ValueError):
        OperationJuridique(forme="SNC")
    with pytest.raises(ValueError):
        OperationJuridique(forme="SA", liberation="troc")
    with pytest.raises(ValueError):
        OperationJuridique(forme="SA", taux_souscription=1.5)


def test_rapport_texte():
    assert rapport_texte([]) == "Aucune alerte."
    texte = rapport_texte(analyser(sa_numeraire(delai_souscription_jours=5)))
    assert "[BLOQUANT] Délai" in texte and "Références" in texte


# --- Règles vérifiées dans l'édition officielle du CSC (IORT, 2022) et le document de la BVMT ---

def test_capital_non_libere_bloque_la_societe_anonyme():
    b = trouver(analyser(sa_numeraire(capital_libere=False)), "Capital", BLOQUANT)
    assert len(b) == 1 and "CSC art. 295" in b[0].references
    assert not trouver(analyser(sa_numeraire(capital_libere=True)), "Capital")


def test_capital_libere_ne_concerne_pas_la_sarl():
    op = OperationJuridique(forme="SARL", liberation="numeraire", age_tenue=True)
    assert not trouver(analyser(op), "Capital")


def test_liberation_du_quart_signalee_pour_la_sa_en_numeraire():
    info = trouver(analyser(sa_numeraire()), "Libération")
    assert len(info) == 1 and "CSC art. 294" in info[0].references
    assert "six mois" in info[0].message and "cinq ans" in info[0].message
    nature = OperationJuridique(forme="SA", liberation="nature", age_tenue=True)
    assert not trouver(analyser(nature), "Libération")


def test_sarl_sans_commissaire_rappelle_l_exception_des_trois_mille_dinars():
    op = OperationJuridique(forme="SARL", liberation="nature", age_tenue=True)
    b = trouver(analyser(op), "Apport en nature", BLOQUANT)
    assert len(b) == 1 and "3 000 dinars" in b[0].message and "CSC art. 100" in b[0].references


def test_commissaire_designe_sa_declenche_le_rappel_d_independance():
    op = OperationJuridique(forme="SA", liberation="nature", age_tenue=True, commissaire_apports=True)
    info = trouver(analyser(op), "Commissaire aux apports")
    assert len(info) == 1 and "CSC art. 174" in info[0].references


def test_incorporation_de_reserves_sarl_majorite_simple():
    op = OperationJuridique(forme="SARL", liberation="incorporation")
    b = trouver(analyser(op), "Décision", BLOQUANT)
    assert len(b) == 1 and "CSC art. 133" in b[0].references and "plus de la moitié" in b[0].message
    assert not trouver(analyser(op), "Délai")


def test_incorporation_de_reserves_sa_sans_delai_de_souscription():
    op = OperationJuridique(forme="SA", liberation="incorporation", age_tenue=True, capital_libere=True)
    alertes = analyser(op)
    assert not trouver(alertes, "Délai") and not trouver(alertes, "Publicité")
    assert trouver(alertes, "Incorporation de réserves")


def test_minoritaires_seuils_selon_l_appel_public_a_l_epargne():
    ferme = trouver(analyser(sa_numeraire()), "Minoritaires")[0]
    cote = trouver(analyser(sa_numeraire(appel_public_epargne=True)), "Minoritaires")[0]
    assert "5 %" in ferme.message and "CSC art. 290 ter" in ferme.references
    assert "3 %" in cote.message and "CSC art. 290 ter" not in cote.references
    assert "10 %" in ferme.message and "10 %" in cote.message


def test_societe_cotee_cite_le_document_de_la_bvmt():
    a = trouver(analyser(sa_numeraire(appel_public_epargne=True)), "Marché boursier")
    assert len(a) == 1 and "BVMT droits de souscription" in a[0].references
    assert not trouver(analyser(sa_numeraire()), "Marché boursier")


def test_les_articles_du_csc_sont_marques_officiels():
    csc = [k for k in REFERENCES if k.startswith("CSC art.")]
    assert csc and all(REFERENCES[k][1] == "officiel" for k in csc)
    assert REFERENCES["BVMT droits de souscription"][1] == "bvmt"


def test_seuil_de_l_article_290_est_de_dix_pour_cent():
    # L'ancienne version du module annonçait 20 % ou 10 %, ce que le texte de 2022 ne confirme pas.
    texte = REFERENCES["CSC art. 290"][0]
    assert "10 %" in texte and "20 %" not in texte
