# Observation de SFA3 MAX sous PPSSPP (2026-10-07)

- **Émulateur** : `~/ppsspp-fork/build-headless/PPSSPPHeadless`, compilé depuis le fork local (sans téléchargement).
  - Configuration : `HEADLESS_CROSS=ON` (pas de SDL3), `-DGLEW_NO_GLU` (pas de libglu).
  - CMake et Ninja viennent du SDK Android : `~/Android/Sdk/cmake/3.31.6/bin`.
- **Lancement** (fichiers de travail hors configuration de l'utilisateur) :
  `PPSSPPHeadless --memstick=<scratch>/memstick --graphics=software --debugger-run=45678 --timeout-wall=3600 work/iso/out/EU_DECRYPTED_WS.iso`
  (copie de l'ISO patchée 16:9 : lue seulement ; le patch touche le test de visibilité 0x1D424).
- **Client** : `ppdbg.py`, client WebSocket en bibliothèque standard seule.
  - Méthodes : `req`, `r8/r16/r32`, `lire`, `capture` (pause → capture PNG → reprise), `appui`, `pause/reprise`.
  - `nav.py bouton[:n] … fichier.png` : navigation dans les menus. `ecrivain.py` : qui écrit une adresse.
  - Avance image par image : `req("cpu.runUntilTime", attendre="cpu.stepping", relativeUs=16700)`.
- **Adresses** : `adr(va)`. Segment 0 (code + données en lecture seule, va < 0x2D4F30) : + 0x08804000. Segment 1
  (données, BSS) : + 0x08AD8F30. Mesuré sur les LUI/ADDIU relogés.
- **Chemin vers un combat** : Yes (sans chargement) → Start ×2 → Training Mode (bas ×2, croix) → curseur (déplacements
  pas à pas : la grille a des trous) → croix ×2 par joueur → croix (décor) → combat.
- **Mesures faites** (Ingrid contre Ken, entraînement) :
  - `0x2F8` = boutons qui viennent d'être appuyés, `0x2FA` = relâchés ; poings `$10/$20/$40`, pieds `$80/$100/$200`.
  - `0x39CA19` = 1 en entraînement (mode de jeu ; le code teste 3).
  - Compteurs de réservoirs `0xA3E7C0-C9` = `0c 0c 06 20 10 10 26 00 03 20` (places libres).
  - Table des joueurs `0x213F88` → structures `0x092E3EA0` + `0x498 k`.

## Fins sur PSP : vérité de terrain (2026-10-10)
- `nav_arcade.py <perso hexa>` : du démarrage (carte mémoire neuve) jusqu'à une partie Arcade avec le perso imposé
  (écriture de J1 + 0x152 sur l'écran de sélection, comme +$102 de tournee.lua). Appuis en temps réel.
- `tournee_psp.py <dossier> [min] [période]` : vie du CPU ramenée à 1 (seulement si > 1 : ne JAMAIS la remonter après un
  K.O., sinon la fin de manche se fige sur « PERFECT »), vie de J1 au max, croix/carré en rafale, captures périodiques.
  L'émulation tourne ~4,5× plus vite que le temps réel : période 0,7 s pour suivre une fin.
- Eagle : partie complète jusqu'à la fin et au générique ; captures `~/.cache/sfa3max/ppsspp/fin_eagle/` (00020-00095 =
  fin). Constats : 1re partie sur le décor du combat contre Bison (sprites Eagle / Bison / Guile) ; scènes scroll2 =
  carte PSP lignes 104 + Y′ (sans repli à 64 : Y′ 01 Bouddha l. 105, 18 crâne l. 128, 26 Terre l. 142) ; image finale
  = train (plan A, scroll1) ; fonds rouge / salle du Psycho Drive = scroll3 (effets).

## Ghidra pour la PSP (2026-10-11)
- Ghidra 12.1.3 (`hsfa/tools/ghidra_12.1.3_PUBLIC`, JDK `hsfa/tools/jdk-21.0.12.1+1`) + extension **ghidra-allegrex
  v21.4** (kotcrab, `ghidra_12.1.3_PUBLIC_20260825_ghidra-allegrex.zip`, 1 945 797 o, sha256 62e829fa…8243), installée
  dans `~/.config/ghidra/ghidra_12.1.3_PUBLIC/Extensions/ghidra-allegrex` (partagée avec la session HSFA).
- Projet : `work/ghidra_psp/SFA3MAX_PSP` (hors dépôt : `work/` exclu) ; EBOOT EU déchiffré importé par le chargeur
  « PSP Executable (ELF) », langage `Allegrex:LE:32:default`, **image base 0**, analyse automatique faite.
  Commande d'import :
  `JAVA_HOME=… analyzeHeadless work/ghidra_psp SFA3MAX_PSP -import ULES00235_EBOOT.elf -loader-imagebase 0`
- Décompiler : `python work/re/ghidra_decomp.py 1d4c48 [...]` (python du venv HSFA, pyghidra).
- **Adresses** : CODE = VA de nos outils (0x1D4C48 = 0x1D4C48) ; DONNÉES (segment 1) = VA de nos outils **+ 0x2D4F30**
  (ex. perso de J2 0x80B55A -> 0xAE048A ; état de fin +$110 0x87FDC0 -> 0xB54CF0) ; adresse PSP réelle = 0x08804000 +
  adresse Ghidra.
