#!/bin/bash
# interrupteurs.sh [module] -- switch audit of the translator (review E8, 11/11/2026, docs/rapports/reviews/):
# builds <module> (default ro3) once as reference, then once with each switch turned off (and the default-0 switches
# turned on), ONE build at a time under nice 19 (about 75 builds of 35 s for ro3), and appends to
# $SORTIE/interrupteurs_<module>.txt one line per trial:
#   VAR=val | NAME code=N md5(all program ROMs) md5(03c) | ext=md5(ext_*.bin) | carte_diff=<map lines differing from ref>
# Each trial keeps $SORTIE/constr/<module>_<name>/build.log and carte_image.txt (the ROMs are deleted).
# Then: python3 interrupteurs_bilan.py $SORTIE/interrupteurs_<module>.txt $SORTIE/constr <module>
# Rule (AGENTS.md §3): every switch at 0 must give a byte-identical ROM; a switch with no effect is dead code
# (the historical switches are listed in docs/methodes/pieges-du-traducteur.md).
# Environment: HSFA_TRAD and SORTIE (see construit.sh); for ro9: RO9_EXTRACT_MODULES and RO9_SON_DONNEES
# (folder of the sound modules and son_donnees_ro9.bin, passed to the build as EXTRACT_MODULES / HSFA_SON_DONNEES).
set -u
ICI=$(dirname "$(readlink -f "$0")"); M=${1:-ro3}
export SORTIE=$(mkdir -p "${SORTIE:-./revue_interrupteurs}" && cd "${SORTIE:-./revue_interrupteurs}" && pwd)
S=$SORTIE/interrupteurs_$M.txt; C=$SORTIE/constr
EXTRA=()
if [ "$M" = ro9 ]; then EXTRA=("EXTRACT_MODULES=${RO9_EXTRACT_MODULES:?}" "HSFA_SON_DONNEES=${RO9_SON_DONNEES:?}"); fi
un() { n=$1; shift
  r=$(MODULE=$M "$ICI/construit.sh" "${M}_$n" "${EXTRA[@]}" "$@")
  d=$(diff <(cut -d' ' -f1,3- "$C/${M}_ref/carte_image.txt" 2>/dev/null) <(cut -d' ' -f1,3- "$C/${M}_$n/carte_image.txt" 2>/dev/null) | grep -c '^[<>]')
  x=$(cat "$C/${M}_$n"/ext_*.bin 2>/dev/null | md5sum | cut -c1-8)
  echo "$* | $r | ext=$x | carte_diff=$d" >> "$S"
  rm -rf "$C/${M}_$n"/roms_* "$C/${M}_$n"/ext_*.bin "$C/${M}_$n"/banques_hx 2>/dev/null
}
: > "$S"
un ref
# default-1 switches of translate.py (form !='0' or =="1"), v160 list of the review
for v in AIDE_ROXR DN_ALU COPIES VRAM_TABLE FLUXEA BYTE_PRE EXTRA_REGS OBJBASE CONST_OP PILE_LUI TBLBYTE MEMSHL IDXRMW CDISP \
  SHIFT_MR ANDAND SPILL_Q TBLMASK BIGSHIFT ABSEXT TBLMEM D8HI ROT LOGIC_ZERO TBLOP MEMSHIFT MULS EXT_MEM LUI_IMM SW_X4 \
  EXG_PILE EXG_PILE_D BITOP_DN CMPDMEM TBL_TST FTC_AVANT TAILBR LUIDN CMPMM MEMSWAPD PRETE_TEST PRETE_CMP RETAG24 RETAG_BRAW \
  AIG_BRANCHE AIG_D1 LONG_POSTINC DROP_SR \
  MERGE_IFELSE BACK_AFTER LATERAL D8_EARLY RELOGE_CODE RELOGE_RAM RELOGE_NATIF COUPE_BLOCS OPTION_RETOUR EXIT_RETOUR S1_MIROIR \
  OBJ_MIROIR SFA3_TUILES_S3 \
  A8_ENTREE TST_C TST_ZX CMP_MEMADD CMP_IDX CMP_D8 CMP_MEMDN PARITE_FLOT PARITE_SITES BCD_REG AIDE_SBCD; do un $v $v=0; done
# (the last line: v161 fixes of the review, journal §219; not in the review's own run)
# default-0 switches: tried at 1 (dead code?)
for v in PARTIAL_LIVE MEMSHIFT_GARDE AIG_D1_TOUS CMPX AUDIT_MEM; do un ${v}_1 $v=1; done
un A8_HOME_none A8_HOME=none; un D8_HOME_none D8_HOME=none; un MEMMODE_type MEMMODE=type; un MEMMODE_cps2 MEMMODE=cps2
un DTAB_rel DTAB=rel; un DPTR_fixe DPTR=fixe; un LOOP_EXT_0 LOOP_EXT=0; un AIG_D1_SEUL_vide AIG_D1_SEUL=
echo FIN >> "$S"
