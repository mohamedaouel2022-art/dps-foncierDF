# DPS Foncier

Moteur de calcul du droit préférentiel de souscription, contrôle juridique et assistant juridique, pour les sociétés à objet foncier en Tunisie : foncières, promoteurs, fonds immobiliers.

Il répond à trois questions que se pose un associé ou un juriste lors d'une augmentation de capital.

1. Que vaut mon droit, et vaut-il mieux exercer, vendre ou laisser expirer ?
2. Si le droit préférentiel de souscription (DPS) est supprimé au profit d'un apporteur d'immeuble, combien perdent les autres associés quand l'immeuble est surévalué ?
3. Le dossier respecte-t-il le Code des sociétés commerciales (CSC) et le droit foncier ?

Les montants sont en dinars tunisiens (DT), à trois décimales.

## Installation

```bash
git clone <url-du-depot>
cd dps-foncier
pip install pytest
pytest
```

Python 3.10 ou plus récent.

## Utilisation

```python
from dps_foncier import (
    Operation, valeur_droit, terp, valeur_droit_periode, cours_action_nouvelle,
    simulation_associe, dilution_apport_immeuble,
)

# Exemple n°1 du document de la Bourse de Tunis (BVMT) : El Wifack Leasing.
# 1 action nouvelle pour 2 anciennes à 6,500 DT, cours de clôture 8,000 DT,
# différence de jouissance en dividende 0,350 DT.
op = Operation(
    actions_anciennes=1_000_000,
    cours_cum=8.0,
    prix_souscription=6.5,
    parite_nouvelles=1,
    parite_anciennes=2,
    difference_jouissance=0.35,
)

valeur_droit(op)                    # 0.3833 : cours théorique du droit au détachement
terp(op)                            # 7.6167 : cours de référence de l'action après détachement
valeur_droit_periode(op, 8.03)      # 0.59   : cours de référence du droit un jour de la période
cours_action_nouvelle(8.03, 0.35)   # 7.68   : action nouvelle souscrite, non encore assimilée

# Associé qui détient 10 000 actions, avec un droit coté 0,450 sur le marché
simulation_associe(op, actions_detenues=10_000, prix_droit_marche=0.45)

# Apport d'un immeuble déclaré 5 000 000 DT pour une valeur réelle de 3 500 000 DT
dilution_apport_immeuble(1_000_000, 20.0, 20.0, 5_000_000, 3_500_000)
```

## Formules

Elles reprennent le document de la BVMT sur les droits de souscription (mise à jour mars 2009). A est le nombre d'actions anciennes, N le nombre d'actions nouvelles, C le cours, PE le prix d'émission et D la différence de jouissance en dividende entre actions nouvelles et anciennes.

1. Droit de souscription au détachement : Ds = N / (A + N) x (C - PE - D), avec C le cours de clôture de la veille.
2. Droit de souscription pendant la période : Ds = N / A x (C - D - PE), avec C le cours de référence de la ligne principale.
3. Action nouvelle non assimilée : NS = C - D.
4. Apport en nature : les actions émises à l'apporteur valent valeur déclarée / prix d'émission. La valeur par action après opération est (capitalisation avant + valeur réelle de l'immeuble) / (actions anciennes + actions émises). La perte des autres associés est la différence avec le cours initial.

Le test de l'exemple n°1 du document (El Wifack Leasing) donne 0,3833 avec la formule, alors que le document affiche 0,390 : le moteur applique la formule, sans arrondi à la centaine de millimes.

## Résultats sur l'exemple n°1

Pour l'associé à 10 000 actions, avec le droit valorisé à sa valeur théorique :

| Choix | Participation finale | Gain ou perte |
| --- | --- | --- |
| Exercer | 1,00 % | 0 |
| Vendre les droits | 0,67 % | 0 |
| Laisser expirer | 0,67 % | moins 3 833,333 DT |

Pour l'apport d'immeuble surévalué de 1 500 000 DT, les autres associés perdent 1,200 DT par action, soit 1 200 000 DT au total, et l'apporteur détient 20 % du capital.

## Page web

`web/index.html` est une page autonome : double clic dessus, elle s'ouvre dans le navigateur sans rien installer. Elle reprend la charte visuelle de la plateforme Credit Risk (thème Classic Bank, mode sombre inclus) et propose quatre onglets.

1. Droit de souscription : cours théorique, cours de référence pendant la période, comparaison exercer, vendre ou laisser expirer.
2. Apport d'immeuble : actions émises à l'apporteur, perte des autres associés quand l'immeuble est surévalué.
3. Contrôle juridique : formulaire du dossier et alertes classées avec les articles, qui se déplient avec leur statut de lecture.
4. Assistant juridique : questions fréquentes et zone de saisie. Il répond hors connexion à partir des textes lus (23 sujets, avec les articles cités) et sait résumer les alertes de votre dossier. Facultatif : avec une clé API Anthropic collée dans l'onglet, il interroge Claude (modèle `claude-haiku-5-5`) avec les mêmes références et votre dossier, et revient aux réponses locales si l'API échoue. La clé reste en mémoire dans l'onglet et n'est envoyée qu'à api.anthropic.com. Le mode API n'a été testé qu'avec une réponse simulée.

Les formules et les règles sont les mêmes que dans les modules Python. Pour le vérifier (Node.js requis) :

```bash
python3 web/verifier_parite.py
```

Le script compare 612 cas entre Python et la page.

## Interface Streamlit

`streamlit_app.py` propose trois onglets : droit de souscription, apport d'immeuble et Law Guru.

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

L'onglet Law Guru est un agent conversationnel (`agent_juridique.py`). Avec une clé API Anthropic collée dans l'onglet (ou définie dans la variable `ANTHROPIC_API_KEY`), il comprend les messages libres, lit les articles, explique les notions, contrôle un dossier décrit en conversation et fait les calculs, avec les mêmes moteurs que le reste du projet. Sans clé, il répond hors connexion à partir de `base_connaissances.json`. Le mode avec clé n'a été testé qu'avec un faux client, pas avec l'API réelle.

## Module juridique (droit tunisien)

`droit_tunisien.py` contrôle une opération au regard du CSC (édition officielle de l'Imprimerie officielle, mise à jour du 10 février 2022), du document de la BVMT, du Code des droits réels, du CATU et du CDET. Il renvoie des alertes classées BLOQUANT, ATTENTION ou INFO, avec les articles concernés.

```python
from droit_tunisien import OperationJuridique, analyser, rapport_texte

dossier = OperationJuridique(
    forme="SA",
    liberation="nature",        # numeraire, nature, mixte ou incorporation
    age_tenue=True,
    capital_libere=True,        # CSC art. 295 : capital existant intégralement libéré
    dps_supprime=True,
    rapport_conseil=True,
    rapport_cac=False,          # manquant : alerte BLOQUANT (CSC art. 300)
    commissaire_apports=True,
    evaluation_approuvee=True,
    valeur_declaree=5_000_000,
    valeur_expertisee=3_500_000,  # écart de 43 % : alerte ATTENTION
    apport_immeuble=True,
    immeuble_immatricule=True,
    acte_forme_legale=True,
    inscription_livre_foncier_prevue=False,  # BLOQUANT (CDR art. 305)
)
print(rapport_texte(analyser(dossier)))
```

Le détail des textes, les recommandations et les points à faire valider sont dans `docs/RECOMMANDATIONS_JURIDIQUES.md`.

## Limites de cette version

1. Les frais de courtage et la fiscalité ne sont pas encore intégrés.
2. Un droit est supposé égal à une action ancienne, et les parités ne sont pas arrondies à un nombre entier d'actions.
3. La souscription à titre réductible n'est pas modélisée.
4. Les formalités auprès du Conseil du marché financier pour les sociétés cotées ne sont pas contrôlées.
5. Les lois postérieures à l'édition 2022 du CSC ne sont pas prises en compte.
6. Le moteur calcule, il ne remplace pas l'avis d'un juriste.

## Feuille de route

1. Souscription à titre irréductible et réductible
2. Frais et fiscalité
3. Calendrier et notifications horodatées
4. Registre des droits et cessions entre associés
5. API

## Licence

MIT
