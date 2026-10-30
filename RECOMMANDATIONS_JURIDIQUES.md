# Recommandations juridiques : droit tunisien

Ce document accompagne le module `droit_tunisien.py`. Il résume les textes lus et les recommandations que la plateforme applique à une augmentation de capital dans une société à objet foncier.

Réserve : les articles du Code des sociétés commerciales (CSC) ont été lus dans l'édition officielle de l'Imprimerie officielle de la République Tunisienne, mise à jour le 10 février 2022. Les lois postérieures ne sont pas prises en compte. Le CDR, le CATU et le CDET ont été lus sur des sites de documentation juridique, et rien n'a été confronté au Journal officiel. Chaque référence porte un statut dans `REFERENCES` : officiel, bvmt, lu, secondaire ou à vérifier. Rien ne remplace l'avis d'un avocat ou d'un notaire tunisien.

## 1. Textes applicables

| Texte | Ce qu'il règle pour la plateforme | Statut |
| --- | --- | --- |
| CSC art. 3 | Acte d'apport rédigé selon la législation en vigueur, sous peine de nullité, si l'apport comprend un immeuble immatriculé | officiel |
| CSC art. 11 | Droits fondamentaux de l'associé non limitables par les statuts ou les assemblées | officiel |
| CSC art. 100, 131 à 135 (SARL) | Commissaire aux apports, majorité des trois quarts, délai d'au moins 21 jours avec avis écrit, répartition des parts non souscrites, dépôt des fonds, incorporation de réserves à la majorité simple, responsabilité solidaire de trois ans | officiel |
| CSC art. 163 | Dépôt au greffe, auquel renvoient les articles 293 et 302 pour la publicité | officiel |
| CSC art. 173 et 174 | Désignation du commissaire aux apports par ordonnance, incompatibilités | officiel |
| CSC art. 284 bis, 290, 290 bis, 290 ter | Recours des actionnaires : seuils de 5 % ou 3 % (questions écrites), 10 % (annulation, expertise), rachat des 5 % au plus hors appel public à l'épargne | officiel |
| CSC art. 292 | Modes d'augmentation, dont l'incorporation de réserves, bénéfices et primes | officiel |
| CSC art. 293 à 295 | Décision de l'assemblée extraordinaire, délégation et délais, capital intégralement libéré avant toute émission, à peine de nullité | officiel |
| CSC art. 296 à 299 | DPS proportionnel, souscription à titre réductible, limitation aux trois quarts, limitation d'office sous 5 % | officiel |
| CSC art. 300 à 304 | Suppression du DPS par l'assemblée avec les deux rapports, délai d'au moins 15 jours, publicité, bulletin et certificat de souscription | officiel |
| CSC art. 306 | Apport en nature : commissaire aux apports, approbation de l'évaluation, accord de l'apporteur si elle est réduite | officiel |
| Document BVMT, mars 2009 | Formules des droits de souscription, négociation, avis de réalisation | bvmt |
| CDR art. 305, 308, 317, 318 | Droit réel constitué par l'inscription au Livre Foncier, immatriculation | lu |
| CATU art. 42 à 44 | Droit de priorité d'achat en réserve foncière | lu |
| CDET art. 29 | Cession de titres portant sur des droits d'immeubles traitée comme une vente d'immeubles | lu |
| Décret du 4 juin 1957 | Autorisation du gouverneur pour l'acquisition par un étranger | secondaire |

## 2. Corrections apportées par la lecture de l'édition officielle

La première version du module reposait sur des sites de documentation. La lecture de l'édition 2022 a changé ceci.

1. L'article 295 impose que le capital soit intégralement libéré avant toute émission d'actions nouvelles, à peine de nullité. Le module ne le contrôlait pas. Il lève maintenant une alerte BLOQUANT pour une SA.
2. L'article 290 fixe le seuil d'annulation à 10 % du capital. La référence annonçait « 20 % ou 10 % ».
3. L'article 173 concerne la constitution de la société. Il s'applique à l'augmentation par le renvoi de l'article 306. Il décrit la désignation par ordonnance parmi les experts judiciaires, complétée par l'article 174 sur les incompatibilités.
4. L'article 100 permet aux associés de SARL de se passer d'un commissaire aux apports pour un apport ne dépassant pas 3 000 dinars. À défaut de commissaire, ils sont solidairement responsables pendant trois ans.
5. L'article 131 admet l'avis des associés par lettre recommandée ou tout autre moyen laissant une trace écrite. Les parts non souscrites sont d'abord réparties entre associés sous 21 jours, puis ouvertes aux tiers.
6. L'article 3 est confirmé : la nullité sanctionne l'acte qui ne respecte pas la forme légale quand l'apport comprend un immeuble immatriculé.
7. Les seuils des recours des articles 284 bis et 290 ter dépendent de l'appel public à l'épargne. Le module distingue les deux cas.
8. L'incorporation de réserves a ses règles : la majoration de la valeur nominale n'exige pas l'unanimité quand elle se fait par incorporation de réserves, de bénéfices ou de primes (art. 292), et une SARL décide à la majorité de plus de la moitié du capital (art. 133).

## 3. Recommandations

Avant l'opération

1. Fixer la forme de la société. Le DPS légal des articles 296 et suivants vise la société anonyme. Une SCI relève de ses statuts et du droit des sociétés civiles, à faire valider.
2. Vérifier que le capital existant est intégralement libéré (SA).
3. Prévoir un délai d'au moins 15 jours après l'annonce au JORT pour une SA, et 21 jours avec avis écrit pour une SARL. Garder une marge.
4. Si le DPS est supprimé, passer par une résolution de l'assemblée extraordinaire avec les deux rapports. Une clause des statuts ne suffit pas.
5. Pour un immeuble, vérifier s'il est immatriculé et lire les droits inscrits sur le titre. S'il ne l'est pas, envisager l'immatriculation avant l'apport.
6. Vérifier si l'immeuble est dans un périmètre de réserve foncière. Le droit de priorité d'achat est distinct du DPS.
7. Si un étranger acquiert l'immeuble, obtenir l'autorisation du gouverneur avant l'acte. La terre agricole lui est fermée selon la source consultée.

Pendant l'opération

8. Notifier les associés avec date certaine et conserver les preuves.
9. Désigner le commissaire aux apports par ordonnance, contrôler ses incompatibilités, et faire voter l'évaluation. Si l'assemblée la réduit, obtenir l'accord exprès de l'apporteur.
10. Chiffrer la dilution avec `dilution_apport_immeuble`. La plateforme alerte à partir de 10 % d'écart entre valeur déclarée et valeur expertisée. Ce seuil est un choix de la plateforme, pas un seuil légal.
11. Pour une société cotée, suivre l'avis de réalisation publié au bulletin de la Bourse.

Après l'opération

12. Rédiger l'acte dans la forme exigée et demander l'inscription au Livre Foncier. Tant qu'elle n'est pas faite, la société n'est pas titulaire du droit réel.
13. Libérer le quart de l'augmentation et la prime d'émission dans le délai de l'article 294, et accomplir la publicité et le dépôt au registre des entreprises.
14. Conserver le dossier pour répondre aux recours des minoritaires.

## 4. Points à faire valider par un juriste tunisien

1. Le délai de libération du quart (article 294, alinéa 3). Le texte français imprimé indique cinq ans, et une note de l'Imprimerie officielle demande de lire six mois selon la version arabe.
2. Le droit de souscription dans une SCI, hors du champ du CSC.
3. L'application du droit de priorité d'achat à un apport en société, et pas seulement à une vente.
4. La suppression du droit de participation dans une SARL, que le CSC ne prévoit pas.
5. Les taux d'enregistrement sur la cession de titres, et le régime de la plus value de cession, avec les lois de finances récentes.
6. L'effet d'une participation étrangère dans une société propriétaire d'immeuble, non traité par les sources lues.
7. Les exceptions à l'autorisation du gouverneur (loi 2005-40), citées par un article de 2013.
8. Les formalités auprès du Conseil du marché financier et de la Bourse pour une société cotée, qui relèvent de la loi sur le marché financier, absente des sources lues.
9. Les modifications du CSC postérieures à février 2022.

## 5. Sources consultées

1. Code des sociétés commerciales, édition 2022, Imprimerie officielle de la République Tunisienne (document fourni).
2. Bourse des Valeurs Mobilières de Tunis, document sur les droits de souscription : calcul théorique et négociation, mise à jour mars 2009 (document fourni).
3. CSC, extrait SARL (CMF) : https://www.cmf.tn/sites/default/files/pdfs/reglementation/textes-reference/code_societes_fr.pdf
4. CDR, articles 303 à 318 : https://jurisitetunisie.com/tunisie/codes/cdr/cdr1265.htm
5. CATU (loi 94-122) : https://faolex.fao.org/docs/pdf/tun16294.pdf
6. CDET, articles 26 à 31 : https://jurisitetunisie.com/tunisie/codes/cdet/cdet1060.htm
7. Note commune 16/2011 : https://bvmt.com.tn/sites/default/files/actualites/note-commune-ndeg162011-commentaires-sur-la-plus-value-provenant-de-la-cession-des-titres.pdf
8. Acquisition par les étrangers : https://legal-doctrine.com/edition/Lacquisition-dun-bien-immobilier-par-les-%C3%A9trangers-en-Tunisie et https://www.mondaq.com/real-estate/249514/guidelines-for-foreigners-when-buying-property-in-tunisia
