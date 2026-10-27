# Cave loader cross-stage — design prêt à assembler + plan de test (2026-06-28)

État : pipeline 100% reversé, package Upper inséré dans l'ISO `SFA Anthology - Hyper Loader Test (USA).iso`
comme **fichier AFS 553** (off_rel 0x10000, 65 Ko compressé MWo3). Reste = le cave + valider le timing (test).

## Adresses clés (toutes confirmées)
- `FUN_154b00(a0=0, a1=index, a2=buffer)` @ **0x154b00** — lit fichier AFS (synchrone).
- `FUN_148698(a0=src, a1=dst)` @ **0x148698** — décompresse MWo3.
- bank ptr (repoint) = **0x1dc2e4** (struct BG +0x34) ; buffers tilemap = **0xba0000/0xba4000/0xba8000/0xbac000**.
- RAM libre : décompression → **0x1580000** ; scratch lecture → **0x1600000**.
- file_ref : **553** = package Upper ; **546** = e546 (bank zero9, pour le test de validation).
- Hook par-frame : site **0x1d1848** = `jal 0x1d18a0` (0x0C074628) dans le drawer ; le remplacer par `jal cave`.
- Cave : **0x1c0400** (après la zone arcade 0x1c0000-0x1c0350, pour coexister/éviter collision).

## ⚠️ Point sensible à TESTER (pourquoi pas livré comme pnach fini)
`FUN_154b00` est un **load disque SYNCHRONE**. L'appeler depuis le hook drawer (mid-frame) peut bloquer/glitcher.
→ À valider : soit ça passe (load one-shot, rare), soit il faut hooker un point HORS rendu (ex. après le
montage du stage : `FUN_22daa4`/`FUN_1c9290`) ou pré-charger à un moment sûr. C'est LE truc à régler ensemble.

## TEST 1 — validation pipeline (cave one-shot, charge e546 = doit être IDENTIQUE)
But : prouver load+décompresse+repoint SANS rien changer visuellement. Si le jeu est identique → pipeline OK.
```asm
; --- hook: a 0x1d1848, remplacer "jal 0x1d18a0" par "jal 0x1c0400" (0x0C070100) ---
; --- cave @0x1c0400 ---
        addiu sp, sp, -0x40
        sw    ra, 0x00(sp)
        sw    a0, 0x04(sp)         ; preserver les args du drawer
        sw    a1, 0x08(sp)
        sw    a2, 0x0c(sp)
        sw    a3, 0x10(sp)
        lui   t0, 0x001c
        lbu   t1, 0x04f0(t0)       ; guard @0x1c04f0
        bnez  t1, done
        nop
        li    t1, 1
        sb    t1, 0x04f0(t0)
        ; FUN_154b00(0, 546, 0x1600000)
        li    a0, 0
        li    a1, 546
        lui   a2, 0x0160
        jal   0x154b00
        nop
        ; FUN_148698(0x1600000, 0x1580000)
        lui   a0, 0x0160
        lui   a1, 0x0158
        jal   0x148698
        nop
        ; repoint bank: *0x1dc2e4 = 0x1580000  (e546 decompresse = base bank index 0)
        lui   t2, 0x0158          ; 0x01580000
        lui   t3, 0x001d
        ori   t3, t3, 0xc2e4      ; 0x1dc2e4
        sw    t2, 0x0000(t3)
done:
        lw    a0, 0x04(sp)
        lw    a1, 0x08(sp)
        lw    a2, 0x0c(sp)
        lw    a3, 0x10(sp)
        lw    ra, 0x00(sp)
        addiu sp, sp, 0x40
        ; appeler le drawer original puis retour normal
        j     0x1d18a0            ; (le drawer fait jr ra -> retourne a 0x1d1850, apres le hook)
        nop
```
Résultat attendu : stage **identique** (rendu depuis 0x1580000 au lieu de 0xdb4000). Si OUI → load+repoint validés.
Si crash/glitch → c'est le timing du load synchrone : passer à un hook hors-rendu.

## TEST 2 — la vraie stage Upper (ajoute la tilemap)
Identique à Test 1 mais : `a1=553` (package Upper), repoint bank = **0x1580010** (les tuiles compactes
commencent après le header 16 o), ET écrire la tilemap chaque frame (partie hors-guard) :
```asm
        ; (apres "done", AVANT de restaurer/appeler le drawer, CHAQUE frame)
        ; ntiles @0x1580004 ; tuiles @0x1580010 ; tilemap @ 0x1580010 + ntiles*0x20
        lui   t2, 0x0158
        lw    t4, 0x0004(t2)      ; ntiles
        sll   t4, t4, 5           ; *0x20
        addiu t5, t2, 0x0010      ; tiles base = 0x1580010  (= valeur a mettre dans 0x1dc2e4 au one-shot)
        addu  t6, t5, t4          ; tilemap src = tiles + ntiles*0x20
        ; memcpy 4 couches: 0xba0000<-[t6], 0xba4000<-[t6+0x4000], 0xba8000<-..., 0xbac000<-...
        ; (4 boucles de 0x4000 octets, ou une de 0x10000 si les buffers sont contigus -> A VERIFIER:
        ;  0xba0000..0xbb0000 = contigu donc memcpy 0x10000 d un coup depuis t6)
        lui   t7, 0x00ba          ; dst 0xba0000
        li    t8, 0x4000          ; 0x10000/4 mots... (boucle de mots)
cploop: lw    t9, 0x0000(t6)
        sw    t9, 0x0000(t7)
        addiu t6, t6, 4
        addiu t7, t7, 4
        addiu t8, t8, -1
        bnez  t8, cploop
        nop
```
⚠️ La tilemap est recomposée par le jeu chaque frame → il faut l'écrire APRÈS le composeur et AVANT le draw.
Le hook 0x1d1848 (juste avant le draw de couche) est bien placé, mais à confirmer (le composeur tourne-t-il
avant ?). Sinon : hooker plus haut (0x1d0854) ou repointer la SOURCE (variante D1, descripteur 0xbe2180).

## Encodage hook (pnach)
- `0x1d1848` : `jal 0x1c0400` = **0x0C070100** (au lieu de 0x0C074628). En pnach : `patch=1,EE,001d1848,word,0C070100`.
- Le cave (mots assemblés) : à générer (j'ai un mini-assembleur dispo) une fois le test 1 calé.

## Plan de test (avec Rickow, PCSX2)
1. Charger l'ISO `Hyper Loader Test`, activer le pnach Test-1 (cave e546).
2. Lancer un versus Hyper. Si stage identique → ✅ pipeline. Si crash → ajuster le hook (hors-rendu).
3. Une fois Test-1 OK → Test-2 (package 553 + tilemap). Ajuster timing tilemap.
4. Puis palette, puis multi-stage (table perso→stage).
