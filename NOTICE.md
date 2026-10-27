# Licences by component / Licences par composant

HSFA mixes code of its own with modifications to two emulators. Each part keeps its own licence.
*(Français : chaque composant garde sa licence ; résumé en fin de fichier.)*

| Component | Where | Licence |
|---|---|---|
| HSFA's own code and documentation (translator, build scripts, tools, docs) | `src/`, `scripts/`, `tools/`, `docs/`, `max/`, `legacy/`, `re/` | **MIT**, see [LICENSE](LICENSE) |
| FBNeo HSFA libretro cores (4:3 `fbneo_hsfa`, 16:9 `fbneo_hsfaws`) | patches in `patches/fbneo/`; binaries attached to releases | **FinalBurn Neo licence**, full text verbatim in [patches/fbneo/LICENSE-FBNeo.txt](patches/fbneo/LICENSE-FBNeo.txt) |
| stb_vorbis 1.22 (Ogg Vorbis decoder, patch `0004`) | `src/dep/libs/stb_vorbis/` once patched | **public domain or MIT**, your choice (Sean Barrett), see below |
| 2nd QSound HLE (`hsfa_qsound.h`, patch `0001`) | `src/burn/drv/capcom/hsfa_qsound.h` once patched | **BSD-3-Clause**: derived from the DL-1425 HLE of `qs_c.cpp` (superctr, Valley Bell), see below |
| MAME fork of the bench (game `sfa3hx`) | patches in `patches/mame-fork/` | **MAME licence**: GPL-2.0-or-later for MAME as a whole; each modified file keeps its own SPDX header (often BSD-3-Clause) |

## FinalBurn Neo HSFA cores

The cores are FinalBurn Neo built from libretro/FBNeo commit `af5d3f3` with the patches of `patches/fbneo/` (chain
`0001`-`0014` plus `0007b`, see [patches/fbneo/README.md](patches/fbneo/README.md)). They are distributed under the
FinalBurn Neo licence, which is reproduced verbatim in `patches/fbneo/LICENSE-FBNeo.txt` and in every core archive.
In short:

- **they may not be sold**, leased or rented, and nobody may seek monetary profit from them;
- **no donations** may be requested for this work;
- **the source of every change is public**: the patches in `patches/fbneo/`, which apply to the commit above;
- they are distributed **without any ROM image**: the games are rebuilt from your own ISO (`hsfa_build.py`);
- FinalBurn Neo is also subject to the MAME licence, as its licence text explains.

## stb_vorbis (patch `0004`)

stb_vorbis v1.22, https://github.com/nothings/stb, is available under two licences, at your choice.

```
ALTERNATIVE A - MIT License
Copyright (c) 2017 Sean Barrett
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

ALTERNATIVE B - Public Domain (www.unlicense.org)
This is free and unencumbered software released into the public domain.
Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.
In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## QSound HLE of the 2nd QSound (patch `0001`)

`hsfa_qsound.h` is an instantiable copy of the DL-1425 HLE emulator of `qs_c.cpp`, the same code as MAME's
`qsoundhle.cpp`. Its copyright holders are superctr and Valley Bell, and it is licensed under BSD-3-Clause:

```
Copyright (c) superctr, Valley Bell
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this
   list of conditions and the following disclaimer in the documentation and/or
   other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may
   be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## MAME fork (`patches/mame-fork/`)

These patches modify MAME 0.285 (tag `mame0285`). MAME as a whole is distributed under the GNU General Public
License, version 2 or later. Each file of MAME keeps the licence given in its own header (`// license:`), often
BSD-3-Clause. The patches follow the licence of the files they modify. Licence texts: COPYING and the docs/legal folder of
https://github.com/mamedev/mame. No MAME binary is distributed by this project.

## Game data

None. *Street Fighter*, *Street Fighter Alpha* and related marks belong to Capcom. The tools read the game data from
the copy of *Street Fighter Alpha Anthology* you own, and what they produce stays with you.

---

**En français.**
- Code et documentation d'HSFA : MIT ([LICENSE](LICENSE)).
- Cœurs FBNeo HSFA : licence de FinalBurn Neo, recopiée mot pour mot dans `patches/fbneo/LICENSE-FBNeo.txt` et
  jointe à chaque archive de cœur. Pas de vente, pas de dons ; les sources des modifications sont les patchs de
  `patches/fbneo/`.
- stb_vorbis : domaine public ou MIT. QSound HLE (`hsfa_qsound.h`) : BSD-3-Clause (superctr, Valley Bell).
- Fork MAME (`patches/mame-fork/`) : licence de MAME (GPL-2.0 ou ultérieure pour l'ensemble).
- Aucune donnée de jeu.
