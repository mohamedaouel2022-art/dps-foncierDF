"""Agent juridique conversationnel pour le DPS (droit tunisien).

L'agent s'appuie sur Claude (API Anthropic) et dispose de quatre outils qui appellent
les mêmes moteurs que le reste du projet :
- consulter_textes : lit les articles et textes de droit_tunisien.REFERENCES
- controler_dossier : exécute droit_tunisien.analyser
- calculer_droit_souscription : formules de la BVMT (dps_foncier)
- calculer_dilution_apport : perte des autres associés en cas d'apport surévalué

Sans clé API, reponse_locale() répond à partir de base_connaissances.json et des références.
"""

import json
import pathlib
import re
import unicodedata

from dps_foncier import (
    Operation,
    cours_action_nouvelle,
    dilution_apport_immeuble,
    simulation_associe,
    terp,
    valeur_droit,
    valeur_droit_periode,
)
from droit_tunisien import REFERENCES, OperationJuridique, analyser

MODELES = {
    "Claude Sonnet 5.5 (recommandé)": "claude-sonnet-5-5",
    "Claude Haiku 5.5 (rapide)": "claude-haiku-5-5",
}
MAX_TOURS = 6
NOM = "Law Guru"

ACCUEIL = (
    "Bonjour, je suis Law Guru. Je peux expliquer un article du Code des sociétés commerciales, clarifier une notion, "
    "faire un calcul de droit de souscription ou passer votre dossier en revue. Posez votre question ou choisissez un thème à gauche."
)
ACCUEIL_HORS_CONNEXION = (
    " Pour le moment je réponds à partir des textes lus : pour contrôler un dossier décrit en conversation, "
    "connectez moi avec une clé API."
)
GUIDE_DOSSIER = (
    "Pour passer votre dossier en revue, indiquez ce que vous savez parmi ces points. Une seule phrase suffit, "
    "les points inconnus peuvent rester vides.\n\n"
    "1. La forme de la société : SA, SARL ou SCI, cotée ou non.\n"
    "2. Le mode d'augmentation : numéraire, apport en nature, les deux, ou incorporation de réserves.\n"
    "3. L'état de la décision : assemblée tenue, capital existant libéré, DPS supprimé et rapports disponibles.\n"
    "4. La souscription : délai prévu, annonce au Journal officiel.\n"
    "5. L'apport en nature : commissaire aux apports, valeur déclarée et valeur expertisée.\n"
    "6. L'immeuble : immatriculé ou non, inscription au Livre Foncier prévue, réserve foncière, acquéreur étranger.\n\n"
    "Exemple : « SA non cotée, apport en nature d'un immeuble immatriculé de 5 000 000 DT expertisé à 3 500 000 DT, "
    "assemblée tenue, DPS supprimé, rapport du conseil seulement. »"
)

STATUTS = {
    "officiel": "édition officielle du CSC, IORT 2022",
    "bvmt": "document de la Bourse de Tunis, mars 2009",
    "lu": "texte lu en ligne, à confronter au Journal officiel",
    "secondaire": "source secondaire, à faire valider",
    "a verifier": "à vérifier",
}

SYSTEME = (
    "Tu es Law Guru, l'assistant juridique d'une plateforme qui aide à préparer une augmentation de capital avec droit "
    "préférentiel de souscription (DPS) en Tunisie. Tu réponds en français, de façon claire, structurée et courte. "
    "Si on te demande ton nom, tu t'appelles Law Guru.\n\n"
    "Ton rôle : expliquer les articles du Code des sociétés commerciales (CSC) et les notions juridiques et financières "
    "(DPS, souscription à titre irréductible et réductible, apport en nature, commissaire aux apports, libération du capital, "
    "droits des minoritaires, droit foncier lié à un apport d'immeuble), contrôler un dossier, et faire les calculs.\n\n"
    "Règles :\n"
    "1. Pour citer ou expliquer un article, appelle d'abord consulter_textes et appuie toi sur ce qu'il renvoie. "
    "Ne cite jamais un article, un seuil ou un délai qui ne vient pas des outils. Si les textes lus ne couvrent pas la question, "
    "dis le, puis donne si utile une explication générale en la présentant comme telle.\n"
    "2. Pour contrôler un dossier, appelle controler_dossier avec uniquement les faits donnés par l'utilisateur. "
    "Un fait non mentionné vaut faux par défaut et peut créer une fausse alerte : pose d'abord une question courte sur les "
    "faits essentiels qui manquent (forme, mode de libération, assemblée tenue, capital libéré, DPS supprimé et rapports, "
    "immeuble immatriculé), ou annonce clairement l'hypothèse retenue. Explique ensuite les alertes par ordre de gravité "
    "(BLOQUANT, ATTENTION, INFO) avec les références.\n"
    "3. Pour un calcul, appelle calculer_droit_souscription ou calculer_dilution_apport, jamais de tête. Donne les montants "
    "en dinars (DT), à trois décimales.\n"
    "4. Le délai de libération du quart (CSC art. 294) est ambigu : cinq ans dans le texte français imprimé, six mois selon "
    "la version arabe. Signale le quand il compte.\n"
    "5. Les textes lus sont l'édition 2022 du CSC : les lois postérieures ne sont pas prises en compte. Le droit foncier "
    "(CDR, CATU, CDET) vient de sites de documentation à confronter au Journal officiel.\n"
    "6. Tes réponses sont indicatives et ne remplacent pas l'avis d'un avocat ou d'un notaire tunisien. Dis le brièvement, "
    "sans le répéter à chaque message.\n"
    "7. Style : phrases simples, pas de tirets pour relier les phrases, pas de formules toutes faites ni de formules "
    "d'enthousiasme. Utilise des listes numérotées seulement quand il y a des étapes ou des points à traiter.\n\n"
    "Références disponibles dans consulter_textes : " + ", ".join(REFERENCES) + "."
)

TOOLS = [
    {
        "name": "consulter_textes",
        "description": (
            "Cherche dans les textes juridiques lus (CSC édition 2022, document BVMT, CDR, CATU, CDET) par numéro d'article "
            "(par exemple 301, 290 bis, 'CSC art. 306') ou par mots clés (par exemple 'délai souscription', 'commissaire aux apports'). "
            "Renvoie le texte résumé de chaque référence trouvée et son statut de lecture."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"requete": {"type": "string", "description": "Numéro d'article ou mots clés."}},
            "required": ["requete"],
        },
    },
    {
        "name": "controler_dossier",
        "description": (
            "Contrôle une augmentation de capital au regard du droit tunisien et renvoie les alertes classées BLOQUANT, ATTENTION, INFO "
            "avec les références. Renseigner uniquement les faits connus : tout champ omis prend sa valeur par défaut (faux ou inconnu)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "forme": {"type": "string", "enum": ["SA", "SARL", "SCI"]},
                "liberation": {"type": "string", "enum": ["numeraire", "nature", "mixte", "incorporation"]},
                "age_tenue": {"type": "boolean", "description": "Décision de l'assemblée extraordinaire prise."},
                "capital_libere": {"type": "boolean", "description": "Capital existant intégralement libéré (SA)."},
                "appel_public_epargne": {"type": "boolean", "description": "Société cotée ou faisant appel public à l'épargne."},
                "publication_jort": {"type": "boolean", "description": "Modalités du DPS annoncées au Journal officiel (SA)."},
                "delai_souscription_jours": {"type": "integer", "description": "Délai de souscription en jours."},
                "dps_supprime": {"type": "boolean"},
                "rapport_conseil": {"type": "boolean"},
                "rapport_cac": {"type": "boolean", "description": "Rapport des commissaires aux comptes."},
                "taux_souscription": {"type": "number", "description": "Part souscrite à la clôture, entre 0 et 1."},
                "limitation_prevue": {"type": "boolean"},
                "commissaire_apports": {"type": "boolean"},
                "evaluation_approuvee": {"type": "boolean"},
                "evaluation_reduite_par_age": {"type": "boolean", "description": "L'assemblée a réduit l'évaluation de l'apport."},
                "accord_apporteur": {"type": "boolean"},
                "valeur_declaree": {"type": "number", "description": "Valeur déclarée de l'apport en DT."},
                "valeur_expertisee": {"type": "number", "description": "Valeur expertisée en DT."},
                "apport_immeuble": {"type": "boolean"},
                "immeuble_immatricule": {"type": "boolean", "description": "Omettre si inconnu."},
                "acte_forme_legale": {"type": "boolean"},
                "inscription_livre_foncier_prevue": {"type": "boolean"},
                "immeuble_en_reserve_fonciere": {"type": "boolean"},
                "droit_priorite_purge": {"type": "boolean", "description": "Bénéficiaire du droit de priorité notifié."},
                "acquereur_etranger": {"type": "boolean"},
                "autorisation_gouverneur": {"type": "boolean"},
                "terre_agricole": {"type": "boolean"},
                "cession_titres_immobiliers": {"type": "boolean"},
            },
            "required": ["forme"],
        },
    },
    {
        "name": "calculer_droit_souscription",
        "description": (
            "Calcule la valeur théorique du droit de souscription et le cours de référence après détachement (formules BVMT). "
            "Si actions_detenues est donné, compare exercer, vendre ou laisser expirer. "
            "Si cours_ligne est donné, calcule aussi le droit pendant la période et le cours de l'action nouvelle non assimilée."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "actions_anciennes": {"type": "integer", "description": "A : nombre d'actions avant l'opération."},
                "cours_cum": {"type": "number", "description": "C : cours de clôture la veille, en DT."},
                "prix_souscription": {"type": "number", "description": "PE : prix d'émission, en DT."},
                "parite_nouvelles": {"type": "integer", "description": "Actions nouvelles offertes (p)."},
                "parite_anciennes": {"type": "integer", "description": "Pour q actions anciennes détenues."},
                "difference_jouissance": {"type": "number", "description": "D en DT, 0 par défaut."},
                "actions_detenues": {"type": "integer"},
                "prix_droit_marche": {"type": "number", "description": "Prix du droit coté, sinon valeur théorique."},
                "cours_ligne": {"type": "number", "description": "Cours de la ligne principale pendant la période."},
            },
            "required": ["actions_anciennes", "cours_cum", "prix_souscription", "parite_nouvelles", "parite_anciennes"],
        },
    },
    {
        "name": "calculer_dilution_apport",
        "description": "Chiffre la perte des autres associés quand un immeuble est apporté pour une valeur déclarée supérieure à sa valeur réelle (DPS supprimé).",
        "input_schema": {
            "type": "object",
            "properties": {
                "actions_anciennes": {"type": "integer"},
                "cours": {"type": "number", "description": "Cours de l'action en DT."},
                "prix_emission": {"type": "number", "description": "Prix d'émission en DT."},
                "valeur_declaree": {"type": "number"},
                "valeur_reelle": {"type": "number"},
            },
            "required": ["actions_anciennes", "cours", "prix_emission", "valeur_declaree", "valeur_reelle"],
        },
    },
]


def _norm(s):
    s = unicodedata.normalize("NFD", s.lower().replace("’", "'"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def consulter_textes(requete, limite=5):
    q = _norm(requete)
    nombres = re.findall(r"\d+", q)
    suffixes = [s for s in ("bis", "ter") if re.search(rf"\b{s}\b", q)]
    mots = [m for m in re.findall(r"[a-z0-9']+", q) if len(m) > 3]
    trouves = []
    for nom, (texte, statut) in REFERENCES.items():
        n, t = _norm(nom), _norm(texte)
        score = 0
        for num in nombres:
            if re.search(rf"\b{num}\b", n):
                score += 10
        if score and suffixes:
            score += 5 if any(s in n for s in suffixes) else -4
        score += sum(1 for m in mots if m in n) * 3 + sum(1 for m in mots if m in t)
        if score > 0:
            trouves.append((score, nom, texte, statut))
    trouves.sort(key=lambda x: -x[0])
    return [
        {"reference": nom, "texte": texte, "statut": STATUTS[statut]}
        for _, nom, texte, statut in trouves[:limite]
    ]


def controler_dossier(**faits):
    champs = set(OperationJuridique.__dataclass_fields__)
    inconnus = sorted(set(faits) - champs)
    op = OperationJuridique(**{k: v for k, v in faits.items() if k in champs})
    alertes = analyser(op)
    return {
        "champs_ignores": inconnus,
        "alertes": [
            {"gravite": a.gravite, "theme": a.theme, "message": a.message, "references": list(a.references)}
            for a in alertes
        ],
    }


def calculer_droit(actions_anciennes, cours_cum, prix_souscription, parite_nouvelles, parite_anciennes,
                   difference_jouissance=0.0, actions_detenues=None, prix_droit_marche=None, cours_ligne=None):
    op = Operation(actions_anciennes, cours_cum, prix_souscription, parite_nouvelles, parite_anciennes, difference_jouissance)
    sortie = {"valeur_droit_au_detachement": round(valeur_droit(op), 4), "cours_reference_apres_detachement": round(terp(op), 4)}
    if cours_ligne:
        sortie["valeur_droit_pendant_la_periode"] = round(valeur_droit_periode(op, cours_ligne), 4)
        sortie["action_nouvelle_non_assimilee"] = round(cours_action_nouvelle(cours_ligne, difference_jouissance), 4)
    if actions_detenues:
        sortie["simulation_associe"] = simulation_associe(op, actions_detenues, prix_droit_marche)
    return sortie


def executer(nom, args):
    """Exécute un outil et renvoie un texte JSON. Les erreurs sont renvoyées à l'agent, pas levées."""
    try:
        if nom == "consulter_textes":
            res = consulter_textes(args.get("requete", ""))
            res = res or "Aucune référence trouvée dans les textes lus."
        elif nom == "controler_dossier":
            res = controler_dossier(**args)
        elif nom == "calculer_droit_souscription":
            res = calculer_droit(**args)
        elif nom == "calculer_dilution_apport":
            res = dilution_apport_immeuble(**args)
        else:
            res = f"Outil inconnu : {nom}"
    except (ValueError, TypeError) as e:
        res = {"erreur": str(e)}
    return json.dumps(res, ensure_ascii=False)


def libelle_outil(nom, args):
    if nom == "consulter_textes":
        return "Lecture des textes : " + str(args.get("requete", ""))
    if nom == "controler_dossier":
        return "Contrôle du dossier"
    if nom == "calculer_droit_souscription":
        return "Calcul du droit de souscription"
    if nom == "calculer_dilution_apport":
        return "Calcul de la dilution de l'apport"
    return nom


def repondre(client, modele, historique):
    """Boucle d'agent : appelle le modèle, exécute les outils demandés, renvoie (texte, outils utilisés).

    historique : liste de {"role": "user" | "assistant", "content": str}.
    """
    messages = [{"role": m["role"], "content": m["content"]} for m in historique]
    outils = []
    for _ in range(MAX_TOURS):
        rep = client.messages.create(model=modele, max_tokens=2000, system=SYSTEME, tools=TOOLS, messages=messages)
        if rep.stop_reason != "tool_use":
            texte = "".join(b.text for b in rep.content if b.type == "text").strip()
            return texte or "Je n'ai pas de réponse à afficher.", outils
        messages.append({"role": "assistant", "content": rep.content})
        resultats = []
        for bloc in rep.content:
            if bloc.type == "tool_use":
                outils.append(libelle_outil(bloc.name, bloc.input))
                resultats.append({"type": "tool_result", "tool_use_id": bloc.id, "content": executer(bloc.name, bloc.input)})
        messages.append({"role": "user", "content": resultats})
    return "La recherche a pris trop d'étapes. Reformulez la question en la précisant.", outils


# ---------------------------------------------------------------- Mode hors connexion

_KB_PATH = pathlib.Path(__file__).resolve().parent / "base_connaissances.json"
try:
    KB = json.loads(_KB_PATH.read_text(encoding="utf-8"))
except (OSError, ValueError):
    KB = []

FALLBACK = (
    "Je n'ai pas trouvé de réponse précise dans les textes lus. Précisez le sujet : droit préférentiel de souscription, "
    "suppression, délai, publicité, capital libéré, apport en nature, immeuble, minoritaires, SARL, SCI, valeur du droit "
    "ou fiscalité. Hors de ces sujets, consultez un avocat ou un notaire tunisien."
)
MESSAGE_DOSSIER = (
    "Pour contrôler un dossier en conversation, connectez l'agent avec une clé API : il lit votre description, "
    "lance le contrôle et explique chaque alerte. Hors connexion, je peux expliquer les articles et les notions."
)


def _mot_present(q, mot):
    if len(mot) <= 4:
        return re.search(r"(^|[^a-z0-9])" + re.escape(mot) + r"([^a-z0-9]|$)", q) is not None
    return mot in q


def reponse_locale(question):
    """Réponse hors connexion : (texte markdown, liste de références)."""
    q = _norm(question)
    notes = []
    for sujet in KB:
        score = sum(len(_norm(m)) for m in sujet["mots"] if _mot_present(q, _norm(m)))
        if score:
            notes.append((score, sujet))
    notes.sort(key=lambda x: -x[0])
    retenus = [s for i, (sc, s) in enumerate(notes) if i == 0 or (i == 1 and sc >= 0.6 * notes[0][0])]
    paragraphes, refs = [], []
    for sujet in retenus:
        if sujet["id"] == "dossier":
            paragraphes.append(MESSAGE_DOSSIER)
            continue
        paragraphes.extend(sujet["texte"])
        refs.extend(r for r in sujet["refs"] if r not in refs)
    if not paragraphes:
        trouves = consulter_textes(question, limite=3)
        if trouves:
            paragraphes = [f"**{t['reference']}** ({t['statut']}) : {t['texte']}" for t in trouves]
        else:
            paragraphes = [FALLBACK]
    texte = "\n\n".join(paragraphes)
    if refs:
        texte += "\n\n**Références** : " + ", ".join(refs)
    return texte, refs
