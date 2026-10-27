#!/usr/bin/env python3
"""(agent_integration_max) Disposition graphique des persos MAX selon le cache de la session MAX choisi.

SFA3MAX_CACHE (défaut ~/.cache/sfa3max) : racine du cache (converti/, fork/, s/). Version ÉTIRÉE (lot 2b11) :
~/.cache/sfa3max_v2_etire. Les codes globaux suivent les fichiers du cache :
  max_gfx.bin          codes G_MAX = $4DAAB ...           (octet G_MAX·128 = $26D5580 de la région graphique)
  max_portraits_gfx    codes G0 = G_MAX + tuiles(max_gfx)  (portraits, icônes, noms)
  max_plus_gfx (nous)  codes G_PLUS = G0 + tuiles(portraits)
  hsfa_plans.bin       $3000000 si tout tient dessous, sinon $3200000 (bases des plans du fork : HSFA_PLANS) ;
                       les codes de plans des tables plan1 / plan2 ($60000 et +) sont alors décalés de PLANS_DELTA.
Usage shell : python3 max_cache.py  -> variables MAXG, PORTG, PLUSG, PLANSG, PLANS, MAXFORK à évaluer."""
import os
RACINE = os.path.expanduser(os.environ.get("SFA3MAX_CACHE", "~/.cache/sfa3max"))
CV = os.path.join(RACINE, "converti") + "/"
FORK = os.path.join(RACINE, "fork") + "/"
S_DIR = os.path.join(RACINE, "s") + "/"
G_MAX = 0x4DAAB
G0 = G_MAX + os.path.getsize(FORK + "max_gfx.bin") // 128
G_PLUS = G0 + os.path.getsize(FORK + "max_portraits_gfx.bin") // 128
PB1 = 0xA60C + ((G0 - 0xA60C) % 16)          # indice de plan2 prolongé (même valeur mod 16 que G0)
PLANS_ORG = 0x3000000 if G0 < 0x5E000 else 0x3200000
PLUS_MAX = PLANS_ORG - G_PLUS * 128          # place pour max_plus_gfx.bin
PLANS_DELTA = (PLANS_ORG - 0x3000000) // 128
PLANS_CODES = (0x60000, 0x60000 + 0xC3C000 // 128)   # codes des plans d'Upper (hsfa_plans.bin, 12,2 Mo) à l'origine
PLANS_HEX = "%x,%x,%x" % (PLANS_ORG >> 16, (PLANS_ORG >> 16) + 0x40, (PLANS_ORG >> 16) + 0xA0)
def code_nom(N, G0_=None):
    """code global de la 1re tuile d'un nom (noms.json : code_global, sinon $5C880 + code_local de la v1)"""
    return int(N["code_global"].lstrip("$"), 16) if "code_global" in N else 0x5C880 + N["code_local"]
if __name__ == "__main__":
    print("MAXG=%X PORTG=%X PLUSG=%X PLANSG=%X PLANS=%s MAXFORK=%s" % (G_MAX * 128, G0 * 128, G_PLUS * 128, PLANS_ORG, PLANS_HEX, FORK))
