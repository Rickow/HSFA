# Patches

PCSX2 `.pnach` files. Place one in your PCSX2 `cheats/` directory, named after
the game serial and CRC — `SLUS-21317_72CE7A78.pnach` — and enable cheats.

These contain **only original code** (injected MIPS routines and byte patches).
They contain no game data.

| File | Purpose |
|---|---|
| `SLUS-21317_72CE7A78.pnach` | Reference build used for cross-stage work |
| `SLUS-21317_72CE7A78_chunli_ctx.pnach` | Cross-stage, layer-context repoint approach (WIP) |
| `SLUS-21317_72CE7A78_chunli*.pnach` | Earlier cross-stage iterations, kept for reference |
| `arcade-mode*.pnach.txt` | Arcade mode patch lines |

> Cross-stage patches are **work in progress** and expect a companion data
> package that is not distributed here (it is derived from your own game copy).
