# PPSSPP-BANC : PPSSPP comme oracle automatique pour les persos MAX

Agent `agent_ppsspp_banc`, 2026-10-25. Dossier : `work/agent_ppsspp_banc/`.
But : lancer SFA3 MAX (PSP) **sans aucune fenêtre**, piloter les entrées image par image, poser des points d'arrêt, lire
RAM et registres, capturer image et son, le tout en Python, avec des résultats **reproductibles à l'octet**.

## 1. Ce qui est livré

| fichier | rôle |
|---|---|
| `psp_debug.py` | bibliothèque Python (bibliothèque standard seule, venv HSFA suffit) : classe `Banc` |
| `sfa3max.py` | adresses SFA3 MAX EU, décodage de la structure joueur, séquences de navigation |
| `creer_etats.py` | du démarrage au combat Eagle contre Ken, crée `etats/*.ppst` (≈ 17 s) |
| `exemple_eagle.py` | démo de bout en bout : coup d'Eagle, relevé des 2 joueurs à chaque image, captures |
| `exemple_points_arret.py` | points d'arrêt mémoire et exécution, registres |
| `exemple_audio.py` | enregistrement WAV du coup |
| `scenarios_max.py` + `nav_arcade.py`, `tournee_psp.py`, `super_bp.py` | portage image par image des scripts de la session MAX (§5b) |
| `reproductibilite.py` | mesure de reproductibilité (résultat : `repro_resultat.txt`) |
| `patches/0001-banc-framerun-state-audio.patch` | le patch minimal du source officiel (§7) |
| `build/PPSSPPHeadless` | binaire construit (md5 `0d41efd7297092fc7e5ba24511efd039`) |
| `demo_eagle/` | sorties de la démo : `releves.tsv`, `structures.bin`, `planche.png`, `captures/`, `resume.txt`, `coup_eagle.wav` |
| `trace_appels.py`, `lua_mame/trace_appels.lua`, `equivalences_connues.json`, `exemples_rapports/` | comparateur de traces d'appels PSP / Upper MAX (§10) |
| `re_ajouts/max_psp.tsv` | découvertes durables pour l'index `re/` |

## 2. Construction (déjà faite ; pour refaire)

- Source : **officiel** `github.com/hrydgard/ppsspp`, étiquette **v1.20.3** (celle du snap), clone `--depth 1 --recurse-submodules` dans `src/ppsspp`.
- Le snap de l'utilisateur (`~/snap/ppsspp-emulator`), sa configuration, ses sauvegardes et `~/ppsspp-fork` ne sont jamais touchés.
- Outils : `cmake` et `ninja` du SDK Android (`~/Android/Sdk/cmake/3.31.6/bin`), pas dans le PATH.

```
export PATH=~/Android/Sdk/cmake/3.31.6/bin:$PATH
cd work/agent_ppsspp_banc && mkdir build && cd build
nice -n 19 cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DHEADLESS=ON -DUSE_DISCORD=OFF -DUSE_MINIUPNPC=OFF \
     -DUNITTEST=OFF -DBUILD_TESTING=OFF -DUSE_WAYLAND_WSI=OFF \
     -DCMAKE_C_FLAGS=-DGLEW_NO_GLU -DCMAKE_CXX_FLAGS=-DGLEW_NO_GLU ../src/ppsspp
nice -n 19 ninja -j8 PPSSPPHeadless        # ≈ 12 min la première fois, ≈ 1 min après une retouche
```

`-DGLEW_NO_GLU` évite le paquet `libglu1-mesa-dev` (absent). Pour reconstruire après `git clone` : appliquer le patch
(`git apply patches/0001-*.patch` dans `src/ppsspp`).

**Dépendances système manquantes : aucune.** Pas de `apt install` à passer. (Xvfb n'est pas installé et n'est pas nécessaire.)

## 3. Lancement sans fenêtre

`Banc.lancer()` démarre `PPSSPPHeadless` ainsi :

```
env -u DISPLAY -u WAYLAND_DISPLAY SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy HOME=<run/> \
  nice -n 19 build/PPSSPPHeadless --debugger=<port> --graphics=software -j --memstick=run/memstick <ISO>
```

- Aucun écran n'est ouvert : pas de `DISPLAY`/`WAYLAND_DISPLAY`, pilote SDL « offscreen », rendu **logiciel** (le contexte
  OpenGL caché n'est même pas nécessaire). Même la fenêtre cachée de `PPSSPPHeadless` n'est donc pas créée sur l'écran de l'utilisateur.
- Carte mémoire et configuration : `run/memstick` (jamais celle du snap). La configuration est celle par défaut du mode headless (anglais).
- Le jeu démarre **en pause** sur la première instruction ; le débogueur WebSocket écoute le port demandé (le patch le limite à
  **127.0.0.1** : vérifié avec `ss -ltnp` pendant un essai, `LISTEN 127.0.0.1:<port>` ; l'officiel écoutait sur toutes les interfaces).
- ISO : `<workspace>/sfa3max-psp-widescreen/work/iso/src/EU_RETAIL.iso`, md5 `5f58de7e83a0270bead43103f6c0136e`
  **vérifié** (= ULES-00235 EU v1.01 ; identique à `~/Téléchargements/Street Fighter Alpha 3 Max (Europe) (v1.01).iso`). Lue en place, jamais copiée.
- Arrêt : par PID (`Banc.arreter()` ou `with`), jamais par nom. `persistant=True` laisse le processus vivre (PID dans `run/banc_<port>.pid`, `Banc.arreter_pid(port)`).

## 4. API du client (`psp_debug.py`)

```python
from psp_debug import Banc, plan, masque
with Banc.lancer(etat="etats/combat_eagle_ken.ppst", cpu="jit", son=False) as b:
    ...
```

Cœurs CPU : `jit` (défaut, ≈ 160 images/s en combat), `interp` (≈ 40 i/s), `ir` (≈ 70 i/s). Mêmes relevés image par image
sur les trois (§6). Mode du jeu : toujours en pause entre deux appels ; rien ne s'exécute hors de `images()`.

| méthode | effet |
|---|---|
| `Banc.lancer(iso, port, etat, cpu, son, dossier, memstick, persistant, extra)` | démarre sans fenêtre, attend le jeu, charge l'état |
| `Banc.connecter(port)` / `b.arreter()` / `Banc.arreter_pid(port)` | se connecter à un banc existant, arrêter par PID |
| `b.images(n, entrees=None, sondes=None)` | **exécute exactement n images** (jusqu'au vblank) ; renvoie `arret` (`frames` / `break`), `images`, `vblank`, `ticks`, `pc`, `raison`, `releves` |
| `plan([("right",55), ("down+right+square",3), ("-",120)])` | liste de masques, un par image ; `masque("down,right")`, noms PSP : `up down left right cross circle square triangle start select ltrigger rtrigger` (+ alias `haut bas gauche droite croix rond carre`) |
| `b.jusqu_arret(max_images, entrees)` | exécute jusqu'au point d'arrêt ; ajoute `regs` (tous les GPR, `pc`, `hi`, `lo`) |
| `b.lire(adr, n)`, `lire8/16/32`, `ecrire`, `ecrire8/16/32` | RAM PSP (adresses 0x08800000…), jeu en pause |
| `b.registres()` , `definir_registre(nom, v)`, `desassembler(adr, n)` | CPU |
| `b.point_arret_exec(adr, condition=None)`, `point_arret_mem(adr, taille, lecture, ecriture, changement, condition)`, `retirer_*`, `retirer_tous_points_arret()` | points d'arrêt |
| `b.capture("x.png")` | PNG 480×272 de l'écran courant (octets renvoyés) |
| `b.etat_sauver(f)`, `b.etat_charger(f)` | états de sauvegarde (fichiers `.ppst`, dans le dossier du banc) |
| `b.audio_debut("x.wav")`, `b.audio_fin()` | WAV 44,1 kHz stéréo de la sortie émulée (lancer avec `son=True`) |
| `b.empreinte_ram()` | md5 de la RAM utilisateur (24 Mo) + VRAM (2 Mo) : empreinte complète de l'état |
| `b.rtc_fixer(s)`, `rtc_lire()`, `reinitialiser()`, `info()`, `statut()`, `pas(n)`, `req(evt, **kw)` | divers, accès brut au WebSocket |

### Entrées déterministes image par image

`images(n, entrees=[m0, m1, …])` : `m_k` est appliqué **avant** l'image k, sur le thread d'émulation (hook de fin d'image),
donc indépendamment de la latence réseau. Liste plus courte que `n` : le dernier masque est conservé. `entrees=None` : les
boutons restent comme ils sont (piège : un bouton tenu le reste). Un appui d'une seule image est vu par le jeu (le
déplacement du coup ci-dessous est reconnu avec 3 images par direction).

### Relevés à chaque image

`images(n, sondes=[(adresse, taille), …])` lit ces plages **à la fin de chaque image** sur le thread d'émulation et renvoie
`releves[k] = (octets_sonde0, octets_sonde1, …)`. Coût : la structure joueur entière (0x498 o) × 2 joueurs × 199 images = 3 s.

### Points d'arrêt

Posés pendant la pause, déclenchés pendant `images()`/`jusqu_arret()` : `arret == "break"`, `images` = nombre d'images
terminées avant l'arrêt (l'arrêt a lieu pendant l'image suivante), registres via `regs`. Pour reprendre après un arrêt :
rappeler `images()`/`jusqu_arret()` (l'instruction courante n'est pas re-déclenchée).

## 5. SFA3 MAX EU : repères mesurés (`sfa3max.py`)

- Module ZERO3 chargé en `0x08804000`. Code (VA < 0x2D4F30) : RAM = `0x08804000 + VA`. **Données/BSS : RAM = `0x08804000 + 0x2D4F30 + VA`**
  (la colonne `role` de plusieurs lignes de `max_psp.tsv` dit `0x08804000 + VA` pour tout : faux pour les données).
- Table des joueurs `RAM 0x08A17F88` → J1 = `0x092E3EA0`, J2 = `0x092E4338` (+0x498).
- Champs : ID perso octet `+0x152` (Eagle 0x26, Maki 0x27, Ken 0x01), X long 16.16 `+0x10`, Y long 16.16 `+0x14` (sol = 40),
  pointeur du pas d'animation `+0x1C`, octets d'état `+0x04..+0x07`, compteur `+0x48`, vie mot `+0x70` (0x90 ; figée en entraînement).
- Chemin vers l'entraînement (images exactes) : `sfa3max.NAV_SELECTION` ; sélection d'Eagle : droite puis bas ×5 (curseur = ID 0x26) ;
  `NAV_EAGLE_KEN`. Les états `etats/selection_training.ppst` et `etats/combat_eagle_ken.ppst` sont fournis (re-générables par `creer_etats.py`).
- **IDs PSP** (octet J1+0x152) : Eagle 0x26, Maki 0x27, **Yun 0x28, Ingrid 0x29** (les ID Upper sont $2D/$2E : ne pas confondre), Ken 0x01.
- Observation : à l'état `combat_eagle_ken`, la marche vers Ken fait +2,5 px/image ; DP+carré déclenche le coup (pas `0x092F41B4…`), arc additif visible sur la capture.
- Points d'arrêt : l'écriture de X(J1) en marche avant passe par `0x08861E80` (a0 = nouvel X, a1 = +0x28000), image 29 de la démo.

## 5b. Scénarios MAX portés sur `Banc` (`scenarios_max.py`)

Portage des trois scripts de `work/re/ppsspp/` (qui attendaient des durées réelles) en **images exactes** : même script = même partie.

| script | fonction | exemple |
|---|---|---|
| `nav_arcade.py <perso> [état.ppst] [capture.png]` | `aller_arcade(b, perso)` : démarrage à froid → menu → ARCADE → perso imposé par écriture de J1+0x152 sur l'écran de sélection → début du 1er combat (~3 000 images, ≈ 12 s) | `nav_arcade.py ingrid etats/arcade_ingrid.ppst` |
| `tournee_psp.py <perso> <dossier> [images] [période]` (`--etat` pour repartir d'un état) | `tournee(b, dossier, images, periode)` : toutes les 8 images, vie J1 = 0x90, vie du CPU ramenée à 1 si > 1 (jamais relevée après un K.O.), croix/carré en alternance, capture périodique | `tournee_psp.py eagle run/fin_eagle 20000 200` |
| `super_bp.py [--etat f] "seq" VA,VA [VA:reg=val]` | `points_arret(b, seq, [VA…], forcages)` : points d'arrêt d'exécution sur des VA de code du module, relevé a0-a3, v0, ra à chaque passage, forçage d'un registre | `super_bp.py "-:5 right:40" 5DE80` |

Navigation par curseur (sans écriture mémoire) : `aller_entrainement(b, perso)` (rangée du bas : Eagle, Maki, ?, Yun, Ingrid). Contrôle : `en_combat(b, id)`.
Mesures : `nav_arcade.py eagle` deux fois → même empreinte RAM+VRAM (`86bd9e6b…`) ; `super_bp.py` : l'arrêt à `0x5DE80` tombe aux images 29, 30, 31, 31, 32… (deux écritures de X dans l'image 31 : `images` = images terminées, un même numéro deux fois = deux arrêts dans la même image) ; forçage `v0=7` vérifié.

## 6. Démo Eagle et reproductibilité

`python3 exemple_eagle.py` (≈ 5 s, sans fenêtre) : charge l'état, 10 images de repos, marche vers Ken (55 images), bas / bas+avant / bas+avant+carré
(3 images chacun), 120 images de repos. Sorties dans `demo_eagle/` : `releves.tsv` (X, Y, pas, état, compteur, vie des deux joueurs, une ligne par image),
`structures.bin` (octets bruts), `captures/` (10 PNG) et `planche.png`, `resume.txt` (empreintes).

**Mesure** (`reproductibilite.py`, résultat `repro_resultat.txt`) : 3 exécutions séquentielles + 3 en parallèle (sous charge) en JIT, plus interpréteur et IR :

| comparaison à la référence | relevés image par image | structures brutes | 10 captures | RAM+VRAM finale |
|---|---|---|---|---|
| JIT séquentiel ×3 | identiques | identiques | identiques | identique |
| JIT parallèle ×3 | identiques | identiques | identiques | identique |
| interpréteur, IR | identiques | identiques | identiques | **diffère** (mémoire interne du JIT/hôte ; sans effet sur le jeu) |

- Chaîne depuis le démarrage à froid (`creer_etats.py`, 3 150 images de navigation) exécutée deux fois : empreinte RAM+VRAM identique à l'écran de sélection (`faa099cc…`) et au début du combat (`4e6145ca…`).
- Le WAV du coup (199 images, 582 700 o) est identique d'une exécution à l'autre (md5 `14708a11…`).
- Précaution : le compteur `vblank` absolu dépend du processus ; compter les images en relatif.

## 7. Le patch (pourquoi un fork minimal)

Le WebSocket de la v1.20.3 officielle ne permet pas un relevé déterministe : pas de pas d'une image, entrées posées depuis le fil réseau (donc
à une image indéterminée), lecture mémoire en marche qui arrête le CPU où elle veut, pas d'état de sauvegarde, pas d'audio, et la capture d'écran échoue toujours en pause CPU.
Patch (`patches/0001-banc-framerun-state-audio.patch`, ≈ 60 lignes modifiées + `BancSubscriber.cpp/.h` ≈ 300 lignes) :

1. `Core/Core.cpp` : hook de fin d'image sur le thread d'émulation (`Core_SetFrameHook`), appelé à chaque `CORE_NEXTFRAME`.
2. `Core/Debugger/WebSocket/BancSubscriber.cpp` (nouveau) : événements `frame.run` (n images, entrées par image, sondes mémoire par image), `state.save`, `state.load`, `audio.record`, `banc.info`.
3. `GPU/Debugger/Stepping.cpp` : exécute les actions GPU demandées en pause CPU (sinon `gpu.buffer.screenshot` répond « Could not download output ») et attend avec un prédicat (sinon blocage possible).
4. `Common/Net/HTTPServer.cpp` + `headless/Headless.cpp` : écoute du débogueur sur 127.0.0.1 seulement (`http::g_banc_loopback_only`, IPv4).
5. `BancSubscriber.cpp` : `trace.start / trace.get / trace.stop` (journal d'appels sans arrêt, voir §10) et `banc.flush` (vide le cache JIT) ; `Breakpoints.cpp` : points d'arrêt de journal.
6. `headless/Headless.cpp` : options `--sound` et `--memstick=`, `-i/-j/--ir` réellement appliqués (le source les écrasait par l'interpréteur), sommeil de 1 ms en pause (au lieu de tourner à 100 %), `g_breakpoints.Frame()` à chaque tour (sans cela, un point d'arrêt posé après la compilation du bloc par le JIT ne se déclenche jamais : piège de PPSSPPHeadless).

Rien d'autre ne change : sans appeler les événements ajoutés, le comportement est celui de la 1.20.3 officielle.

## 8. Comparaison avec l'existant (`~/ppsspp-fork` + `work/re/ppsspp/`, lu sans le modifier)

Mesuré avec le même scénario (navigation + coup) sur `~/ppsspp-fork/build-headless/PPSSPPHeadless` :
- **Il est déterministe** (2 exécutions : mêmes structures J1, même RAM) grâce à `cpu.runUntilTime` (temps émulé), mais :
  - les tranches de 16 683 µs ne sont **pas alignées sur le vblank** ; les entrées sont posées entre deux tranches : le même script donne un autre résultat qu'avec `frame.run` (X final 674,0 contre 701,5) et le décalage d'une image dépend de la phase ;
  - un aller-retour réseau par image et par lecture : navigation de 3 151 images en 30-36 s (≈ 90 i/s) contre ≈ 10 s ici (≈ 300 i/s, aucune requête par image) ; 199 images avec relevé de J1 : 3,2-3,7 s ;
  - pas d'états de sauvegarde par le WebSocket (seulement `--state`/`--save-state` en ligne de commande), pas de son, relevés lus pendant la pause seulement ;
  - ce n'est pas la source officielle (demande de l'utilisateur) ; les points d'arrêt JIT ont le même piège (`Frame()`).
- `psp_debug.py` sait piloter ce binaire en **mode repli** (`Banc.lancer(binaire=…/PPSSPPHeadless)`) : `images()` utilise alors `runUntilTime` ; `etat_*` et `audio_*` y sont indisponibles. Testé : 700 images en 8 s.
- Les scripts `nav_arcade.py`, `tournee_psp.py`, `super_bp.py` fonctionnent en temps réel ; ils peuvent être portés sur `Banc` (même WebSocket).

## 9. Limites

- Rendu **logiciel** : captures fidèles au jeu (arc additif d'Eagle visible) mais lentes pour les scènes lourdes ; transitions d'écran (triangles verts) parfois mal rendues par le rendu logiciel (artefact de capture pendant la transition, pas du jeu).
- Le son n'est pas rejoué : seulement enregistré (WAV) ; quelques échantillons saturent (286 sur 335 488 : le mixage du jeu).
- Un seul client WebSocket à la fois est prévu ; `frame.run` bloque le fil du serveur pendant l'exécution (les autres requêtes attendent).
- `cpu=interp` est 4× plus lent que `jit` ; à réserver aux comparaisons croisées.
- Points d'arrêt : `images` d'un arrêt = images terminées ; le pc est l'instruction qui va s'exécuter (exec) ou qui vient d'écrire (mémoire).
- Pas de support de l'analogique par image (`input.analog.send` du WebSocket reste utilisable en pause, non scripté par image).
- États sauvegardés : propres à la version de PPSSPP (v1.20.3 officielle) ; ils ne se chargent pas dans le fork.
- Le banc n'a pas encore été relié au banc des coups MAME (`work/banc_coups/`) : la bibliothèque est prête, la traduction « frame PSP ↔ frame CPS2 » reste à écrire.

## 10. Comparateur automatique de traces d'appels PSP / Upper MAX (`trace_appels.py`)

But : trouver sans intervention le premier endroit où le code MAX traduit d'Upper part dans une autre direction que la PSP. Le code traduit garde
l'adresse PSP dans ses labels (`psp_1c5228` = fonction PSP 0x1C5228 du module) : on journalise les ENTRÉES de ces 969 fonctions des deux côtés
pour le même coup, puis on compare.

**Côté PSP** (patch du banc) : `Banc.trace_demarrer(adresses)` pose des points d'arrêt de journal (action LOG marquée, jamais PAUSE), `trace_lire()`
renvoie `{image, pc, ra, a0-a3, sp}` dans l'ordre d'exécution (appelant = ra - 8), `trace_arreter()`. Sans arrêt ni aller-retour : 330 images avec 969 points
d'arrêt en 2 s (JIT), résultat déterministe. ⚠ Piège PPSSPP : après la pose de points d'arrêt, le cache JIT doit être vidé (`Banc.vider_cache_jit()`,
fait par `trace_demarrer` et par `point_arret_*`) sinon les blocs déjà compilés restent muets (`BreakpointManager::Update` ne retient que la dernière adresse).

**Côté Upper MAX** (MAME, fork cps2f, UNE instance, `nice`, `-video none`, nvram/cfg propres, sans `-state`, via `lance_max.sh` de la session d'intégration, lu sans le modifier) :
`lua_mame/trace_appels.lua` charge `lua/coup.lua` (entrées scriptées `COUP`, période `PER`) puis pose un `bpset` à action `printf` sur chaque label ; la console du débogueur
est vidée dans un fichier à chaque image (c'est un tampon circulaire). Pièges MAME : le `pc` du 68000 est en avance de 2 (l'adresse du point d'arrêt est donc écrite en clair),
`a7` n'est pas un symbole (la pile se lit `d@sp`), les variables `$x` ne s'initialisent pas. Table label -> adresse 68K : `prep/symboles.json` (= `banc_max17`) ; pour un banc plus ancien,
`carte_ancien()` aligne le code `$3A0000-$3B7000` relevé par MAME sur celui de banc_max17 (préfixes de 24 à 4 octets, fenêtre autour du décalage courant : ≈ 905 labels sur 969 retrouvés ; les autres sont ignorés).

**Complétude de la trace PSP** : un point d'arrêt se déclenche quand l'adresse est EXÉCUTÉE, quel que soit le chemin (jal, jalr par table de rappels, jr, branchement) et quel que soit l'appelant (moteur natif compris) ; le champ appelant (ra - 8) n'est qu'une information. Deux causes d'« appels manquants » ont été trouvées et corrigées : le cache JIT non vidé (blocs déjà compilés muets) et une fenêtre PSP plus courte que celle d'Upper (le scénario Yun finissait 150 images trop tôt : comptes PSP/Upper 2,3× d'écart faussés).

**Alignement** : mêmes entrées des deux côtés (`SCENARIOS` : une description unique traduite en masques PSP et en chaîne `COUP`), fenêtre de 330 images à partir du premier appui.
On ne garde que les fonctions du module MAX (VA 0x1B0000-0x1D9000) et, en contexte seulement, les aides moteur appelées par lui (ordre des objets et traduction des aides diffèrent).
Les objets sont comparés séparément (l'ordre des objets dans une image n'est pas le même) :
1. **joueur 1** (PSP a0 = structure J1, Upper A6 = $FF8400) : suite d'appels alignée par `difflib` ; décalage d'images mesuré ; écarts de fin de fenêtre ignorés ;
2. **autres objets** (projectiles, effets) : comptes par nom sur des blocs de 8 images (décalés du même nombre d'images), écart significatif = ≥ 3 appels ET rapport > 1,5.
Le rapport donne : fonction, image, appelant, arguments (PSP a0-a3 ; Upper d0, d1, a6, retour), 10 appels avant / après de chaque côté, fonctions appelées d'un seul côté, et la table des écarts **propres au banc testé** par rapport à un banc de référence corrigé (`--reference banc_max17`).
`equivalences_connues.json` : différences structurelles connues (rémanences d'Ingrid, variantes de l'objet effet 1c839c/1c84dc/1c849c), appliquées par défaut (`--brut` les désactive).

Usage : `trace_appels.py scenarios` ; `trace_appels.py compare ingrid_super --banc banc_max11` (≈ 1 min : une instance MAME 15 s + PPSSPP 15 s) ; sorties dans `run/trace_<scénario>_<banc>/` (`rapport.md`, `traces.json`, journaux bruts).
Scénarios : `ingrid_super` (marche + 2×QCB+LP : LP = carré ; avec HP la super est une autre), `yun_qcbp` (QCB+LP), `eagle_dp`. Un nouveau scénario = une liste `[(touches, images)]` dans `SCENARIOS`.

**Validation** (rapports dans `exemples_rapports/`) :

| cas | banc | résultat |
|---|---|---|
| super 2×QCB+P d'Ingrid | banc_max17 (corrigé, référence) | suite du joueur 1 identique, aucun objet en écart avant l'image 207 ; reste, après l'image 207, des écarts de comptage dans la fin de super (psp_1c518c, 1c50b0, 1c60a0, 1c52f8, 1c7260-1c7488 : ratios 3/8 à 4/19), à examiner : c'est la zone du « RESTE : super bloquée quand elle touche » |
| idem | banc_max11 (avant correctif) | écart propre au banc : **psp_1c5228 4/0 à l'image PSP 255** (la PSP entre dans l'état 12 de la super, Upper appelle 1c60a0 depuis 1c50b0) ; PSP-seulement : 1c5228 ×5 ; le joueur 1 diffère plus tôt (image 173, 1c6274 appelé par 4ee3c côté Upper) |
| QCB+P de Yun (onde de choc) | banc_max12 (avant correctif) | écart propre au banc : **psp_1c19e0 10/0 à l'image 23**, avec 1c19ac 10/0, 1c0dd0 10/2, 1c1854 10/2 (projectile $2D tué dès l'image suivante) |
| idem | banc_max15 et banc_max17 | pas d'écart de 1c19e0 : corrigé |

Limites : (1) banc_max15 est corrigé pour Yun, banc_max12 non (c'est le seul ancien banc avec bug Yun essayé) ; (2) Yun : le rappel +0x50 (`psp_1bc8bc`, à chaque image) est exécuté des DEUX côtés (vérifié : 191 passages PSP sur 144 images, a0 = J1, J1+0x175 = 0 donc pas de mannequin). Le joueur 1 diffère pourtant à l'image 20 sur tous les bancs : la PSP appelle le rappel +0x40 `psp_1bb944` (×4, appelant 0x57814, puis 1bba38 ×1 et 1bbdfc ×3) au début de la manipulation et Upper ne l'appelle jamais : écart RÉEL, consigné dans `equivalences_connues.json` (constats non appliqués) ; (3) une divergence hors des labels psp_ (code natif du moteur) n'est pas vue ; (4) l'alignement suppose des objets joueur identifiables (J1 = a0 / A6) : les projectiles ne sont comparés que par comptes ; (5) la PSP est tracée en entraînement contre Ken, Upper en VERSUS (MODE=1) contre Ken : les positions de départ peuvent différer de quelques pixels.
