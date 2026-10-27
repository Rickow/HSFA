#!/usr/bin/env python3
"""Mesure ce que le traducteur consomme reellement, et ce qui lui echappe.

On parcourt les blocs cartographies et on compte, instruction MIPS par instruction,
celles qui sont absorbees par un idiome reconnu et celles qui ne le sont pas.
Les non-reconnues sont regroupees par motif pour montrer OU investir.
"""
import sys, json, collections
sys.path.insert(0, "<workspace>/scripts/untranspile")
from mips import decode, REG

RECONNU = {
 'lui','sll','addiu','lw','sw','lb','sb','lh','sh','lbu','lhu',
 'dsll32','dsra32','andi','bne','beq',
 'jal','jr','jalr','ld','sd','bltz','bgez',
 'addu','subu','and','or','xor','nor','sltu','ori','srl','sllv',
}

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    mp=json.load(open("<workspace>/scripts/untranspile/map_ro3_sfa3.json"))
    blocks=sorted(mp["blocks"], key=lambda b:-b["pts"])[:12]
    tot=0; known=0
    unk=collections.Counter()
    for b in blocks:
        a,z = b["mips"]
        for ins in decode(ro3, a, min(z, a+0x20000)):
            tot+=1
            if ins.m in RECONNU: known+=1
            else: unk[ins.m]+=1
    print("instructions MIPS parcourues : %d"%tot)
    print("absorbees par un idiome connu : %d (%.1f%%)\n"%(known,100*known/max(1,tot)))
    print("=== ce qui echappe, par frequence ===")
    for m,c in unk.most_common(18):
        print("  %-10s %7d  (%.1f%%)"%(m,c,100*c/max(1,tot)))
