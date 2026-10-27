# Vérification du tableau des coups contre SuperCombo Wiki

Tableau : $GUIDE/csv/*.csv (séparateur « ; »,
colonnes jeu;mode;personnage;version_style;type;nom_du_coup;manipulation;boutons;conditions;page_pdf). Ne modifie PAS ces fichiers.
Pages SuperCombo converties en texte : .../guide/sc/txt/<Jeu>--<Perso>.txt (Street_Fighter_Alpha, Street_Fighter_Alpha_2 [Gold inclus],
Street_Fighter_Alpha_3, Pocket_Fighter = Super Gem Fighter Mini Mix). Les icônes de commande y sont des jetons entre crochets :
[Qcf]=↓↘→ [Qcb]=↓↙← [Dp]=→↓↘ [Rdp]=←↓↙ [Hcf]=←↙↓↘→ [Hcb]=→↘↓↙← [F]=→ [B]=← [D]=↓ [U]=↑ [Df]=↘ [Db]=↙ [Uf]=↗ [Ub]=↖
[Cb]=← (charge) [Cd]=↓ (charge) [Cdb]=↙ (charge) [Tk]=↓↘→↗ (tiger knee) [360]/[R360]=360° [Qcd]=←↙↓ (à confirmer par le contexte)
[P]=Punch [K]=Kick [Lp]/[Mp]/[Hp]/[Lk]/[Mk]/[Hk] [2p]/[3p]=2/3 Punch [2k]/[3k] [S]=Start [X-ISM]/[A-ISM]/[V-ISM]=ISM concernée.
Pages du guide : zoom 300 dpi avec .../guide/zoom.sh <page> <x0> <y0> <x1> <y1> (fractions 0-1), images entières .../guide/p/p-NNN.png.

Pour chaque ligne de ton périmètre de type lancer / special / super / alpha counter / systeme (pas les combos ni custom combos, sauf
s'ils sont marqués [douteux]) ET pour toute ligne contenant « douteux », « sic », « probablement » ou « tel qu » :
1. retrouve le coup sur la page SuperCombo du perso (noms parfois différents : Hadoken/Hado Ken, Shoryuken/Shoryu Ken… ; SuperCombo
   donne souvent une commande par ISM en Alpha 3) ;
2. compare manipulation et boutons (une notation équivalente n'est pas un écart : ex. « ↓↘→ » = [Qcf] ; « Any Punch » = [P]) ;
3. en cas d'écart, re-zoome la ligne du guide pour savoir si c'est NOTRE lecture qui est fausse (alors corrige vers ce qui est imprimé,
   et si l'imprimé est lui-même faux, vers SuperCombo) ou une COQUILLE du guide (alors corrige vers SuperCombo).
   Si SuperCombo ne contient pas le coup ou ne permet pas de trancher, laisse la ligne et note-la « non vérifiable ».

Sortie : un fichier TSV (tabulations) à créer, avec l'en-tête :
page_pdf	personnage	nom_du_coup	champ	ancien	nouveau	cause	source
- champ : manipulation / boutons / conditions / nom_du_coup ; ancien = valeur EXACTE actuelle du champ dans le CSV (copie-colle) ;
  nouveau = valeur corrigée complète du champ (même notation que le tableau : flèches Unicode, « ← (charge) → », « ou »…) ;
  pour une ligne [douteux] confirmée sans changement, mets une ligne champ=conditions avec nouveau = conditions sans « [douteux] »
  et la mention « vérifié SuperCombo ».
- cause : lecture_erronee / coquille_guide / douteux_confirme / non_verifiable
- source : URL SuperCombo (https://wiki.supercombo.gg/w/<Jeu>/<Perso>) ou « zoom p.NNN ».
Pour une coquille du guide, dans conditions ajoute en plus « (guide imprime : <ancienne manipulation>) » via une ligne champ=conditions.
Termine en répondant : nombre de lignes vérifiées, nombre de corrections par cause, et la liste des « non_verifiable ».
