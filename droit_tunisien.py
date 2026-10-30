"""Module juridique : contrôle d'une augmentation de capital selon le droit tunisien.

Textes : Code des sociétés commerciales (CSC, édition officielle de l'Imprimerie
officielle de la République tunisienne mise à jour le 10 février 2022), document de la
Bourse des Valeurs Mobilières de Tunis sur les droits de souscription,
Code des droits réels (CDR), Code de l'aménagement du territoire et de l'urbanisme (CATU),
Code des droits d'enregistrement et de timbre (CDET). Le détail est dans
docs/RECOMMANDATIONS_JURIDIQUES.md.

Ce module aide à préparer un dossier. Il ne remplace pas l'avis d'un avocat
ou d'un notaire. Les articles du CSC ont été lus dans l'édition officielle de 2022 :
les lois postérieures ne sont pas prises en compte.
"""

from dataclasses import dataclass

BLOQUANT = "BLOQUANT"
ATTENTION = "ATTENTION"
INFO = "INFO"
_ORDRE = {BLOQUANT: 0, ATTENTION: 1, INFO: 2}

DELAI_MIN_SA = 15            # CSC art. 301
DELAI_MIN_SARL = 21          # CSC art. 131
SEUIL_ECART_VALEUR = 0.10    # seuil d'alerte propre à la plateforme, pas un seuil légal

# Statut : "officiel" = lu dans l'édition officielle du CSC (IORT, 2022), "bvmt" = document
# de la Bourse de Tunis, "lu" = vu dans un texte juridique en ligne, "secondaire" = commentaire
# ou article de praticien, "a verifier" = non confirmé par un texte.
REFERENCES = {
    "CSC art. 3": ("Si les apports comprennent un immeuble immatriculé, l'acte doit être rédigé selon la législation en vigueur, sous peine de nullité.", "officiel"),
    "CSC art. 11": ("Les droits fondamentaux de l'associé ne peuvent être réduits ou limités par les statuts ou par les décisions des assemblées.", "officiel"),
    "CSC art. 100": ("SARL : l'apport en nature est évalué par un commissaire aux apports désigné à l'unanimité des associés ou par ordonnance du président du tribunal. Les associés peuvent décider à la majorité de s'en passer si chaque apport ne dépasse pas 3 000 dinars. Sans commissaire, ils sont solidairement responsables envers les tiers pendant trois ans.", "officiel"),
    "CSC art. 131": ("SARL : statuts modifiés par les associés représentant les trois quarts du capital, ou selon le quorum et la majorité prévus aux statuts. Chaque associé participe à l'augmentation selon sa part, dans un délai d'au moins 21 jours à compter de l'ouverture, avisé par lettre recommandée avec accusé de réception ou tout autre moyen laissant une trace écrite. Les parts non souscrites sont réparties entre les autres associés sous 21 jours, puis la souscription peut être ouverte aux tiers par décision de l'assemblée. Nul associé ne peut être obligé d'augmenter son engagement.", "officiel"),
    "CSC art. 133": ("SARL : toute augmentation est décidée selon l'article 131. L'augmentation par incorporation de réserves peut être décidée par les associés représentant plus de la moitié du capital.", "officiel"),
    "CSC art. 134": ("SARL : les fonds d'une souscription en numéraire sont déposés auprès d'un établissement financier. Si l'augmentation n'est pas réalisée dans les six mois de l'assemblée, tout apporteur peut demander à retirer son apport.", "officiel"),
    "CSC art. 135": ("SARL : si la valeur retenue diffère de celle du commissaire, associés et souscripteurs sont solidairement responsables envers les tiers pendant trois ans.", "officiel"),
    "CSC art. 163": ("Avant toute souscription, dépôt du projet de statuts au greffe du tribunal de première instance du siège. Les articles 293 et 302 renvoient à ces formalités pour la publicité de l'augmentation.", "officiel"),
    "CSC art. 173": ("SA : les commissaires aux apports sont désignés par ordonnance sur requête du président du tribunal de première instance, parmi les experts judiciaires, et évaluent chaque apport sous leur responsabilité (description, mode d'évaluation, intérêt pour la société). L'article 306 y renvoie pour l'augmentation de capital.", "officiel"),
    "CSC art. 174": ("Ne peuvent être commissaires aux apports : l'apporteur, ses ascendants, descendants, collatéraux et alliés jusqu'au deuxième degré, ceux des administrateurs ou membres du directoire lors des augmentations, leurs conjoints, et les autres personnes visées par l'article.", "officiel"),
    "CSC art. 284 bis": ("SA : les actionnaires détenant au moins 5 % du capital (3 % pour une société faisant appel public à l'épargne, ou une participation d'au moins un million de dinars), non membres du conseil, peuvent poser des questions écrites au moins deux fois par an. Réponse écrite due dans le mois.", "officiel"),
    "CSC art. 290": ("SA : les actionnaires détenant au moins 10 % du capital peuvent demander l'annulation des décisions contraires aux statuts ou portant atteinte aux intérêts de la société, prises dans l'intérêt de quelques actionnaires ou d'un tiers. L'action se prescrit par un an.", "officiel"),
    "CSC art. 290 bis": ("SA : les actionnaires détenant au moins 10 % du capital peuvent demander au juge des référés une expertise de gestion. Le rapport va notamment au Conseil du marché financier pour les sociétés faisant appel public à l'épargne.", "officiel"),
    "CSC art. 290 ter": ("SA ne faisant pas appel public à l'épargne : les actionnaires détenant 5 % au plus peuvent imposer le rachat de leurs titres à un prix fixé par expertise. Cet article ne s'applique pas aux sociétés faisant appel public à l'épargne.", "officiel"),
    "CSC art. 292": ("SA : l'augmentation se fait par actions nouvelles ou par majoration de la valeur nominale. Libération en numéraire, par compensation de créances, par incorporation de réserves, de bénéfices ou de primes d'émission, par apports en nature ou par conversion d'obligations. La majoration de la valeur nominale exige l'unanimité, sauf incorporation de réserves, de bénéfices ou de primes.", "officiel"),
    "CSC art. 293": ("SA : l'augmentation est décidée par l'assemblée générale extraordinaire, dans les conditions de la loi et sans contredire les dispositions légales impératives. La décision est publiée selon l'article 163.", "officiel"),
    "CSC art. 294": ("SA : l'assemblée peut déléguer au conseil la réalisation de l'augmentation, qui doit intervenir dans les cinq ans de la décision. Le quart de l'augmentation et la totalité de la prime d'émission doivent être libérés dans le délai de l'alinéa 3, sinon la décision est réputée non écrite (le texte français imprimé indique cinq ans, une note de l'Imprimerie officielle demande de lire six mois selon la version arabe). Une clause des statuts donnant au conseil le pouvoir de décider l'augmentation est réputée non avenue.", "officiel"),
    "CSC art. 295": ("SA : le capital social doit être intégralement libéré avant toute émission de nouvelles actions, à peine de nullité.", "officiel"),
    "CSC art. 296": ("SA : DPS proportionnel au montant des actions, négociable lorsqu'il est détaché d'actions négociables, sinon cessible comme l'action. Renonciation individuelle possible, clause contraire non avenue.", "officiel"),
    "CSC art. 297": ("SA : les actions non souscrites sont attribuées aux actionnaires qui ont demandé plus que leur droit préférentiel (souscription à titre réductible), proportionnellement à leurs parts et dans la limite de leurs demandes.", "officiel"),
    "CSC art. 298": ("SA : limitation aux souscriptions si elles atteignent les trois quarts et si l'assemblée l'a prévu, redistribution aux actionnaires sauf décision contraire, offre au public si l'assemblée l'a admise.", "officiel"),
    "CSC art. 299": ("SA : augmentation non réalisée si les souscriptions libérées n'atteignent pas la totalité (ou les trois quarts en cas de limitation). Le conseil peut limiter d'office l'augmentation quand le non souscrit est inférieur à 5 %.", "officiel"),
    "CSC art. 300": ("SA : suppression du DPS par l'assemblée extraordinaire, qui approuve à peine de nullité le rapport du conseil et celui des commissaires aux comptes.", "officiel"),
    "CSC art. 301": ("SA : délai d'exercice d'au moins quinze jours, à compter de l'annonce au Journal officiel du droit préférentiel, des dates d'ouverture et de clôture et de la valeur des actions à l'émission.", "officiel"),
    "CSC art. 302": ("SA : formalités de publicité des articles 163 et suivants avant l'ouverture de la souscription.", "officiel"),
    "CSC art. 303 et 304": ("SA : le contrat de souscription est constaté par un bulletin de souscription. Les souscriptions et versements sont constatés par un certificat de l'établissement dépositaire des fonds.", "officiel"),
    "CSC art. 306": ("SA : apports en nature évalués par un commissaire aux apports. L'assemblée délibère sur l'évaluation et, si elle l'approuve, déclare l'augmentation réalisée. Si elle réduit l'évaluation, l'accord exprès de l'apporteur est requis, sinon l'augmentation n'est pas réalisée. Les actions d'apport doivent être intégralement libérées dès leur émission.", "officiel"),
    "BVMT droits de souscription": ("Document de la Bourse de Tunis (mise à jour mars 2009). Droit de souscription au détachement : Ds = N/(A+N) x (C - PE - D). Pendant la période : Ds = N/A x (C - D - PE). Les droits sont négociables pendant la période. Les actions nouvelles non assimilées valent C - D et sont négociables à la date fixée par l'avis de réalisation publié au bulletin de la Bourse.", "bvmt"),
    "CDR art. 305": ("Un droit réel sur immeuble immatriculé ne se constitue qu'à compter de son inscription au Livre Foncier.", "lu"),
    "CDR art. 308": ("Les droits réels existants sont inscrits sur le titre, un droit non inscrit est réputé non avenu.", "lu"),
    "CDR art. 317 et 318": ("L'immatriculation est facultative, tout titulaire d'un droit réel immobilier peut la requérir.", "lu"),
    "CATU art. 42 à 44": ("Droit de priorité d'achat dans les périmètres de réserves foncières : prénotation sur le titre, réponse du bénéficiaire sous un an, annulation possible du contrat conclu en violation.", "lu"),
    "CDET art. 29": ("Les cessions de titres portant sur des droits de propriété ou de jouissance d'immeubles sont réputées porter sur les biens, règles des ventes d'immeubles.", "lu"),
    "Note commune 16/2011": ("Plus value de cession de titres : régime décrit pour 2011, à confronter aux lois de finances récentes.", "a verifier"),
    "Décret du 4 juin 1957": ("Autorisation préalable du gouverneur pour l'acquisition d'immeubles par un étranger.", "secondaire"),
    "Loi 2005-40": ("Exceptions à l'autorisation (zones touristiques ou industrielles), selon un article de praticien.", "secondaire"),
    "Terres agricoles": ("Un étranger ne peut pas acquérir de terre agricole, selon un article de praticien de 2013.", "secondaire"),
}


@dataclass(frozen=True)
class Alerte:
    gravite: str
    theme: str
    message: str
    references: tuple


@dataclass
class OperationJuridique:
    """Faits de l'opération, à renseigner par le juriste ou la société."""

    forme: str                              # "SA", "SARL" ou "SCI"
    liberation: str = "numeraire"           # "numeraire", "nature", "mixte" ou "incorporation"
    age_tenue: bool = False                 # décision de l'assemblée extraordinaire
    capital_libere: bool = False            # capital existant intégralement libéré (SA)
    appel_public_epargne: bool = False      # société cotée ou faisant appel public à l'épargne
    publication_jort: bool = False
    delai_souscription_jours: int | None = None
    dps_supprime: bool = False
    rapport_conseil: bool = False
    rapport_cac: bool = False
    taux_souscription: float | None = None  # entre 0 et 1
    limitation_prevue: bool = False
    commissaire_apports: bool = False
    evaluation_approuvee: bool = False
    evaluation_reduite_par_age: bool = False
    accord_apporteur: bool = False
    valeur_declaree: float | None = None
    valeur_expertisee: float | None = None
    apport_immeuble: bool = False
    immeuble_immatricule: bool | None = None
    acte_forme_legale: bool = False
    inscription_livre_foncier_prevue: bool = False
    immeuble_en_reserve_fonciere: bool = False
    droit_priorite_purge: bool = False
    acquereur_etranger: bool = False
    autorisation_gouverneur: bool = False
    terre_agricole: bool = False
    cession_titres_immobiliers: bool = False

    def __post_init__(self):
        if self.forme not in ("SA", "SARL", "SCI"):
            raise ValueError("La forme doit être SA, SARL ou SCI.")
        if self.liberation not in ("numeraire", "nature", "mixte", "incorporation"):
            raise ValueError("La libération doit être numeraire, nature, mixte ou incorporation.")
        if self.taux_souscription is not None and not 0 <= self.taux_souscription <= 1:
            raise ValueError("Le taux de souscription doit être compris entre 0 et 1.")


def analyser(op: OperationJuridique, seuil_ecart: float = SEUIL_ECART_VALEUR) -> list:
    """Retourne les alertes juridiques, les plus graves en premier."""
    alertes = []

    def ajouter(gravite, theme, message, *refs):
        alertes.append(Alerte(gravite, theme, message, tuple(refs)))

    en_numeraire = op.liberation in ("numeraire", "mixte")
    en_nature = op.liberation in ("nature", "mixte")
    incorporation = op.liberation == "incorporation"

    # Forme de la société et décision d'assemblée
    if op.forme == "SCI":
        ajouter(ATTENTION, "Forme",
                "Le Code des sociétés commerciales vise les sociétés commerciales, et le DPS légal des "
                "articles 296 et suivants concerne la société anonyme. Pour une SCI, le droit de "
                "souscription dépend des statuts et du droit des sociétés civiles. Faire valider le "
                "régime par un juriste avant d'ouvrir la souscription.",
                "CSC art. 296")
    if not op.age_tenue:
        if op.forme == "SA":
            ajouter(BLOQUANT, "Décision",
                    "Aucune décision d'assemblée générale extraordinaire n'est enregistrée. "
                    "L'augmentation de capital relève de cette assemblée.", "CSC art. 293")
        elif op.forme == "SARL" and incorporation:
            ajouter(BLOQUANT, "Décision",
                    "Aucune décision des associés n'est enregistrée. L'augmentation par incorporation de "
                    "réserves peut être décidée par les associés représentant plus de la moitié du capital.",
                    "CSC art. 133")
        elif op.forme == "SARL":
            ajouter(BLOQUANT, "Décision",
                    "Aucune décision de l'assemblée extraordinaire n'est enregistrée. "
                    "L'augmentation doit être décidée dans les conditions de l'article 131.",
                    "CSC art. 131", "CSC art. 133")

    # Capital existant (SA)
    if op.forme == "SA" and not op.capital_libere:
        ajouter(BLOQUANT, "Capital",
                "Le capital existant n'est pas intégralement libéré. Aucune action nouvelle ne peut être "
                "émise avant sa libération intégrale, à peine de nullité.", "CSC art. 295")

    # Délai et publicité de la souscription en numéraire
    if en_numeraire and op.forme in ("SA", "SARL"):
        minimum = DELAI_MIN_SA if op.forme == "SA" else DELAI_MIN_SARL
        ref = "CSC art. 301" if op.forme == "SA" else "CSC art. 131"
        if op.delai_souscription_jours is None:
            ajouter(ATTENTION, "Délai",
                    f"Le délai de souscription n'est pas renseigné. Il doit être d'au moins {minimum} jours.", ref)
        elif op.delai_souscription_jours < minimum:
            ajouter(BLOQUANT, "Délai",
                    f"Le délai de souscription est de {op.delai_souscription_jours} jours, "
                    f"alors que le minimum est de {minimum} jours.", ref)
        if op.forme == "SA" and not op.publication_jort:
            ajouter(BLOQUANT, "Publicité",
                    "Les modalités du DPS (dates d'ouverture et de clôture, valeur des actions) doivent "
                    "être annoncées au Journal officiel avant l'ouverture de la souscription. "
                    "Le délai court à partir de cette annonce.", "CSC art. 301", "CSC art. 302")
        if op.forme == "SA":
            ajouter(INFO, "Libération",
                    "Le quart de l'augmentation et la totalité de la prime d'émission doivent être libérés dans le "
                    "délai de l'article 294, sinon la décision est réputée non écrite. Le texte français imprimé indique "
                    "cinq ans, une note de l'Imprimerie officielle demande de lire six mois selon la version arabe : "
                    "faire confirmer le délai. L'augmentation doit être réalisée dans les cinq ans de la décision.",
                    "CSC art. 294")
            ajouter(INFO, "Formalités de souscription",
                    "Chaque souscription est constatée par un bulletin de souscription, et les versements par un "
                    "certificat de l'établissement dépositaire des fonds.", "CSC art. 303 et 304")
        if op.forme == "SARL":
            ajouter(INFO, "Notification",
                    "Aviser chaque associé de l'ouverture de la souscription et du délai par lettre recommandée avec "
                    "accusé de réception, ou par tout autre moyen laissant une trace écrite, et conserver la preuve. "
                    "Les parts non souscrites sont d'abord réparties entre les autres associés sous vingt et un jours, "
                    "puis la souscription peut être ouverte aux tiers par décision de l'assemblée.",
                    "CSC art. 131")
            ajouter(INFO, "Fonds de souscription",
                    "Les fonds sont déposés auprès d'un établissement financier. Si l'augmentation n'est pas réalisée "
                    "dans les six mois de l'assemblée, tout apporteur peut demander à retirer son apport.",
                    "CSC art. 134")

    # Suppression du DPS
    if op.dps_supprime and not incorporation:
        if op.forme == "SA":
            manquants = []
            if not op.rapport_conseil:
                manquants.append("le rapport du conseil")
            if not op.rapport_cac:
                manquants.append("le rapport des commissaires aux comptes")
            if manquants:
                ajouter(BLOQUANT, "Suppression du DPS",
                        "Il manque " + " et ".join(manquants) + ". L'assemblée doit approuver ces rapports "
                        "à peine de nullité.", "CSC art. 300")
            ajouter(INFO, "Suppression du DPS",
                    "La suppression ne peut pas résulter d'une clause des statuts. Elle exige une "
                    "résolution de l'assemblée extraordinaire.", "CSC art. 296", "CSC art. 300")
        elif op.forme == "SARL":
            ajouter(ATTENTION, "Suppression du DPS",
                    "Le Code des sociétés commerciales ne prévoit pas de suppression du droit de participation des "
                    "associés de SARL à l'augmentation, et leurs droits fondamentaux ne peuvent être limités par les "
                    "statuts ni par les assemblées. La souscription ne s'ouvre aux tiers qu'après le délai et la "
                    "répartition entre associés de l'article 131. Faire valider par un juriste.",
                    "CSC art. 11", "CSC art. 131")

    # Apport en nature
    if en_nature:
        if op.forme == "SA":
            if not op.commissaire_apports:
                ajouter(BLOQUANT, "Apport en nature",
                        "Aucun commissaire aux apports n'est désigné. Il est nommé par ordonnance sur requête du "
                        "président du tribunal de première instance, parmi les experts judiciaires.",
                        "CSC art. 306", "CSC art. 173")
            else:
                ajouter(INFO, "Commissaire aux apports",
                        "Vérifier que le commissaire aux apports n'est pas dans un cas d'incompatibilité : l'apporteur "
                        "lui-même, ses ascendants, descendants, collatéraux et alliés jusqu'au deuxième degré, ceux des "
                        "administrateurs ou membres du directoire, leurs conjoints, et les autres cas de l'article 174. "
                        "Son rapport décrit chaque apport, son mode d'évaluation et son intérêt pour la société.",
                        "CSC art. 173", "CSC art. 174")
            if not op.evaluation_approuvee:
                ajouter(BLOQUANT, "Apport en nature",
                        "L'assemblée n'a pas approuvé l'évaluation des apports. Cette approbation emporte "
                        "la réalisation de l'augmentation.", "CSC art. 306")
            if op.evaluation_reduite_par_age and not op.accord_apporteur:
                ajouter(BLOQUANT, "Apport en nature",
                        "L'assemblée a réduit l'évaluation sans l'accord exprès de l'apporteur. "
                        "Dans ce cas l'augmentation n'est pas réalisée.", "CSC art. 306")
            ajouter(INFO, "Apport en nature",
                    "Pour les actions d'apport, la protection des autres actionnaires repose sur l'évaluation "
                    "du commissaire aux apports et sur le vote de l'assemblée. Le DPS vise les souscriptions en numéraire. "
                    "Les actions d'apport doivent être intégralement libérées dès leur émission.",
                    "CSC art. 306", "CSC art. 296")
        elif op.forme == "SARL":
            if not op.commissaire_apports:
                ajouter(BLOQUANT, "Apport en nature",
                        "Aucun commissaire aux apports n'est désigné. Il est désigné à l'unanimité des associés ou par "
                        "ordonnance du président du tribunal, sauf si les associés décident à la majorité de s'en passer "
                        "pour des apports ne dépassant pas 3 000 dinars chacun. À défaut, les associés sont solidairement "
                        "responsables envers les tiers de la valeur attribuée pendant trois ans.",
                        "CSC art. 100", "CSC art. 135")
            else:
                ajouter(INFO, "Apport en nature",
                        "Si la valeur retenue diffère de celle du commissaire, associés et souscripteurs "
                        "sont solidairement responsables envers les tiers pendant trois ans.", "CSC art. 135")

        if op.valeur_declaree and op.valeur_expertisee:
            ecart = (op.valeur_declaree - op.valeur_expertisee) / op.valeur_expertisee
            if abs(ecart) > seuil_ecart:
                sens = "supérieure" if ecart > 0 else "inférieure"
                suite = (" Les autres actionnaires sont dilués : chiffrer la perte avec dilution_apport_immeuble."
                         if ecart > 0 else "")
                ajouter(ATTENTION, "Évaluation",
                        f"La valeur déclarée est {sens} de {abs(ecart):.0%} à la valeur expertisée "
                        f"(seuil d'alerte de la plateforme : {seuil_ecart:.0%}).{suite}",
                        "CSC art. 306")

    # Immeuble et droit foncier
    if op.apport_immeuble:
        if op.immeuble_immatricule is None:
            ajouter(ATTENTION, "Droit foncier",
                    "Le statut d'immatriculation de l'immeuble n'est pas connu. Le vérifier à la "
                    "Conservation de la propriété foncière et lire les droits inscrits sur le titre.",
                    "CDR art. 308")
        elif op.immeuble_immatricule:
            if not op.acte_forme_legale:
                ajouter(BLOQUANT, "Droit foncier",
                        "L'acte d'apport doit respecter la forme prévue par la législation, sous peine de "
                        "nullité quand l'apport comprend un immeuble immatriculé.", "CSC art. 3")
            if not op.inscription_livre_foncier_prevue:
                ajouter(BLOQUANT, "Droit foncier",
                        "Un droit réel sur immeuble immatriculé ne se constitue qu'à compter de son inscription "
                        "au Livre Foncier. Tant que l'inscription n'est pas faite, la société n'est pas titulaire du droit.",
                        "CDR art. 305")
        else:
            ajouter(ATTENTION, "Droit foncier",
                    "L'immeuble n'est pas immatriculé, donc aucune inscription au Livre Foncier n'est possible. "
                    "L'immatriculation est facultative et peut être requise par tout titulaire d'un droit réel. "
                    "Envisager de la demander avant l'apport.", "CDR art. 317 et 318")
        if op.immeuble_en_reserve_fonciere and not op.droit_priorite_purge:
            ajouter(ATTENTION, "Droit de priorité d'achat",
                    "L'immeuble est dans un périmètre de réserve foncière. L'État, une collectivité locale ou une "
                    "agence peut avoir un droit de priorité d'achat, prénoté sur le titre, et un contrat conclu en "
                    "violation peut être annulé. Vérifier si l'apport y est soumis et notifier le bénéficiaire. "
                    "Ce droit est distinct du DPS.", "CATU art. 42 à 44")
        if op.acquereur_etranger:
            if not op.autorisation_gouverneur:
                ajouter(BLOQUANT, "Acquisition par un étranger",
                        "L'autorisation préalable du gouverneur est exigée. Sans elle, la vente est considérée "
                        "comme nulle. Des exceptions existent, par exemple en zone touristique ou industrielle.",
                        "Décret du 4 juin 1957", "Loi 2005-40")
            if op.terre_agricole:
                ajouter(BLOQUANT, "Acquisition par un étranger",
                        "Un étranger ne peut pas acquérir de terre agricole.", "Terres agricoles")

    # Fiscalité
    if op.cession_titres_immobiliers:
        ajouter(INFO, "Fiscalité",
                "La cession de titres portant sur des droits d'immeubles est traitée comme une vente d'immeubles "
                "pour les droits d'enregistrement. Le taux et le régime de la plus value sont à vérifier "
                "dans les textes en vigueur.", "CDET art. 29", "Note commune 16/2011")

    # Résultat de la souscription
    if op.forme == "SA" and en_numeraire and op.taux_souscription is not None and op.taux_souscription < 1:
        t = op.taux_souscription
        if t > 0.95:
            ajouter(INFO, "Souscription",
                    "Le non souscrit est inférieur à 5 % : le conseil peut limiter l'augmentation au montant souscrit.",
                    "CSC art. 299")
        elif t >= 0.75 and op.limitation_prevue:
            ajouter(INFO, "Souscription",
                    "L'augmentation peut être limitée aux souscriptions reçues, car elles atteignent les trois quarts "
                    "et la limitation était prévue.", "CSC art. 298")
        else:
            ajouter(ATTENTION, "Souscription",
                    f"Les souscriptions couvrent {t:.0%} de l'augmentation. Sans limitation prévue, l'augmentation "
                    "n'est pas réalisée, sauf redistribution aux actionnaires ou offre au public admise par l'assemblée.",
                    "CSC art. 298", "CSC art. 299")

    # Incorporation de réserves
    if incorporation and op.forme == "SA":
        ajouter(INFO, "Incorporation de réserves",
                "L'augmentation par incorporation de réserves, de bénéfices ou de primes d'émission ne donne pas lieu "
                "à souscription en numéraire. La majoration de la valeur "
                "nominale des actions exige l'unanimité, sauf s'il s'agit d'une incorporation de réserves, de "
                "bénéfices ou de primes d'émission.", "CSC art. 292")
    if incorporation and op.forme == "SARL":
        ajouter(INFO, "Incorporation de réserves",
                "L'augmentation par incorporation de réserves peut être décidée par les associés représentant plus "
                "de la moitié du capital.", "CSC art. 133")

    # Société cotée ou faisant appel public à l'épargne
    if op.forme == "SA" and op.appel_public_epargne and en_numeraire:
        ajouter(INFO, "Marché boursier",
                "Les droits sont détachés à la date d'effet de l'augmentation et négociables pendant la période. "
                "Les actions nouvelles non assimilées sont négociables à la date fixée par l'avis de réalisation publié "
                "au bulletin de la Bourse. Les formalités propres au marché financier relèvent d'autres textes que le "
                "Code des sociétés commerciales et sont à vérifier.",
                "BVMT droits de souscription", "CSC art. 296")

    # Minoritaires
    if op.forme == "SA" and op.appel_public_epargne:
        ajouter(INFO, "Minoritaires",
                "Les actionnaires disposent de recours : questions écrites (3 % du capital), expertise de gestion et "
                "annulation de décisions prises dans l'intérêt de quelques actionnaires ou d'un tiers (10 %). Le rachat "
                "des petits porteurs de l'article 290 ter ne s'applique pas aux sociétés faisant appel public à "
                "l'épargne. Conserver les notifications, les rapports et les calculs de dilution.",
                "CSC art. 284 bis", "CSC art. 290", "CSC art. 290 bis")
    elif op.forme == "SA":
        ajouter(INFO, "Minoritaires",
                "Les actionnaires disposent de recours : questions écrites (5 % du capital), expertise de gestion et "
                "annulation de décisions prises dans l'intérêt de quelques actionnaires ou d'un tiers (10 %), et "
                "rachat de leurs titres par ceux qui détiennent 5 % au plus. Conserver les notifications, les "
                "rapports et les calculs de dilution.",
                "CSC art. 284 bis", "CSC art. 290", "CSC art. 290 bis", "CSC art. 290 ter")

    return sorted(alertes, key=lambda a: _ORDRE[a.gravite])


def rapport_texte(alertes: list) -> str:
    """Met les alertes en texte lisible."""
    if not alertes:
        return "Aucune alerte."
    lignes = []
    for a in alertes:
        lignes.append(f"[{a.gravite}] {a.theme} : {a.message}")
        lignes.append("    Références : " + ", ".join(a.references))
    return "\n".join(lignes)


if __name__ == "__main__":
    dossier = OperationJuridique(
        forme="SA",
        liberation="nature",
        age_tenue=True,
        capital_libere=True,
        dps_supprime=True,
        rapport_conseil=True,
        rapport_cac=False,
        commissaire_apports=True,
        evaluation_approuvee=True,
        valeur_declaree=5_000_000,
        valeur_expertisee=3_500_000,
        apport_immeuble=True,
        immeuble_immatricule=True,
        acte_forme_legale=True,
        inscription_livre_foncier_prevue=False,
    )
    print(rapport_texte(analyser(dossier)))
