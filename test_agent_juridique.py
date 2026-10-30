"""Tests de l'agent juridique : outils, boucle d'agent (avec un faux client) et mode hors connexion."""

import json
from types import SimpleNamespace

import agent_juridique as ag


def test_consulter_textes_par_numero_d_article():
    res = ag.consulter_textes("article 301")
    assert res[0]["reference"] == "CSC art. 301"
    assert "quinze jours" in res[0]["texte"]


def test_consulter_textes_distingue_bis_et_ter():
    assert ag.consulter_textes("290 ter")[0]["reference"] == "CSC art. 290 ter"
    assert ag.consulter_textes("290 bis")[0]["reference"] == "CSC art. 290 bis"


def test_consulter_textes_par_mots_cles():
    refs = [r["reference"] for r in ag.consulter_textes("commissaire aux apports")]
    assert "CSC art. 306" in refs or "CSC art. 173" in refs


def test_controler_dossier_renvoie_les_alertes_tries():
    res = json.loads(ag.executer("controler_dossier", {"forme": "SA", "liberation": "numeraire", "delai_souscription_jours": 10}))
    graves = [a["gravite"] for a in res["alertes"]]
    assert graves == sorted(graves, key=["BLOQUANT", "ATTENTION", "INFO"].index)
    assert any(a["theme"] == "Délai" and a["gravite"] == "BLOQUANT" for a in res["alertes"])


def test_controler_dossier_ignore_les_champs_inconnus():
    res = json.loads(ag.executer("controler_dossier", {"forme": "SA", "champ_invente": 1}))
    assert res["champs_ignores"] == ["champ_invente"]


def test_controler_dossier_forme_invalide_renvoie_une_erreur():
    res = json.loads(ag.executer("controler_dossier", {"forme": "SNC"}))
    assert "erreur" in res


def test_calcul_droit_exemple_bvmt():
    res = json.loads(ag.executer("calculer_droit_souscription", dict(
        actions_anciennes=1_000_000, cours_cum=8.0, prix_souscription=6.5,
        parite_nouvelles=1, parite_anciennes=2, difference_jouissance=0.35, cours_ligne=8.03, actions_detenues=10_000)))
    assert abs(res["valeur_droit_au_detachement"] - 0.3833) < 1e-4
    assert abs(res["valeur_droit_pendant_la_periode"] - 0.59) < 1e-4
    assert abs(res["action_nouvelle_non_assimilee"] - 7.68) < 1e-4
    assert abs(res["simulation_associe"]["expirer"]["gain_ou_perte"] + 3833.333) < 0.01


def test_calcul_dilution_apport():
    res = json.loads(ag.executer("calculer_dilution_apport", dict(
        actions_anciennes=1_000_000, cours=20.0, prix_emission=20.0, valeur_declaree=5_000_000, valeur_reelle=3_500_000)))
    assert res["perte_totale_autres_associes"] == 1_200_000


def test_outil_inconnu_et_arguments_invalides():
    assert "inconnu" in ag.executer("nimporte", {})
    assert "erreur" in ag.executer("calculer_dilution_apport", {"actions_anciennes": 0, "cours": 1, "prix_emission": 1, "valeur_declaree": 1, "valeur_reelle": 1})
    assert "erreur" in ag.executer("calculer_dilution_apport", {"mauvais": 1})


class FauxClient:
    """Premier appel : demande un outil. Second appel : texte final."""

    def __init__(self):
        self.appels = []
        self.messages = self

    def create(self, **kw):
        self.appels.append(kw)
        if len(self.appels) == 1:
            bloc = SimpleNamespace(type="tool_use", id="t1", name="consulter_textes", input={"requete": "301"})
            return SimpleNamespace(stop_reason="tool_use", content=[bloc])
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Quinze jours au minimum (CSC art. 301).")])


def test_boucle_d_agent_execute_l_outil_puis_repond():
    client = FauxClient()
    texte, outils = ag.repondre(client, "claude-sonnet-5-5", [{"role": "user", "content": "Quel délai pour une SA ?"}])
    assert "301" in texte and outils == ["Lecture des textes : 301"]
    assert len(client.appels) == 2
    retour = client.appels[1]["messages"][-1]["content"][0]
    assert retour["type"] == "tool_result" and "quinze jours" in retour["content"]
    assert client.appels[0]["tools"] == ag.TOOLS and client.appels[0]["model"] == "claude-sonnet-5-5"


def test_boucle_d_agent_s_arrete_apres_le_maximum_de_tours():
    class Boucle(FauxClient):
        def create(self, **kw):
            bloc = SimpleNamespace(type="tool_use", id="t", name="consulter_textes", input={"requete": "301"})
            return SimpleNamespace(stop_reason="tool_use", content=[bloc])

    texte, outils = ag.repondre(Boucle(), "m", [{"role": "user", "content": "x"}])
    assert "trop d'étapes" in texte and len(outils) == ag.MAX_TOURS


def test_reponse_locale_explique_un_sujet():
    texte, refs = ag.reponse_locale("Quel délai pour souscrire ?")
    assert "quinze jours" in texte and "CSC art. 301" in refs


def test_reponse_locale_dossier_renvoie_vers_l_agent():
    texte, _ = ag.reponse_locale("Que faut-il corriger dans mon dossier ?")
    assert "clé API" in texte


def test_reponse_locale_sujet_inconnu():
    texte, _ = ag.reponse_locale("zzzz qqqq")
    assert texte == ag.FALLBACK


def test_l_agent_s_appelle_law_guru():
    assert ag.NOM == "Law Guru" and "Law Guru" in ag.SYSTEME and "Law Guru" in ag.ACCUEIL
