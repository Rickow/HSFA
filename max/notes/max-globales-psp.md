# Globales PSP sans équivalent arcade, consultées par le code des persos MAX (2026-10-04)

Bloc `0x39C9E0…` : structure d'état propre au PSP (modes/options ?), très utilisée par le moteur PSP ; pas une
copie de la zone A5 arcade (votes incohérents). Bloc `0xA3E…/0xA4…` : compteurs/réservoirs (effets…).
À trancher au banc (valeur du mode arcade) ; contenu MAX hors persos écarté (HANDOFF §109).

| adresse | décalage | accès (qui : L/É) |
|---|---|---|
| `0x39c9e0` | +0x0 | ingrid R×1 |
| `0x39c9e1` | +0x1 | ingrid R×1 |
| `0x39ca06` | +0x26 | moteur R×3 |
| `0x39ca2a` | +0x4a | moteur R×1, yun R×2 |
| `0x39ca3d` | +0x5d | ingrid R×1, ingrid W×1 |
| `0x39ca3e` | +0x5e | ingrid R×1 |
| `0x39ca67` | +0x87 | moteur R×1 |
| `0xa3e7c3` | +0x7c3 | moteur R×1, moteur W×1 |
| `0xa3e7c6` | +0x7c6 | moteur R×1, moteur W×1 |
| `0xa3e7c9` | +0x7c9 | moteur R×1, moteur W×1 |
| `0xa46a2a` | +0x8a2a | ingrid W×2 |
| `0xa46ac2` | +0x8ac2 | ingrid R×2, ingrid W×4 |
| `0xa46ac4` | +0x8ac4 | ingrid R×1, ingrid W×1 |
| `0xa46ac6` | +0x8ac6 | ingrid R×2, ingrid W×4 |
| `0xa46b5a` | +0x8b5a | ingrid R×2, ingrid W×4 |
| `0xa46b5e` | +0x8b5e | ingrid R×1, ingrid W×1 |
| `0xa4ced0` | +0xeed0 | moteur R×1 |
| `0xa4ced4` | +0xeed4 | moteur R×1 |
