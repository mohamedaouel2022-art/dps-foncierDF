"""Vérifie que web/index.html donne les mêmes résultats que le moteur Python.

Compare sur des cas fixes (droit de souscription, apport d'immeuble) et sur
600 dossiers juridiques tirés au hasard.
Demande Node.js. Usage : python3 web/verifier_parite.py
"""
import json
import pathlib
import random
import re
import subprocess
import sys
import tempfile

RACINE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from dps_foncier import (  # noqa: E402
    Operation,
    cours_action_nouvelle,
    dilution_apport_immeuble,
    simulation_associe,
    valeur_droit_periode,
)
from droit_tunisien import OperationJuridique, analyser  # noqa: E402

html = (RACINE / "web" / "index.html").read_text(encoding="utf-8")
moteur = re.search(r'<script id="moteur">(.*?)</script>', html, re.S).group(1)

random.seed(2026)

finance = [
    dict(N=1_000_000, P=20.0, S=15.0, p=1, q=4, det=10_000, marche=None),
    dict(N=1_000_000, P=8.0, S=6.5, p=1, q=2, det=10_000, marche=None, D=0.35, ligne=8.03),
    dict(N=2_000_000, P=6.6, S=3.5, p=7, q=30, det=3_000, marche=0.45, D=0.17, ligne=6.9),
    dict(N=1_000_000, P=20.0, S=15.0, p=1, q=4, det=10_000, marche=1.2),
    dict(N=1_000_000, P=20.0, S=15.0, p=1, q=4, det=10_000, marche=0.8),
    dict(N=500_000, P=12.5, S=9.0, p=3, q=7, det=1_234, marche=None),
    dict(N=2_000_000, P=8.0, S=6.5, p=2, q=5, det=50_000, marche=0.9),
]
apport = [
    (1_000_000, 20.0, 20.0, 5_000_000, 3_500_000),
    (1_000_000, 20.0, 20.0, 5_000_000, 5_000_000),
    (750_000, 14.2, 13.0, 2_100_000, 2_600_000),
]


def operation_aleatoire():
    return dict(
        forme=random.choice(["SA", "SARL", "SCI"]),
        liberation=random.choice(["numeraire", "nature", "mixte", "incorporation"]),
        capital_libere=random.random() < 0.6,
        appel_public_epargne=random.random() < 0.4,
        age_tenue=random.random() < 0.6,
        publication_jort=random.random() < 0.6,
        delai_souscription_jours=random.choice([None, 5, 14, 15, 20, 21, 30]),
        dps_supprime=random.random() < 0.5,
        rapport_conseil=random.random() < 0.5,
        rapport_cac=random.random() < 0.5,
        taux_souscription=random.choice([None, 0.5, 0.75, 0.8, 0.96, 1.0]),
        limitation_prevue=random.random() < 0.5,
        commissaire_apports=random.random() < 0.5,
        evaluation_approuvee=random.random() < 0.5,
        evaluation_reduite_par_age=random.random() < 0.3,
        accord_apporteur=random.random() < 0.5,
        valeur_declaree=random.choice([None, 1e6, 3.6e6, 5e6]),
        valeur_expertisee=random.choice([None, 1e6, 3.5e6, 5e6]),
        apport_immeuble=random.random() < 0.6,
        immeuble_immatricule=random.choice([None, True, False]),
        acte_forme_legale=random.random() < 0.5,
        inscription_livre_foncier_prevue=random.random() < 0.5,
        immeuble_en_reserve_fonciere=random.random() < 0.4,
        droit_priorite_purge=random.random() < 0.5,
        acquereur_etranger=random.random() < 0.4,
        autorisation_gouverneur=random.random() < 0.5,
        terre_agricole=random.random() < 0.4,
        cession_titres_immobiliers=random.random() < 0.4,
    )


juridique = [operation_aleatoire() for _ in range(600)]

attendu = {"finance": [], "periode": [], "apport": [], "juridique": []}
for c in finance:
    op = Operation(c["N"], c["P"], c["S"], c["p"], c["q"], c.get("D", 0.0))
    attendu["finance"].append(simulation_associe(op, c["det"], c["marche"]))
    if c.get("ligne"):
        attendu["periode"].append(dict(
            droit=valeur_droit_periode(op, c["ligne"]),
            action=cours_action_nouvelle(c["ligne"], c.get("D", 0.0)),
        ))
for a in apport:
    attendu["apport"].append(dilution_apport_immeuble(*a))
for kw in juridique:
    attendu["juridique"].append([
        dict(gravite=x.gravite, theme=x.theme, message=x.message, references=list(x.references))
        for x in analyser(OperationJuridique(**kw))
    ])

with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    (tmp / "moteur.js").write_text(moteur, encoding="utf-8")
    (tmp / "cas.json").write_text(json.dumps(dict(finance=finance, apport=apport, juridique=juridique)), encoding="utf-8")
    (tmp / "run.js").write_text("""
const m = require('./moteur.js');
const c = require('./cas.json');
const sortie = {
  finance: c.finance.map(x => m.simulationAssocie({actions_anciennes:x.N, cours_cum:x.P, prix_souscription:x.S, parite_nouvelles:x.p, parite_anciennes:x.q, difference_jouissance:x.D || 0}, x.det, x.marche)),
  periode: c.finance.filter(x => x.ligne).map(x => {
    const op = {actions_anciennes:x.N, cours_cum:x.P, prix_souscription:x.S, parite_nouvelles:x.p, parite_anciennes:x.q, difference_jouissance:x.D || 0};
    return {droit: m.valeurDroitPeriode(op, x.ligne), action: m.coursActionNouvelle(x.ligne, x.D || 0)};
  }),
  apport: c.apport.map(a => m.dilutionApport(...a)),
  juridique: c.juridique.map(op => m.analyser(op)),
};
console.log(JSON.stringify(sortie));
""", encoding="utf-8")
    res = subprocess.run(["node", "run.js"], cwd=tmp, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(1)
    obtenu = json.loads(res.stdout)


def proche(a, b):
    if isinstance(a, dict):
        return all(k in b and proche(a[k], b[k]) for k in a)
    return abs(a - b) < 1e-6


erreurs = 0
for i, (a, b) in enumerate(zip(attendu["finance"], obtenu["finance"])):
    if not proche(a, b):
        erreurs += 1
        print("finance", i, a, b)
for i, (a, b) in enumerate(zip(attendu["periode"], obtenu["periode"])):
    if not proche(a, b):
        erreurs += 1
        print("periode", i, a, b)
for i, (a, b) in enumerate(zip(attendu["apport"], obtenu["apport"])):
    if not proche(a, b):
        erreurs += 1
        print("apport", i, a, b)
for i, (a, b) in enumerate(zip(attendu["juridique"], obtenu["juridique"])):
    if a != b:
        erreurs += 1
        if erreurs < 4:
            print("juridique", i, juridique[i])
            print(" python", a)
            print(" js    ", b)

total = len(finance) + len(attendu["periode"]) + len(apport) + len(juridique)
print(f"{total - erreurs}/{total} cas identiques entre Python et la page web")
sys.exit(1 if erreurs else 0)
