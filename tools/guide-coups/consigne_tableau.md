# Tableau des coups (seule sortie du relevé : commandes et pages, aucun texte du guide)

Fichier : $GUIDE/csv/<ton lot>.csv (ex. 025-048.csv)
UTF-8, séparateur « ; », PAS de guillemets, jamais de « ; » dans un champ (remplace par « / »). Première ligne = en-tête exacte :

jeu;mode;personnage;version_style;type;nom_du_coup;manipulation;boutons;conditions;page_pdf

Une ligne par coup listé dans les tableaux du guide (Throws, Special Attacks, Super Combos, Alpha Counters, Custom Combos,
commandes système générales, secrets à manipulation comme le déblocage d'un perso, etc.). Les combos de stratégie écrits dans
le texte courant ne sont pas des lignes, sauf s'ils sont dans un tableau.

- jeu : Street Fighter Alpha / Street Fighter Alpha 2 / Street Fighter Alpha 2 Gold / Street Fighter Alpha 3 /
  Super Gem Fighter Mini Mix / Anthology (secrets, options communs)
- mode : mode de jeu si le guide le précise (Manual, Automatic, Saikyo, Classical, Hyper Street Fighter Alpha…), sinon vide
- personnage : tel qu'imprimé (Ryu, Chun-Li…) ; « Tous » pour une commande commune
- version_style : ISM (X-ISM, A-ISM, V-ISM), variante (Evil Ryu, Shin Akuma, Classical Chun-Li…) si le guide la précise, sinon vide
- type : lancer / special / super / alpha counter / custom combo / systeme / secret / autre
- nom_du_coup : tel qu'imprimé
- manipulation : uniquement la direction, en flèches Unicode → ← ↓ ↑ ↘ ↙ ↗ ↖ ; charge notée « ← (charge) → » ;
  alternatives « →↓↘ ou ←↓↙ » ; enchaînement de boutons sans direction (ex. Shun Goku Satsu) : « LP, LP, →, LK, HP » ici ;
  vide si aucun mouvement
- boutons : Punch / Kick / LP / MP ou HP / 3 Punch / 2 Kick… (traduits a minima : « or » → « ou », « all three Punches » → « 3 Punch »)
- conditions : en français, concises : « en l'air », « au sommet d'un saut avant », « près de l'adversaire », « jauge niveau 3 »,
  « pendant Hyakki Shu », « en garde », « niveau selon le nombre de boutons »… ; vide si aucune
- page_pdf : numéro de page du PDF

Les flèches doivent être vérifiées au zoom (zoom.sh), comme le demande consigne_transcription.md. Si une ligne reste douteuse, ajoute « [douteux] »
dans conditions.
