/* dechiffre_cps2.c : programme 68K d'un jeu CPS2 -> deux images gros-boutistes (instructions dechiffrees, donnees brutes).
   Reprend l'algorithme de FBNeo (src/burn/drv/capcom/cps2_crpt.cpp, lignes 129-640 = boites S et reseaux de Feistel) :
     sed -n '129,640p' <FBNeo>/src/burn/drv/capcom/cps2_crpt.cpp > corps.inc && gcc -O2 -w -o dechiffre_cps2 dechiffre_cps2.c
     cat sz3e.03c sz3e.04c sz3.05c ... sz3.10b > brut.bin       (fichiers du zip, dans l'ordre de chargement)
     ./dechiffre_cps2 sfa3.key brut.bin code.bin donnees.bin
   code.bin : vue « instructions » (desassembler) ; donnees.bin : vue « donnees » (tables, lectures ordinaires).
   Seule la zone sous la limite de la cle (1 Mo pour sfa3) est chiffree. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef int32_t INT32; typedef uint32_t UINT32; typedef uint16_t UINT16; typedef uint8_t UINT8; typedef int8_t INT8;
#define BIT(x,n) (((x)>>(n))&1)
#define BITSWAP8(v,b7,b6,b5,b4,b3,b2,b1,b0) ((BIT(v,b7)<<7)|(BIT(v,b6)<<6)|(BIT(v,b5)<<5)|(BIT(v,b4)<<4)|(BIT(v,b3)<<3)|(BIT(v,b2)<<2)|(BIT(v,b1)<<1)|BIT(v,b0))
#include "corps.inc"
int main(int c,char**v){
  FILE*f=fopen(v[1],"rb"); UINT8 kb[20]; fread(kb,1,20,f); fclose(f);
  f=fopen(v[2],"rb"); fseek(f,0,2); long n=ftell(f); rewind(f); UINT16*rom=malloc(n); fread(rom,1,n,f); fclose(f);
  UINT16 decoded[10]={0};
  for(int b=0;b<160;b++){int bit=(317-b)%160; if((kb[bit/8]>>((bit^7)%8))&1) decoded[b/16]|=(0x8000>>(b%16));}
  UINT32 mk[2]={(decoded[0]<<16)|decoded[1],(decoded[2]<<16)|decoded[3]};
  UINT32 lower=0,upper=(decoded[9]==0xffff)?0xffffff:((((~decoded[9]&0x3ff)<<14)|0x3fff)+1);
  if(decoded[9]==0xffff) lower=0xff0000;
  lower/=2; upper/=2; long length=n;
  UINT16*dec=malloc(n); UINT32 key1[4]; struct optimised_sbox s1[16],s2[16];
  optimise_sboxes(&s1[0],fn1_r1_boxes);optimise_sboxes(&s1[4],fn1_r2_boxes);optimise_sboxes(&s1[8],fn1_r3_boxes);optimise_sboxes(&s1[12],fn1_r4_boxes);
  optimise_sboxes(&s2[0],fn2_r1_boxes);optimise_sboxes(&s2[4],fn2_r2_boxes);optimise_sboxes(&s2[8],fn2_r3_boxes);optimise_sboxes(&s2[12],fn2_r4_boxes);
  expand_1st_key(key1,mk);
  key1[0]^=BIT(key1[0],1)<<4;key1[0]^=BIT(key1[0],2)<<5;key1[0]^=BIT(key1[0],8)<<11;key1[1]^=BIT(key1[1],0)<<5;key1[1]^=BIT(key1[1],8)<<11;key1[2]^=BIT(key1[2],1)<<5;key1[2]^=BIT(key1[2],8)<<11;
  for(int i=0;i<0x10000;i++){
    UINT16 seed=feistel(i,fn1_groupA,fn1_groupB,&s1[0],&s1[4],&s1[8],&s1[12],key1[0],key1[1],key1[2],key1[3]);
    UINT32 sk[2],key2[4]; expand_subkey(sk,seed); sk[0]^=mk[0]; sk[1]^=mk[1]; expand_2nd_key(key2,sk);
    key2[0]^=BIT(key2[0],0)<<5;key2[0]^=BIT(key2[0],6)<<11;key2[1]^=BIT(key2[1],0)<<5;key2[1]^=BIT(key2[1],1)<<4;key2[2]^=BIT(key2[2],2)<<5;key2[2]^=BIT(key2[2],3)<<4;key2[2]^=BIT(key2[2],7)<<11;key2[3]^=BIT(key2[3],1)<<5;
    for(long a=i;a<length/2;a+=0x10000) dec[a]=(a>=lower&&a<=upper)?feistel(rom[a],fn2_groupA,fn2_groupB,&s2[0],&s2[4],&s2[8],&s2[12],key2[0],key2[1],key2[2],key2[3]):rom[a];
  }
  f=fopen(v[3],"wb"); for(long a=0;a<n/2;a++){fputc(dec[a]>>8,f);fputc(dec[a]&255,f);} fclose(f);
  f=fopen(v[4],"wb"); for(long a=0;a<n/2;a++){fputc(rom[a]>>8,f);fputc(rom[a]&255,f);} fclose(f);
  fprintf(stderr,"cle %08x %08x limite %x\n",mk[0],mk[1],upper*2); return 0;}
