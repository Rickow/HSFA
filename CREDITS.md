# Credits / Remerciements

HSFA stands on the work of many people. Thank you all.
*(Français : HSFA s'appuie sur le travail de beaucoup de monde ; merci à toutes et à tous. Résumé en fin de fichier.)*

## The games

- **Capcom**: *Street Fighter Alpha* / *Zero* 1, 2, 3, *Street Fighter Alpha 3 Upper*, *Hyper Street Fighter Alpha*
  (*Street Fighter Alpha Anthology*, PS2) and *Street Fighter Alpha 3 MAX* (PSP). *Street Fighter* and *Street Fighter
  Alpha* are trademarks of Capcom. HSFA is not affiliated with or endorsed by Capcom, and contains no game data.

## Emulators and libraries HSFA builds on

- **FinalBurn Neo** team and the **libretro** project: the base of the HSFA cores (FinalBurn Neo licence, see
  `NOTICE.md`), and **RetroArch**.
- **MAME** team: the bench (fork of MAME) and decades of CPS-2 documentation.
- **PPSSPP** (PSP oracle and bench), **PCSX2** (PS2 reference), **Ghidra**, **Capstone** (disassembly), **NumPy**,
  **Pillow**.
- **Sean Barrett**: stb_vorbis (Ogg Vorbis decoder). The DL-1425 **QSound HLE** authors (via MAME). See `NOTICE.md`.
- **Recalbox**, **ROCKNIX** and **Android** retro communities: the platforms the cores run on.

## Projects that helped (ideas, cross-checks; no code copied unless stated)

- **irnutsmurt**, [Street-Alpha-3-Dreamcast-Recomp](https://github.com/irnutsmurt/Street-Alpha-3-Dreamcast-Recomp):
  recompiles the same four *SFA3 MAX* characters from the PSP for the Dreamcast; about thirty addresses cross-checked
  with ours, and a public exchange of corrections.
- **Zer0-NexuS**: patcher adding the four MAX characters to *Upper* on NAOMI, the same idea on another board.
- **tmcleroy**, [cps2recomp](https://github.com/tmcleroy/cps2recomp) and
  [sfa2-recomp](https://github.com/tmcleroy/sfa2-recomp): static recompilation of CPS-2 games to C++. HSFA's
  « stage-locked » 16:9 view comes from its *Invisible walls* idea; its notes confirmed where the stage art ends and
  how stages move between games; its guest-stage work (#281, #294) gave the stage-check idea (camera held in the
  middle and at both ends) and SFA2 stage-code addresses; it cross-checked our SFA3 address index (#249) and corrected
  four entries. Ideas only: no code taken (GPL-3.0).
- **omegakatana92**, [Street-Fighter-Alpha-Recomp](https://github.com/omegakatana92/Street-Fighter-Alpha-Recomp-):
  *Street Fighter Alpha* port made with cps2recomp; its memory map of SFA1 was read as a reference. No code taken.

## Books and guides consulted (cited by page; nothing reproduced)

- *All About Street Fighter Zero*, *Zero 2* and *Zero 3* (Dempa Publications), *All About Capcom Fighting Games
  1987-2000*.
- *Capcom Secret File* (*Street Fighter Zero 2*, *Zero 3*), *Street Fighter Eternal Challenge*.
- BradyGames' *Street Fighter Alpha Anthology* official guide.

## Authors

- **Rickow**: project, testing on real hardware (Android handhelds, ROCKNIX, Raspberry Pi), decisions.
- Written with **Claude** (Anthropic) as coding assistant: the commits say so (`Co-Authored-By`).

---

*Résumé en français : jeux de Capcom (marques déposées ; projet non affilié, sans données de jeu) ; émulateurs et
bibliothèques (FinalBurn Neo, libretro / RetroArch, MAME, PPSSPP, PCSX2, Ghidra, Capstone, stb_vorbis, QSound HLE) ;
projets voisins qui ont aidé par leurs idées ou leurs recoupements, sans reprise de code (irnutsmurt : Street Alpha 3
Dreamcast Recomp ; Zer0-NexuS : patcheur Upper NAOMI ; tmcleroy : cps2recomp et sfa2-recomp, d'où vient l'idée de la
vue 16:9 calée sur le décor ; omegakatana92 : Street Fighter Alpha Recomp) ; livres et guides cités par page, rien de
reproduit ; auteurs : Rickow, avec Claude (Anthropic) comme assistant de programmation.*
