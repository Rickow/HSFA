# MAX greffe quatre transfuges sur Alpha 3

Les quatre ajouts de *Street Fighter Alpha 3 MAX* (PSP, 2006 ; *ZERO3↑↑ « Double Upper »* au Japon) ne sont pas des créations SFA3. **Eagle, Maki et Yun sont repris presque tels quels de *Capcom vs. SNK 2* (2001)**, via la version GBA de 2002. **Ingrid vient de *Capcom Fighting Jam / Evolution* (2004)** « avec très peu de changements ». Leurs listes de coups sont donc stables et bien documentées : 5 spéciaux et 2 supers pour Eagle ; 6 spéciaux, une chaîne et 3 supers pour Maki ; 6 spéciaux et 3 supers pour Yun ; 6 spéciaux, une roulade et 3 supers pour Ingrid. Les écarts entre versions tiennent en peu de points. Le Reppukyaku de Maki passe de LK+HP ou LP+HK (GBA) à KKK (PSP), et sa perte de vitalité est disputée. Yun gagne Hiten Souryujin sur PSP, puis Raishin Mahhaken dans CFC2 seulement. Les prises et la roulade d'Ingrid changent d'entrée entre CFE, PSP et CFC2. Les wikis se contredisent surtout sur la **répartition par ISM** : Canterbury Blue, St. Andrew's Green et Union Jack Platinum chez Eagle, Tetsuzankou et Senkyutai chez Yun. Seules les tables PSP peuvent trancher. Sur la version elle-même, MAX est un **portage C natif** de Capcom, pas une émulation CPS2. Aucune frame data propre à SFA3 n'est publiée pour ces quatre persos. Le seul bug de gameplay officiellement reconnu les concernant vient de CFC2 : des coups de Bison et de R. Mika ne les touchaient pas. C'est le symptôme typique de **tables indexées par adversaire non étendues**, que HSFA doit traquer en priorité.

Conventions : commandes pour un perso tourné vers la droite. ↓↘→ = quart avant (236), ↓↙← = quart arrière (214), ←↙↓↘→ = demi-cercle avant (41236), →↘↓↙← = demi-cercle arrière (63214), →↓↘ = « Shoryuken » (623), 720 = deux tours. P/K = un poing/un pied ; PP/KK/KKK = deux ou trois boutons. ISM : X, A (appelé Z au Japon et chez SuperCombo), V. « MAX » = super réservée au niveau 3 en A-ISM. Les sources principales sont citées sous chaque tableau : StrategyWiki (liste MAX), SuperCombo (pages SFA3, souvent recopiées de FAQ GameFAQs, donc peu indépendantes) et Fandom.

## Eagle et Maki : la panoplie de CvS2, à deux nuances près

Eagle est le perso le plus simple des quatre : **aucun coup normal de commande**, il frappe toujours avec ses bâtons ([Fandom, Eagle](https://streetfighter.fandom.com/wiki/Eagle)). Sa liste est identique à celle de CvS2, mêmes commandes comprises ([Fandom, liste CvS2](https://streetfighter.fandom.com/wiki/List_of_Moves_in_Capcom_vs._SNK_2) ; [Game Watch, 2001](https://game.watch.impress.co.jp/docs/20010907/cvs2_wc.htm)). Le seul vrai point de friction est la répartition par ISM, où les trois wikis divergent sur trois coups.

| Coup (JP) | Commande PSP | ISM (SuperCombo / StrategyWiki / Fandom) | Propriétés |
|---|---|---|---|
| Fool On Pile (prise) | près, ←/→ + PP | XAV | « Pile of Fools » dans CvS2 |
| Percussion Fool (prise) | près, ←/→ + KK | XAV | « Fool Percussion » dans CvS2 |
| Prise aérienne | en l'air, ←/→ + PP ou KK | XAV | — |
| Manchester Black (マンチェスターブラック) | ↓↙← + P | XAV / XAV / XAV | LP tourne sur place, MP/HP avancent ; brève invulnérabilité des jambes au début |
| Canterbury Blue (カンタベリーブルー) | ↓↘→ + P, bouton maintenable | **XAV / AV / XAV** | garde automatique : LP haute, MP moyenne, HP basse (SuperCombo SFA3 : « toutes hauteurs ») ; arrête les projectiles, pas les supers ; seule la LP fait chuter |
| Oxford Red (オックスフォードレッド) | ←↙↓↘→ + K | XAV | glissade puis rafale d'estocs, plus longue avec la force |
| Liverpool White (リバプールホワイト) | ↓↙← + K | XAV | saut puis coup en overhead, plus haut et plus long avec la force |
| St. Andrew's Green (セントアンドリューグリーン) | →↓↘ + P | **XAV / AV / AV** | swing ascendant qui renvoie les projectiles normaux (pas ceux des supers), angle selon le bouton |
| Manchester Gold (super) | ↓↙←↓↙← + P | X A | 6 / 9 / 13 coups (Lv1/2/3) ; le Lv3 finit en embrochant l'adversaire |
| Union Jack Platinum (super) | ↓↘→↓↘→ + P | **A / A / XA** | 9 / 11 / 17 coups ; finit sur un Oxford Red renforcé |

Sources : [StrategyWiki, MAX/Moves](https://strategywiki.org/wiki/Street_Fighter_Alpha_3_MAX/Moves) ; [SuperCombo, SFA3/Eagle](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Eagle) ; [Fandom, liste SFA3 A-G](https://streetfighter.fandom.com/wiki/List_of_moves_in_Street_Fighter_Alpha_3_A-G) ; [Fandom, Canterbury Blue](https://streetfighter.fandom.com/wiki/Canterbury_Blue) ; [Fandom, St. Andrew's Green](https://streetfighter.fandom.com/wiki/St._Andrew%27s_Green).

Le désaccord sur Union Jack Platinum se tranche presque par la logique. En X-ISM, un perso n'a **qu'un seul super** ([Fandom, SFA3](https://streetfighter.fandom.com/wiki/Street_Fighter_Alpha_3)). Le tableau Fandom, qui donne les deux supers d'Eagle en X, viole donc sa propre règle, et Manchester Gold, seul point commun aux trois sources, est presque sûrement le super X. Canterbury Blue (2 sources sur 3 : disponible en X) et St. Andrew's Green (2 sur 3 : absent en X) restent de vrais doutes. Les références chiffrées n'existent que pour CvS2 : Canterbury Blue maintenable de 13 à 73 images, St. Andrew's Green démarrant en 14 images, Liverpool White en 36 à 41, invulnérabilité totale des supers de 8, 14 ou 22-23 images selon le niveau ([SuperCombo, CvS2/Eagle](https://wiki.supercombo.gg/w/Capcom_vs_SNK_2/Eagle)). Ces valeurs donnent des ordres de grandeur pour contrôler le portage, pas des valeurs à reproduire.

Maki est plus riche : un coup normal de commande, une chaîne à fin de projection, des spéciaux à suites et un super de projection en 720. Sur l'ISM, les trois wikis sont pour une fois **unanimes** : tout en XAV sauf Bushin Gouraiha (X, A), Tesshinhou (A) et Ajaratengu (A) ([SuperCombo, SFA3/Maki](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Maki) ; [StrategyWiki](https://strategywiki.org/wiki/Street_Fighter_Alpha_3_MAX/Moves) ; [Fandom, liste I-Z](https://streetfighter.fandom.com/wiki/List_of_moves_in_Street_Fighter_Alpha_3_I-Z)).

| Coup (JP) | Commande PSP | ISM | Propriétés |
|---|---|---|---|
| Shishigari (prise) | près, ←/→ + PP | XAV | poing au ventre puis coup de pied ; portée de prise longue (60 px dans CvS2) |
| Hiza Kamashi (prise) | près, ←/→ + KK | XAV | — |
| Prise aérienne « Head Bomber » | en l'air, ←/→ + PP (StrategyWiki : PP ou KK) | XAV | — |
| Hiji Otoshi (commande) | en saut, ↓ + MP | XAV | coupe l'élan, chute verticale ; garde haute |
| Bushin Gokusaken (chaîne) | LP, MP, HP, HK ; fin en projection LP, MP, HP, ↓+HP | XAV | doit partir d'un LP debout ; peut rater les accroupis ou sortir de portée |
| Genko (拳コ) | ↓↘→ + P | XAV | crochet avançant ; démarrage identique aux trois forces, le bouton règle distance et dégâts |
| Hayagake (疾駆け) | ↓↘→ + K, puis K | XAV | LK arrêt (急停止), MK glissade basse Kage Sukui, HK attaque haute Kubikari |
| Saka Hayagake (逆疾駆け) | ↓↙← + K, puis K | XAV | LK arrêt, MK arrêt + saut avant, HK arrêt + saut arrière |
| Tengu Daoshi (天狗倒し) | en l'air, près, ←↙↓↘→ + P | XAV | projection aérienne (adversaire en l'air), faisable en « instant air » (412369+P) |
| Hassoukyaku (八艘脚) | en l'air, contre le bord, ↓↙← + P ou K | XAV | LP rebond ; MP/HP plongeon + saisie (**adversaire debout seulement**) ; LK accroche + chute ; MK/HK pied plongeant |
| Reppukyaku (烈風脚) | **KKK** (GBA : LK+HP ou LP+HK) | XAV | tonfa planté, rotation qui frappe des deux côtés ; coût en vitalité disputé |
| Bushin Gouraiha (武神剛雷破, super) | ↓↘→↓↘→ + P | X A | 5 / 6 / 8 coups |
| Tesshinhou (鉄心崩, super) | ↓↘→↓↘→ + K, **puis K** (disputé) | A | 3 / 4 / 8 coups ; le Lv3 finit en Genko |
| Ajaratengu (戯天狗, super) | 720 + P, au sol ou en l'air | A | super de projection, rebonds sur les murs, fin en Head Bomber ; plus de dégâts en l'air |

Sources : [SuperCombo, SFA3/Maki](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Maki) ; [StrategyWiki](https://strategywiki.org/wiki/Street_Fighter_Alpha_3_MAX/Moves) ; [Fandom, Reppukyaku](https://streetfighter.fandom.com/wiki/Reppukyaku) ; [Fandom, Hassoukyaku](https://streetfighter.fandom.com/wiki/Hassoukyaku) ; noms japonais de la liste CvS2 de [Game Watch](https://game.watch.impress.co.jp/docs/20010907/cvs2_wc.htm).

Trois points restent ouverts chez Maki. Pour **Tesshinhou**, SuperCombo et Fandom exigent une seconde pression de K après la course ; StrategyWiki ne note que la commande ([Fandom, Tesshinhou](https://streetfighter.fandom.com/wiki/Tesshinhou)). Pour **Hayagake**, SuperCombo décrit les suites MK et HK comme des « hitgrab », là où Fandom et CvS2 parlent d'une glissade et d'un coup de pied ([Fandom, Hayagake](https://streetfighter.fandom.com/wiki/Hayagake)). Pour **Reppukyaku**, dans CvS2 le coup coûte 600 points de vitalité à Maki (environ 4,3 %) et ne sort pas à vie nulle ([SuperCombo, CvS2/Maki](https://wiki.supercombo.gg/w/Capcom_vs_SNK_2/Maki)). Une page japonaise, vue seulement en extrait, dit que la GBA garde cette perte et que la PSP la supprime ([ゲームカタログ@Wiki](https://w.atwiki.jp/gcmatome/pages/3260.html)). SuperCombo SFA3 va dans le même sens (« She doesn't lose any life for using this unlike in CVS2 »), mais StrategyWiki laisse entendre le contraire ([StrategyWiki, Alpha/Maki](https://strategywiki.org/wiki/Street_Fighter_Alpha/Maki)). La prépondérance des sources penche pour **aucune perte sur PSP**. Enfin, Fandom affirme que Tengu Daoshi et Reppukyaku sont « introduits dans MAX », ce que la liste CvS2 de 2001 dément ([Fandom, Tengu Daoshi](https://streetfighter.fandom.com/wiki/Tengu_Daoshi)).

## Yun et Ingrid : un Yun de CvS2, pas de 3S, et une Ingrid de CFJ

Le Yun de MAX est celui de **CvS2**, pas celui de *3rd Strike*. Il garde Senkyutai (↓↘→+K) là où 3S a Nishou Kyaku (623+K). You-hou devient un super MAX en ↓↙←×2 au lieu d'un Super Art en ↓↘→×2. Genei-Jin n'existe pas ([Fandom, Senkyutai](https://streetfighter.fandom.com/wiki/Senkyutai) ; [SuperCombo, 3S/Yun](https://wiki.supercombo.gg/w/Street_Fighter_3:_3rd_Strike/Yun) ; [Fandom, You Hou](https://streetfighter.fandom.com/wiki/You_Hou)). Même l'animation de You-hou suit CvS2 : bras avant plié en revers, au lieu de tendu dans SF3. Aucune commande n'est en charge.

| Coup (JP) | Commande PSP | ISM (StrategyWiki / SuperCombo / Fandom) | Propriétés |
|---|---|---|---|
| Hiji Geki (prise) | près, ←/→ + PP | XAV | « Chugeki » dans CvS2 |
| Monkey Flip (prise) | près, ←/→ + KK | XAV | — |
| Air Monkey Flip | en l'air, ←/→ + KK | XAV | — |
| Senpuu Kyaku (commande) | → + MK | XAV | overhead dans CvS2 |
| Raigeki Shuu (雷撃蹴, commande) | en l'air, ↘ + K | XAV | dive kick |
| Kuu Rensui (commande) | en l'air, LP puis → + HP | XAV | « Kurenso » dans CvS2 |
| Tetsuzankou (鉄山靠) | →↓↘ + P | **AV / XAV / XAV** | roulade avant + coup de dos ; dans CvS2, MP et HP passent sous les projectiles |
| Zesshou-hohou (絶招歩法) | ↓↘→ + P | XAV | bond poing tendu, plus loin avec la force |
| Senkyutai (穿弓腿) | ↓↘→ + K | **XV / XAV / XV** | envol en biais, pied en avant |
| Kobokushi (虎撲子) | ↓↙← + P | XAV | double paume après préparation ; annule les projectiles (CvS2) |
| Fake Kobokushi | ↓↙← + PP | XAV | la préparation seule |
| Zenpou-tenshin (前方転身) | →↘↓↙← + K | XAV | saisie imparable, **0 dégât**, passe derrière l'adversaire |
| Sourai-Rengeki (槍雷連撃, super) | ↓↘→↓↘→ + P | X A | 4 / 6 / 8 coups |
| You-hou (揚炮, super) | ↓↙←↓↙← + P | A, MAX | 3 coups, finit en uppercut lanceur |
| Hiten Souryujin (飛天双龍陣, super) | en l'air, ↓↙←↓↙← + K | A, MAX | Yang apparaît et frappe avec Yun ; **PSP et CFC2, pas GBA** |
| Raishin Mahhaken (雷震魔破拳, super) | ↓↘→↓↘→ + K | A | **CFC2 seulement** (sources communautaires) |

Sources : [StrategyWiki](https://strategywiki.org/wiki/Street_Fighter_Alpha_3_MAX/Moves) ; [SuperCombo, SFA3/Yun](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Yun) ; [Fandom, liste I-Z](https://streetfighter.fandom.com/wiki/List_of_moves_in_Street_Fighter_Alpha_3_I-Z) ; [Fandom, Hiten Souryujin](https://streetfighter.fandom.com/wiki/Hiten_Souryujin) ; [SuperCombo, CvS2/Yun](https://wiki.supercombo.gg/w/Capcom_vs_SNK_2/Yun).

Les désaccords de Yun sont plus gênants que ceux d'Eagle, car aucune règle système ne les arbitre. Sur **Senkyutai**, StrategyWiki et Fandom s'accordent (absent en A-ISM). Sur **Tetsuzankou**, les trois sources donnent trois réponses. L'entrée de la feinte est stable pour SFA3 (↓↙← + PP), mais Fandom écrit PPP pour CvS2 ([Fandom, CvS2](https://streetfighter.fandom.com/wiki/List_of_Moves_in_Capcom_vs._SNK_2)). Hiten Souryujin est absent de la page SuperCombo SFA3. C'est une omission : Fandom note qu'il manquait sur GBA alors qu'il apparaît dans la fin de Yun, et la PSP le rétablit.

Ingrid est le seul ajout sans passé CvS2. Ses **spéciaux et leurs commandes sont identiques entre CFE et MAX** ([StrategyWiki, CFE/Moves](https://strategywiki.org/wiki/Capcom_Fighting_Evolution/Moves)). Les noms « Sun Strike » et « Meteor Smash » n'apparaissent dans **aucune** liste consultée, y compris l'infobox Fandom qui recense ses coups de CFAS à SF6 ([Fandom, Ingrid](https://streetfighter.fandom.com/wiki/Ingrid)). Ce ne sont pas des coups d'Ingrid.

| Coup (JP) | Commande PSP | ISM | Propriétés |
|---|---|---|---|
| Suncrack (prise) | près, ←/→ + PP | XAV | lévitation puis crochet (CFE : LP+LK) |
| Light Punish (prise) | près, ←/→ + KK | XAV | martelable pour plus de coups (CFE : LP+LK) |
| Prise aérienne | en l'air, ←/→ + PP | XAV | — |
| Sunbright (commande) | → + MP | XAV | frappe de lumière, touche en mid dans SFA3 |
| Easy Step (commande) | → + MK | XAV | petit bond avec coup de pied |
| Little Lag (commande) | ↘ + MK | XAV | glissade d'un peu moins d'un demi-écran |
| Wrap Around (roulade) | MP+HK **ou** MK+HP | **X V** (Fandom : MP+HK en X, MK+HP en V) | roulade de CFJ qui passe derrière l'adversaire, images rémanentes |
| Sun Shot (サンシュート) | ↓↘→ + P | XAV | projectile en arc, portée selon le bouton |
| Sun Rise (サンライズ) | ↓↘→ + K | XAV | pirouette de 6 coups, finit en Sun Arch |
| Sun Arch (サンアーチ) | →↓↘ + K | XAV | le « DP » d'Ingrid, salto avec coup de pied |
| Sun Upper (サンアッパー) | ↓↙← + P | XAV | contre haut/mid qui lance en l'air ; **perd contre les projectiles** |
| Sun Lower (サンローワー) | ↓↙← + K | XAV | contre bas qui lance en l'air ; perd contre les projectiles |
| Sun Dive (サンダイブ) | en l'air, ↓↙← + K | XAV | LK vrille vers le bas (jusqu'à 4 coups), MK/HK pieds tournoyants |
| Sunburst (サンバースト, super) | ↓↘→↓↘→ + P | A | orbe lent qui explose à une distance fixée par le bouton, 5 coups |
| Sunshine (サンシャイン, super) | ↓↙←↓↙← + K | A | 4 / 5 / 7 coups, finit sur l'animation d'Easy Step |
| Sun Delta (サンデルタ, super) | ↓↙←↓↙← + P | X ; A au niveau 3 | super de saisie par mur de lumière ; portée selon le bouton |

Sources : [StrategyWiki](https://strategywiki.org/wiki/Street_Fighter_Alpha_3_MAX/Moves) ; [SuperCombo, SFA3/Ingrid](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Ingrid) ; [Fandom, Wrap Around](https://streetfighter.fandom.com/wiki/Wrap_Around) ; [Fandom, Sun Delta](https://streetfighter.fandom.com/wiki/Sun_Delta) ; [Fandom, Light Punish](https://streetfighter.fandom.com/wiki/Light_Punish).

La page Fandom de Sun Delta range le coup parmi les supers « A-ISM only ». C'est une contradiction interne de Fandom : son propre tableau, StrategyWiki et SuperCombo donnent tous X + A (MAX). SuperCombo souligne surtout que le portage depuis CFJ s'est fait « avec très peu de changements » : certaines techniques de CFJ marchent encore, comme l'accroupi HP qui passe sous les projectiles ([SuperCombo, SFA3/Ingrid](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Ingrid)). Les boîtes de collision et les propriétés héritées de CFJ sont donc dans les données PSP, et un portage fidèle doit les garder. Pour Yun comme pour Ingrid, **aucune frame data SFA3 n'est publiée**. Seules existent des valeurs CvS2 (Yun) et 3S, utiles pour l'ordre de grandeur relatif, comme Tetsuzankou LP bien plus rapide que HP ([SuperCombo, CvS2/Yun](https://wiki.supercombo.gg/w/Capcom_vs_SNK_2/Yun)).

## Quatre versions, une poignée de différences documentées

Les ajouts naissent sur **GBA** (Crawfish, 2002, *ZERO3↑*), qui reprend Eagle, Maki et Yun de CvS2 ([StrategyWiki, SFA3 GBA](https://strategywiki.org/wiki/Street_Fighter_Alpha_3_(Game_Boy_Advance)) ; [FAQ Capcom JP](https://www.capcom.co.jp/support/faq/platform_psp_stz_036998.html)). La **PSP** les reprend et ajoute Ingrid. **CFC2** (Upper NAOMI) les rend jouables en option le 6 août 2025 (heure du Pacifique, donc le 7 août au Japon). **CFE** n'entre dans la comparaison que pour Ingrid, dont il est le jeu d'origine. Le tableau ci-dessous ne retient que les écarts sourcés.

| Perso | GBA (2002) | PSP MAX (2006) | CFE (2004) | CFC2 (2025) |
|---|---|---|---|---|
| Tous | contrôle à 4 boutons (moyens via gâchette + bouton) ; prises à l'ancienne (coup moyen ou fort + direction) ; pas de fin propre ; ZERO Counter non différencié par ISM | prises PP/KK ; fin et histoire propres ; ZERO Counter différencié par ISM | — | option « Additional Characters », interdits en ligne ; bug Bison/Mika corrigé en 1.0.4 |
| Eagle | même liste que PSP | référence | absent | aucun changement documenté |
| Maki | Reppukyaku LK+HP ou LP+HK, avec perte de vitalité (extrait) | Reppukyaku KKK, sans perte (majorité des sources) | absente | aucun changement documenté |
| Yun | **pas de Hiten Souryujin** | Hiten Souryujin rétabli | sans objet (le Yun de MAX vient de CvS2) | **+ Raishin Mahhaken** (communautaire) |
| Ingrid | absente | prises ←/→+PP/KK ; Wrap Around MP+HK ou MK+HP (X, V) ; supers à niveau variable en A, Sun Delta seule en X | prises LP+LK ; roulade MP+MK ; Sunburst niv. 1, Sunshine niv. 2, Sun Delta niv. 3 | roulade renommée **Love Roll, en KKK** |

Sources : [StrategyWiki](https://strategywiki.org/wiki/Street_Fighter_Alpha_3_MAX/Moves) ; [Fandom, SFA3](https://streetfighter.fandom.com/wiki/Street_Fighter_Alpha_3) ; [Wikipédia JA](https://ja.wikipedia.org/wiki/ストリートファイターZERO) ; [Nintendo World Report, test GBA](https://nintendoworldreport.com/review/4122/street-fighter-alpha-3-game-boy-advance) ; [StrategyWiki, CFE/Moves](https://strategywiki.org/wiki/Capcom_Fighting_Evolution/Moves) ; [SuperCombo, SFA3/Ingrid](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Ingrid) ; [EventHubs, août 2025](https://www.eventhubs.com/news/2025/aug/06/capcom-collection-patch-notes/).

Le côté CFC2 mérite de la prudence. Les notes officielles d'août 2025 n'annoncent **aucun changement de coups** ([EventHubs, août 2025](https://www.eventhubs.com/news/2025/aug/06/capcom-collection-patch-notes/)). Le Raishin Mahhaken de Yun ne repose que sur une modification anonyme de StrategyWiki (11 juin 2026) et sur un message X lu seulement en résumé ([historique StrategyWiki](https://strategywiki.org/w/index.php?title=Street_Fighter_Alpha_3_MAX/Moves&action=history) ; [X, @rouken_miasuke](https://x.com/rouken_miasuke/status/1955284590156824609)). Le même message affirme que l'option n'ajoute que quatre persos, sans faire du jeu un MAX complet. Selon lui, CFC2 garde des défauts « hérités de la PSP », dont la détection de Head Press et de Sardine's Beach Special sur Yun et Ingrid. Il ajoute qu'une particularité de la fausse prise, qui ne peut plus être maintenue sur GBA et PSP, n'est pas reprise. Un autre message soutient au contraire que l'Upper de CFC2 « devient MAX » ([X, @Mekikung](https://x.com/Mekikung/status/1951741112475099353)). Aucune de ces affirmations n'est vérifiée.

Une seule différence de commande GBA → PSP est donc établie pour Eagle, Maki et Yun : le Reppukyaku. Aucune liste GBA complète n'a toutefois pu être lue. Des écarts plus fins (dégâts, frames, ISM de Tetsuzankou sur GBA) ne sont donc pas exclus.

## MAX elle-même : un portage C natif, riche en modes, pauvre en documentation

Capcom développe et édite *MAX* sans sous-traitant nommé ; Crawfish n'est crédité que pour la GBA ([Wikipédia EN](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_3)). Le jeu est montré au TGS 2005 sous le titre *Zero 3 Double Upper* ([GameSpot, TGS 2005](https://gamespot.com/articles/tgs-2005-street-fighter-zero-3-double-upper-hands-on/1100-6133441/)). Il sort le **19 janvier 2006 au Japon**, le 7 février aux États-Unis, le 24 février en Australie et le 10 mars en Europe ([Wikipédia EN](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_3)). Le titre japonais officiel, *ストリートファイターZERO3↑↑*, se lit « ダブルアッパー ». Il prolonge le « ↑ » de l'Upper NAOMI et de la GBA : MAX est la deuxième révision « Upper ». Aucune source officielle n'explique ce titre ; c'est une déduction. Capcom présente le jeu comme la *Zero 3* d'arcade « à laquelle on a ajouté divers modes et persos jouables » ([FAQ Capcom, différences](https://www.capcom.co.jp/support/faq/platform_psp_stz_036999.html)). StrategyWiki y voit plutôt une mise à niveau de la GBA ([StrategyWiki](https://strategywiki.org/wiki/Street_Fighter_Alpha_3_MAX)).

L'analyse de l'EBOOT par le projet tranche la question technique : **MAX n'émule pas le CPS2 et ne recompile pas le 68000**. L'Anthology accède des centaines de milliers de fois aux registres 68K gardés en mémoire ; l'EBOOT de MAX ne le fait que 1 113 fois, suit l'ABI C standard et ne contient aucune chaîne d'émulateur. La structure reste pourtant arcade : aire 384×224, tables de sauts pilotées par des octets de routine, virgule fixe 16.16. L'hypothèse la plus probable est une traduction des sources 68K en C. Les listes de coups sont des textures **GBIX/PVRT** de format Dreamcast, et le World Tour suit le modèle de la Dreamcast : les données descendent de la branche DC/NAOMI (dépôt HSFA, `docs/MAX-Etude-Contenu-Persos.md` §1-§6 ; [Wikipédia JA](https://ja.wikipedia.org/wiki/ストリートファイターZERO)).

Côté contenu, Capcom revendique **tous les persos de l'arcade et des versions console**, plus les ajouts de CvS2 et Ingrid ([FAQ Capcom, persos](https://www.capcom.co.jp/support/faq/platform_psp_stz_036998.html)). Le décompte varie : 38 noms dans la table de l'EBOOT, 39 selon Wikipédia, 40 selon IGN. Dans l'EBOOT, les IDs prolongent ceux de l'Anthology : `$26` Eagle, `$27` Maki, `$28` Yun, `$29` Ingrid. Le code de Juni y est un clone de celui de Juli (dépôt, `docs/MAX-Etude-Contenu-Persos.md` §2). Les ajouts n'ont **pas de décor propre** : Yun prend celui de Fei Long, Maki celui de Guy, Eagle celui de Birdie, et Ingrid n'en a aucun ([Wikipédia JA](https://ja.wikipedia.org/wiki/ストリートファイターZERO)). Capcom liste quinze modes, dont trois nouveaux face aux versions PS et DC : Variable Battle (tag à deux), R. Dramatic Battle (un joueur contre deux CPU) et VS 100 Kumite. S'y ajoutent Final Battle (boss final d'emblée), Free Battle et un mode réseau ad hoc de 2 à 8 PSP, sans jeu en ligne ([FAQ Capcom, modes](https://www.capcom.co.jp/support/faq/platform_psp_stz_036997.html)). L'I-ISM n'existe que dans le World Tour ([Wikipédia EN](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_3)). La musique passe en flux ATRAC3, et les voix en banques PPHD/VAG.

La réputation de fidélité porte sur l'image, pas sur le comportement. Wikipédia parle d'une conversion « near-faithful […] with all frames and sprites intact » ([Wikipédia EN](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_3)) ; GameSpot dit le jeu intact « right down to the last pixel » ([GameSpot](https://www.gamespot.com/reviews/street-fighter-alpha-3-max-review/1900-6143720/)) ; IGN regrette surtout la croix directionnelle ([IGN](https://www.ign.com/articles/street-fighter-alpha-3-max)). Le seul bug **reconnu par Capcom** est la non-reconnaissance des Memory Stick de 4 Go ou plus, jamais corrigée ([FAQ Capcom](https://www.capcom.co.jp/support/faq/platform_psp_stz_036995.html)). Une critique d'utilisateur japonaise, isolée et lue seulement en extrait, affirme que la PSP n'a plus le **着キャン** (annulation à l'atterrissage), ce qui casserait les jongles ([pspmk2.net](http://pspmk2.net/soft/bact/zero3.html)). Selon TCRF, vu seulement en extrait, les différences régionales sont cosmétiques (logo, ™, couleur de « Press Start ») et la recherche de contenu inutilisé reste à faire ([TCRF](https://tcrf.net/Street_Fighter_Alpha_3_MAX_(PlayStation_Portable))). Particularité de données : les listes de coups de Sakura et des quatre ajouts sont **en japonais même dans les fichiers européens**. Les dialogues anglais d'Ingrid sont, eux, notoirement mal traduits ([SuperCombo, Ingrid](https://wiki.supercombo.gg/w/Street_Fighter_Alpha_3/Ingrid)).

La rétro-ingénierie publique est quasi inexistante. Le seul travail extérieur trouvé est un patch 16:9 (Python, trois régions). Son README note qu'un UMD commercial contient l'ELF **non chiffré** sous `PSP_GAME/SYSDIR/BOOT.BIN`, et que les dumps EU et JP reconnus sont en v1.01 ([Rickow/SFA3max-PSP-widescreen](https://github.com/Rickow/SFA3max-PSP-widescreen)). La documentation la plus complète est celle du dépôt HSFA (`tools/max/`). Elle couvre le conteneur `plXX_e.pac` à 9 entrées, un décodeur de tuiles validé sur 698 180 tuiles sur 698 180, les palettes, GBIX/PVRT et PPHD/VAG, ainsi qu'un module de code contigu par perso, d'environ 95 Ko pour les quatre ajouts. L'art PSP y est établi **identique au pixel** à celui d'Upper, à une permutation de palette `i → 16−i` près. Trois entrées `.pac`, [5], [6] et [7], restent non décodées (dépôt, `tools/max/README.md` ; `docs/MAX-Etude-Contenu-Persos.md` §3-§8). Du côté de CFC2, l'exécutable est protégé par Enigma Protector, ce qui a fait abandonner un projet de rétro-portage ([arcade-projects](https://www.arcade-projects.com/threads/capcom-fighting-collection-2-street-fighter-zero-3-upper-sega-naomi-p-o-r-t.34097/page-3)). CFC2 ne peut donc servir que d'oracle de jeu, pas de source de code.

## Ce que HSFA doit vérifier dans les données PSP

Le correctif CFC2 1.0.4 du 10 septembre 2025 est l'indice le plus utile pour le projet. Le Head Press et le Somersault Skull Diver de Bison ne touchaient pas Eagle, Maki, Yun ni Ingrid, et la Sardine Beach Special de R. Mika ne les touchait pas correctement. Le même patch a mis à jour « certain victory text for Juni » ([EventHubs, sept. 2025](https://www.eventhubs.com/news/2025/sep/10/capcom-collection-patch-notes/)). Les trois coups sont des attaques à cible scriptée, et les quatre persos sont touchés ensemble. Tout indique des **tables indexées par l'ID de l'adversaire**, dimensionnées pour l'ancien roster. HSFA se trouve exactement dans la même situation que Capcom en 2025 : greffer des persos PSP dans un moteur Upper. Le tableau suivant classe les vérifications par ordre de priorité.

| Priorité | Point à vérifier | Pourquoi | Comment trancher |
|---|---|---|---|
| 1 | Tables par adversaire de Bison (Head Press, Skull Diver) : la table Upper « 3 × 40 » doit couvrir jusqu'à `$29` | bug CFC2 officiel | étendre la table, puis tester les deux coups contre `$26`-`$29` |
| 1 | Sardine Beach Special de R. Mika : chercher une table de positions ou de hauteurs par adversaire | bug CFC2 officiel ; le dépôt a déjà un test « jauge forcée » | même test contre les quatre persos |
| 1 | Toutes les autres prises et supers de saisie (Zangief, Sodom, T. Hawk, Hassoukyaku, Ajaratengu, Zenpou-tenshin, Sun Delta…) | même famille de risque, non citée par Capcom | balayage systématique 38 × 4 |
| 1 | Citations de victoire par adversaire (Juni, et Juli dont le code est cloné) | patch CFC2 sur Juni | lire `winXX_e.pac` et la table perso → citation |
| 2 | ISM d'Eagle : Canterbury Blue (X ?), St. Andrew's Green (X ?), Union Jack Platinum (X ?) | trois wikis en désaccord | table ISM/commandes du module MIPS d'Eagle (sans doute dans les entrées `.pac` [5]-[7] ou le module de code) |
| 2 | ISM de Yun : Tetsuzankou (X ?), Senkyutai (A ?) | trois réponses différentes | même méthode ; contrôle en PPSSPP |
| 2 | Wrap Around d'Ingrid : MP+HK et MK+HP valent-ils dans les deux ISM, ou un par ISM (X et V) ? Absente en A ? | Fandom contre StrategyWiki et SuperCombo | décodeur de commandes PSP |
| 2 | Reppukyaku : entrée KKK (pas la combinaison GBA) et **absence de perte de vitalité** | sources contradictoires | lire le code du coup ; mesurer la vie en PPSSPP |
| 2 | Tesshinhou : seconde pression de K obligatoire ? | SuperCombo/Fandom contre StrategyWiki | code de l'état « course » |
| 3 | Canterbury Blue : une hauteur de garde par bouton, ou garde à toutes hauteurs | SuperCombo SFA3 contre Fandom et CvS2 | données de garde automatique |
| 3 | Raishin Mahhaken absent du Yun PSP, ou présent mais inutilisé ; sprites de Yang pour Hiten Souryujin | super CFC2 seulement ; Yang requis | chercher l'animation dans `pl28_e.pac` |
| 3 | Restes CFJ d'Ingrid (accroupi HP sous les projectiles) ; Sun Upper/Lower qui perdent contre les projectiles ; lueurs additives | « très peu de changements depuis CFJ » | boîtes de collision PSP, à conserver |
| 3 | ZERO Counter différencié par ISM pour les quatre (corrigé par la PSP face à la GBA) | écart GBA/PSP documenté | table Alpha Counter par perso et par ISM |
| 3 | Table perso → décor (`$26`-`$28` : Birdie, Guy, Fei Long ; `$29` : aucun) et fins individuelles | oracle de Wikipédia JA | à reporter dans les tables Upper |
| 4 | Absence de 着キャン sur PSP | une seule source, faible | sans enjeu pour le moteur Upper du port, mais à noter si un comportement des quatre persos en dépend |
| 4 | Fausse prise : « ne peut plus être maintenue » sur GBA/PSP | message X non vérifié | observer en PPSSPP avant tout choix |

Pour tous ces points, la règle d'arbitrage est la même : la PSP fait foi, ni la GBA ni CFC2. Les éléments propres à la GBA (prises au coup moyen ou fort, Reppukyaku à deux boutons) et à CFC2 (Love Roll en KKK, Raishin Mahhaken) ne doivent pas apparaître dans le port. Les valeurs CvS2 de SuperCombo restent une grille qualitative, utile pour repérer un écart grossier : invulnérabilité des supers qui croît avec le niveau, Genko à frames identiques pour les trois forces, portée du Tengu Daoshi qui diminue avec la force.

## Conclusion

Le vrai risque pour HSFA n'est pas dans les listes de coups : elles sont stables depuis CvS2 et CFJ, et les données PSP tranchent tous les désaccords qui restent. Le risque est dans les **interactions avec le roster existant**. Capcom a livré en 2025 une intégration de ces quatre persos dans le moteur Upper. Il lui a fallu un patch pour que deux coups de Bison et une prise de R. Mika les touchent, et retoucher des répliques de Juni. Le premier bug est déjà identifié dans le dépôt, avec la table Bison « 3 × 40 ». Le deuxième désigne R. Mika. Le troisième désigne les citations de victoire. Un balayage croisé des 38 persos contre `$26`-`$29` vaut donc davantage qu'une vérification coup par coup des listes.

Deuxième enseignement : MAX étant un portage C, sa « fidélité à l'arcade » ne vaut que pour l'image. Le comportement des quatre ajouts n'a jamais été mesuré publiquement : aucune frame data SFA3, aucun inventaire de bugs PSP, page TCRF non lue. La documentation HSFA est déjà la référence la plus complète sur les données de MAX. Les décisions sur les points disputés (ISM d'Eagle et de Yun, vitalité du Reppukyaku, fausse prise) doivent venir du décodage des entrées `.pac` [5]-[7] et de mesures en PPSSPP, puis être consignées comme acquis du projet. Les wikis communautaires, sur ces points précis, se recopient entre eux.
