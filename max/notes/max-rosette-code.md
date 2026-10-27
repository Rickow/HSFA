# Rosette du code PSP (C) ↔ 68K arcade : API moteur et champs objet (pour info, pas d'action requise)

Note de la session MAX, 2026-10-04. Rien n'est poussé. Détail : `sfa3max-psp-widescreen/work/re/rosette_code/README.md`.

- Appris sur **les 26 persos de SFA3** (C du PSP ↔ `sfa3_prog.bin`), sans attendre Upper : ton `rosetta.py` par
  constantes ne marche pas ici (le C ne garde pas les immédiats), mais **les arguments des appels survivent**.
- **API moteur** : 45 paires sûres (vote indépendant par perso) + 16 par interpolation (l'ordre des adresses est
  conservé). Ex. : `$2A708` / `$2A758` / `$2A710` = lancer l'animation n (tables `$2B0` / `$2B4` / `$2BC`),
  `$2A7EA` = avancer l'animation (`$32`), `$2F728` / `$2F74C` = force du poing / du pied pressé (`$378|$37A`),
  `$2E7F2` = prise (adversaire `$38`, attaque n de `$A0`), `$804DA` / `$80B70` = création d'objet fils.
- **Champs de la structure joueur** : le C recopie la structure 68K, décalée par zones (14 zones, ex. `$040-$067` →
  `+0x20`, `$101-$132` → `+0x50`, `$290-$2C9` → `−0x10`) ; 82 % des accès d'Eagle se traduisent directement.
- Tables par perso de l'arcade : 20 tables de 32 longs indexées par `$102(A6)` en `0xDCB12…0xDF892` (points d'entrée
  du code de chaque perso, régions rangées dans l'ordre des ID : Ryu `0x33F00-0x35A74`…). Pour `$26`–`$29` dans le
  fork arcade, ce sont aussi des tables à étendre.
