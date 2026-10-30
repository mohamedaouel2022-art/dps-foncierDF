"""DPS Foncier : moteur de calcul du droit préférentiel de souscription (marché tunisien).

Les formules suivent le document de la Bourse des Valeurs Mobilières de Tunis
sur les droits de souscription (mise à jour mars 2009). Les montants
sont en dinars tunisiens (DT), à trois décimales.

Fonctions principales :
- parite_nouvelles_actions : nombre d'actions nouvelles émises
- valeur_droit : cours théorique du droit de souscription le jour du détachement
- terp : cours de référence de l'action après détachement
- valeur_droit_periode : cours de référence du droit pendant la période de souscription
- cours_action_nouvelle : cours de référence d'une action nouvelle non assimilée
- simulation_associe : exercer, vendre ou laisser expirer
- dilution_apport_immeuble : cas où le DPS est supprimé au profit d'un apporteur
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Operation:
    """Termes d'une augmentation de capital en numéraire avec droit de souscription."""

    actions_anciennes: int      # A : nombre d'actions avant l'opération
    cours_cum: float            # C : cours de clôture la veille de la date d'effet
    prix_souscription: float    # PE : prix d'émission des actions nouvelles
    parite_nouvelles: int       # p : actions nouvelles offertes
    parite_anciennes: int       # q : pour q actions anciennes détenues
    difference_jouissance: float = 0.0  # D : dividende que les actions nouvelles ne touchent pas

    def __post_init__(self):
        if self.actions_anciennes <= 0:
            raise ValueError("Le nombre d'actions anciennes doit être positif.")
        if self.parite_nouvelles <= 0 or self.parite_anciennes <= 0:
            raise ValueError("La parité doit être strictement positive.")
        if self.prix_souscription <= 0 or self.cours_cum <= 0:
            raise ValueError("Les prix doivent être strictement positifs.")
        if self.difference_jouissance < 0:
            raise ValueError("La différence de jouissance ne peut pas être négative.")


def parite_nouvelles_actions(op: Operation) -> float:
    """Nombre total d'actions nouvelles si tous les droits sont exercés."""
    return op.actions_anciennes * op.parite_nouvelles / op.parite_anciennes


def valeur_droit(op: Operation) -> float:
    """Cours théorique du droit de souscription le jour du détachement (BVMT 1.1).

    Ds = N / (A + N) x (C - PE - D)
    """
    n = parite_nouvelles_actions(op)
    return n / (op.actions_anciennes + n) * (op.cours_cum - op.prix_souscription - op.difference_jouissance)


def terp(op: Operation) -> float:
    """Cours de référence de l'action après détachement : C moins le cours théorique du droit."""
    return op.cours_cum - valeur_droit(op)


def valeur_droit_periode(op: Operation, cours_ligne: float) -> float:
    """Cours de référence du droit pendant la période de souscription (BVMT 1.2).

    Ds = N / A x (C - D - PE), où C est le cours de référence de la ligne principale ce jour-là
    et N / A la parité de l'opération.
    """
    if cours_ligne <= 0:
        raise ValueError("Le cours de la ligne principale doit être strictement positif.")
    return op.parite_nouvelles / op.parite_anciennes * (cours_ligne - op.difference_jouissance - op.prix_souscription)


def cours_action_nouvelle(cours_ligne: float, difference_jouissance: float = 0.0) -> float:
    """Cours de référence d'une action nouvelle non encore assimilée : NS = C - D (BVMT 1.3)."""
    return cours_ligne - difference_jouissance


def simulation_associe(op: Operation, actions_detenues: int, prix_droit_marche: float | None = None) -> dict:
    """Compare les trois choix d'un associé : exercer, vendre, laisser expirer.

    Les droits sont supposés au nombre d'une action ancienne = un droit.
    Une action nouvelle souscrite vaut le cours de référence moins D tant qu'elle n'est pas assimilée.
    Frais et fiscalité ne sont pas inclus dans cette version.
    """
    if actions_detenues <= 0 or actions_detenues > op.actions_anciennes:
        raise ValueError("Nombre d'actions détenues invalide.")

    n_total = parite_nouvelles_actions(op)
    v_droit = valeur_droit(op)
    cours_ex = op.cours_cum - v_droit
    prix_droit = v_droit if prix_droit_marche is None else prix_droit_marche

    # Valeur de départ du portefeuille de l'associé
    valeur_initiale = actions_detenues * op.cours_cum

    # 1. Exercer : souscrire toutes les actions nouvelles auxquelles il a droit
    nouvelles = actions_detenues * op.parite_nouvelles / op.parite_anciennes
    cout_souscription = nouvelles * op.prix_souscription
    valeur_exercer = actions_detenues * cours_ex + nouvelles * (cours_ex - op.difference_jouissance) - cout_souscription
    pct_exercer = (actions_detenues + nouvelles) / (op.actions_anciennes + n_total)

    # 2. Vendre les droits : l'associé encaisse le prix du droit et garde ses actions
    valeur_vendre = actions_detenues * cours_ex + actions_detenues * prix_droit
    pct_vendre = actions_detenues / (op.actions_anciennes + n_total)

    # 3. Laisser expirer : les droits perdent toute valeur
    valeur_expirer = actions_detenues * cours_ex
    pct_expirer = pct_vendre

    pct_initial = actions_detenues / op.actions_anciennes

    return {
        "valeur_droit_theorique": round(v_droit, 4),
        "cours_theorique_ex_droit": round(cours_ex, 4),
        "participation_initiale": round(pct_initial, 6),
        "exercer": {
            "participation_finale": round(pct_exercer, 6),
            "gain_ou_perte": round(valeur_exercer - valeur_initiale, 3),
        },
        "vendre": {
            "participation_finale": round(pct_vendre, 6),
            "gain_ou_perte": round(valeur_vendre - valeur_initiale, 3),
        },
        "expirer": {
            "participation_finale": round(pct_expirer, 6),
            "gain_ou_perte": round(valeur_expirer - valeur_initiale, 3),
        },
    }


def dilution_apport_immeuble(
    actions_anciennes: int,
    cours: float,
    prix_emission: float,
    valeur_declaree: float,
    valeur_reelle: float,
) -> dict:
    """Cas de l'apport en nature d'un immeuble avec DPS supprimé.

    L'apporteur reçoit des actions pour la valeur déclarée de l'immeuble.
    Si la valeur réelle est plus faible, les autres associés subissent
    une perte de valeur par action.
    """
    if min(actions_anciennes, cours, prix_emission, valeur_declaree, valeur_reelle) <= 0:
        raise ValueError("Toutes les valeurs doivent être strictement positives.")

    nouvelles = valeur_declaree / prix_emission
    capitalisation_avant = actions_anciennes * cours
    valeur_par_action_apres = (capitalisation_avant + valeur_reelle) / (actions_anciennes + nouvelles)
    perte_par_action = cours - valeur_par_action_apres
    part_apporteur = nouvelles / (actions_anciennes + nouvelles)

    return {
        "actions_emises_a_l_apporteur": round(nouvelles, 2),
        "part_apporteur": round(part_apporteur, 6),
        "valeur_par_action_apres": round(valeur_par_action_apres, 4),
        "perte_par_action_pour_les_autres": round(perte_par_action, 4),
        "perte_totale_autres_associes": round(perte_par_action * actions_anciennes, 3),
        "ecart_valeur_declaree_reelle": round(valeur_declaree - valeur_reelle, 3),
    }


if __name__ == "__main__":
    # Exemple n°1 de la BVMT : WIFAK, 1 action nouvelle pour 2 anciennes à 6,500 DT, cours 8,000 DT
    op = Operation(
        actions_anciennes=1_000_000,
        cours_cum=8.0,
        prix_souscription=6.5,
        parite_nouvelles=1,
        parite_anciennes=2,
        difference_jouissance=0.35,
    )
    print("Cours théorique du droit :", round(valeur_droit(op), 4), "DT")
    print("Cours de référence après détachement :", round(terp(op), 4), "DT")
    print(simulation_associe(op, actions_detenues=10_000))
    print(dilution_apport_immeuble(1_000_000, 20.0, 20.0, 5_000_000, 3_500_000))
