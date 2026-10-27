/* Pilotage d'Hyper depuis un frontal libretro : portage C de tools/hyper-etats/tournee_hyper.lua (VERSUS a 2 joueurs).
   Lit et ecrit la RAM 68K exposee par le coeur (retro_get_memory_data, CpsRamFF = $FF0000-$FFFFFF, mots dans l'ordre
   de l'hote : octet 68K a -> ram[(a - 0xFF0000) ^ 1]). Selection : J1 / J2 = perso (id de base) + famille Z / Z2 / A /
   Z3 ; combat : vie de J1 maintenue, adversaire ramene a 1 apres 60 images. Lancer le coeur avec HSFA_NOROUL=1. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
enum { J_B = 0, J_Y = 1, J_SELECT = 2, J_START = 3, J_UP = 4, J_DOWN = 5, J_LEFT = 6, J_RIGHT = 7, J_A = 8, J_X = 9 };
#define BOUTON1 J_Y                      /* poing faible (disposition FBNeo par defaut) */
#define BOUTON4 J_B                      /* pied faible */
static const uint8_t GRILLE[64] = {0xff,0xff,0xa6,0x0a,0x67,0xff,0xff,0xff,0xff,0x20,0x03,0x04,0x0b,0x21,0xff,0xff,0x22,0x0c,0x07,0x1a,0x08,0x02,0x17,0x3f,0x00,0x18,0x1b,0x1d,0x1c,0x19,0x01,0x3f,0x1e,0x0f,0x06,0x16,0x05,0x10,0x1f,0x3f,0xff,0x23,0x0e,0x0d,0x11,0x15,0xff,0xff,0xff,0xff,0x69,0x09,0xa8,0xff,0xff,0xff,0xff,0xff,0x3f,0x3f,0x3f,0xff,0xff,0xff};
static const uint8_t VERS[] = {0x30,0x40,0x60,0x00,0x31,0x41,0x61,0x01,0x32,0x42,0x62,0x02,0x33,0x43,0x63,0x03,0x34,0x44,0x64,0x04,0x35,0x45,0x65,0x05,0x36,0x46,0x66,0x06,0x37,0x47,0x67,0x07,0x38,0x48,0x68,0x08,0x39,0x49,0x69,0x09,0x3a,0x4a,0x6a,0x0a,0x3b,0x4b,0x6b,0x0b,0x3c,0x4c,0x6c,0x0c,0x4d,0x6d,0x0d,0xff,0x4e,0x6e,0x0e,0xff,0x4f,0x6f,0x0f,0xff,0x50,0x70,0x10,0xff,0x51,0x71,0x11,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x15,0xff,0xff,0xff,0x7e,0x16,0xff,0xff,0x57,0x77,0x17,0xff,0x18,0xff,0xff,0xff,0x19,0xff,0xff,0xff,0x1a,0xff,0xff,0xff,0x1b,0xff,0xff,0xff,0x1c,0xff,0xff,0xff,0x1d,0xff,0xff,0xff,0x1e,0xff,0xff,0xff,0x1f,0xff,0xff,0xff,0x20,0xff,0xff,0xff,0x21,0xff,0xff,0xff,0x22,0xff,0xff,0xff,0x23,0xff,0xff,0xff,0x32,0x42,0x62,0x02,0x15,0xff,0xff,0xff};
typedef struct { int base; char fam[4]; int ism, mode, ex, exv, exg, roul; } spec_t;  /* fam : "Z", "Z2", "A", "Z3" ; ism : -1 X, 0 A, 1 V ;
   mode : 0 NORMAL, 1 MAZI, 2 SAIKYO, 3 CLASSIC, 4-7 leur S-ISM dans le meme ordre (menu des modes, ZERO 3 ;
   curseur P+$5C = 0-3, S-ISM = 6, 5, 7, 4) ; ex : Start + droite (> 0) ou gauche (< 0)
   maintenus pendant la validation du mode */
typedef struct {
  uint8_t *ram; FILE *jl; long k; int nsel, combats, stable; int en_sel[2]; char last[160];
  spec_t liste[16][2]; int nliste; int presse[2][16]; int tm[2], te[2], tv[2];
} tournee_t;
static uint32_t T_J[2] = {0xFF8400, 0xFF8800};
static int tu8(tournee_t *t, uint32_t a) { return t->ram[(a - 0xFF0000) ^ 1]; }
static int tu16(tournee_t *t, uint32_t a) { return *(uint16_t *)&t->ram[a - 0xFF0000]; }
static void tw16(tournee_t *t, uint32_t a, int v) { *(uint16_t *)&t->ram[a - 0xFF0000] = (uint16_t)v; }
static const char *famille(int id) { return id < 0x30 ? "Z3" : id < 0x40 ? "Z" : id < 0x60 ? "Z2" : "A"; }
static int colonne(const spec_t *s) {
  for (int c = 0; c < 4; c++) { int id = VERS[s->base * 4 + c]; if (id != 0xff && !strcmp(famille(id), s->fam)) return c; }
  return 0;
}
static const int DX[4] = {1, -1, 0, 0}, DY[4] = {0, 0, 1, -1}, DB[4] = {J_RIGHT, J_LEFT, J_DOWN, J_UP};
static int pas_(int *x, int *y, int dx, int dy, int j) {
  int nx = *x, ny = *y;
  for (int n = 0; n < 8; n++) {
    nx = (nx + dx) & 7; ny = (ny + dy) & 7;
    int c = GRILLE[ny * 8 + nx];
    if (c != 0x3f) { if ((c >> (6 + j)) & 1) return 0; *x = nx; *y = ny; return 1; }
  }
  return 0;
}
/* premiere direction (indice de DB) d'un plus court chemin vers base, -1 si deja dessus ou introuvable */
static int chemin(int x0, int y0, int base, int j) {
  int pere[64], dir[64], file[64], n = 0, i = 0;
  for (int q = 0; q < 64; q++) pere[q] = -2;
  pere[y0 * 8 + x0] = -1; file[n++] = y0 * 8 + x0;
  while (i < n) {
    int c = file[i++], x = c & 7, y = c >> 3;
    if ((GRILLE[c] & 0x3f) == base) {
      if (pere[c] == -1) return -1;
      while (pere[c] != y0 * 8 + x0) c = pere[c];
      return dir[c];
    }
    for (int d = 0; d < 4; d++) { int nx = x, ny = y; if (pas_(&nx, &ny, DX[d], DY[d], j)) { int q = ny * 8 + nx; if (pere[q] == -2) { pere[q] = c; dir[q] = d; file[n++] = q; } } }
  }
  return -1;
}
static void on(tournee_t *t, int port, int b) { t->presse[port][b] = 1; }
static void appui(tournee_t *t, int j, int b) { if (t->k % 8 < 3) on(t, j, b); }
static void selectionne(tournee_t *t, int j, const spec_t *s) {
  uint32_t P = T_J[j]; int et = tu8(t, P + 5);
  if (et == 0) {
    int d = chemin(tu16(t, P + 0x12) & 7, tu16(t, P + 0x16) & 7, s->base, j);
    if (d >= 0) appui(t, j, DB[d]);
    else { if (s->exg) on(t, j, J_START); if (s->roul) on(t, j, J_SELECT);  /* .g : Start tenu ; .r : Select tenu (roulette) */
      if (t->k % 16 >= 8 && t->k % 16 < 11) on(t, j, BOUTON1); }
  } else if (et == 2) {
    if (!t->tv[j] && tu8(t, P + 0x5C) != colonne(s)) appui(t, j, J_DOWN);
    else if (s->exv) {                   /* Start + droite (ou gauche) maintenus pendant la validation de la version */
      t->tv[j]++; on(t, j, J_START); if (s->exv != 2) on(t, j, s->exv < 0 ? J_LEFT : J_RIGHT);
      if (t->tv[j] > 8 && t->k % 16 >= 8 && t->k % 16 < 11) on(t, j, BOUTON1);
    } else if (t->k % 16 >= 8 && t->k % 16 < 11) on(t, j, BOUTON1);
  } else if (et == 8) {
    int i = tu8(t, P + 0x133); if (i >= 0x80) i -= 0x100;
    if (i != s->ism) appui(t, j, J_DOWN); else appui(t, j, BOUTON1);
  } else if (et == 6) {                  /* menu des modes (ZERO 3) : curseur en P+$5C */
    static const int SV[4] = {6, 5, 7, 4};               /* valeur du curseur pour la S-ISM de chaque mode (mesure) */
    int c = tu8(t, P + 0x5C), base = s->mode & 3, cible = s->mode < 4 ? s->mode : SV[base];
    if (s->ex && cible < 4) {            /* ancienne forme : Start + direction maintenus pendant la validation */
      if (!t->te[j] && c != cible) { if (t->k % 8 == 0) on(t, j, J_DOWN); }
      else { t->te[j]++; on(t, j, J_START); on(t, j, s->ex < 0 ? J_LEFT : J_RIGHT);
        if (t->te[j] > 8 && t->k % 16 >= 8 && t->k % 16 < 11) on(t, j, BOUTON1); }
    } else if (c < 4 && c != base) { if (t->k % 8 == 0) on(t, j, J_DOWN); }
    else if (c != cible) { on(t, j, J_START); if (t->k % 16 == 4) on(t, j, J_RIGHT); }   /* Start tenu + droite : S-ISM */
    else { if (cible >= 4) on(t, j, J_START); if (t->k % 16 >= 8 && t->k % 16 < 11) on(t, j, BOUTON1); }
  } else if (et == 4 || et == 0xA) appui(t, j, BOUTON1);
}
/* une image : decide les entrees (t->presse) d'apres la RAM ; journal des transitions */
static void tournee_image(tournee_t *t) {
  t->k++; memset(t->presse, 0, sizeof t->presse);
  int p0 = tu16(t, 0xFF8000), p4 = tu16(t, 0xFF8004), p8 = tu16(t, 0xFF8008);
  if (p0 == 6 || p0 == 4 || (p0 == 2 && p4 == 0)) {
    if (t->k > 200 && t->k % 60 < 6 && t->k < 900) { on(t, 0, J_SELECT); on(t, 1, J_SELECT); }
    if (p0 == 6 && t->k > 300 && t->k % 40 < 6) on(t, 0, J_START);
    if (p0 == 4) { if (tu8(t, 0xFF4201) != 1) { if (t->k % 20 < 4) on(t, 0, J_DOWN); } else if (t->k % 20 >= 10 && t->k % 20 < 14) on(t, 0, BOUTON1); }
  }
  if (p0 == 2 && p4 == 2 && p8 == 4) {
    if ((tu8(t, 0xFF80A9) & 2) == 0 && t->k % 30 < 4) on(t, 1, J_START);
    for (int j = 0; j < 2; j++) {
      uint32_t P = T_J[j]; int et = tu8(t, P + 5);
      if (tu8(t, P + 1) != 0 && et < 0xC) {
        if (!t->en_sel[j]) { t->en_sel[j] = 1; t->tm[j] = t->te[j] = t->tv[j] = 0; if (j == 0) { t->nsel++; fprintf(t->jl, "SELECTION %d image %ld\n", t->nsel, t->k); } }
        const spec_t *s = &t->liste[(t->nsel - 1 + t->nliste) % t->nliste][j];
        selectionne(t, j, s);
      }
    }
  }
  for (int j = 0; j < 2; j++) {
    uint32_t P = T_J[j];
    if (t->en_sel[j] && tu8(t, P + 5) == 0xC) {
      t->en_sel[j] = 0;
      fprintf(t->jl, "CHOIX J%d image %ld : $102=%02x base=%02x ism=%02x $116=%02x $122=%02x $123=%02x $15F=%02x $D0=%02x $5C=%02x\n", j + 1, t->k,
              tu8(t, P + 0x103), tu8(t, P + 0x117), tu8(t, P + 0x133), tu8(t, P + 0x116), tu8(t, P + 0x122), tu8(t, P + 0x123),
              tu8(t, P + 0x15F), tu8(t, P + 0xD0), tu8(t, P + 0x5C));
    }
  }
  if (p0 == 2 && p4 == 2 && p8 != 4 && t->k % 24 >= 12 && t->k % 24 < 15) { on(t, 0, BOUTON1); on(t, 1, BOUTON1); }
  /* combat */
  uint32_t adv[3]; int na = 0; uint32_t cand[3] = {T_J[1], 0xFF8C00, 0xFF9000};
  for (int q = 0; q < 3; q++) if (tu8(t, cand[q] + 5) == 2) adv[na++] = cand[q];
  int combat = p0 == 2 && p4 == 4 && p8 == 6 && tu8(t, T_J[0] + 5) == 2 && na > 0;
  if (combat) {
    t->stable++;
    if (t->stable == 1) { t->combats++; fprintf(t->jl, "MANCHE %d image %ld J1 %02x J2 %02x\n", t->combats, t->k, tu8(t, T_J[0] + 0x103), tu8(t, T_J[1] + 0x103)); }
    tw16(t, T_J[0] + 0x50, 0x90); tw16(t, T_J[0] + 0x52, 0x90);
    static int passif = -1; if (passif < 0) passif = getenv("HSFA_TOURNEE_PASSIF") && atoi(getenv("HSFA_TOURNEE_PASSIF")) == 1;
    if (t->stable > 60 && !passif) {             /* HSFA_TOURNEE_PASSIF=1 : le combat est laisse aux entrees (HSFA_ENTREES) */
      static int pv = -1; if (pv < 0) pv = getenv("HSFA_TOURNEE_PV") && atoi(getenv("HSFA_TOURNEE_PV")) == 1;
      if (!pv)                           /* HSFA_TOURNEE_PV=1 : l'adversaire garde sa vie (cris de degats) */
      for (int q = 0; q < na; q++) { int v = tu16(t, adv[q] + 0x50); if (v > 1 && v < 0x100) { tw16(t, adv[q] + 0x50, 1); tw16(t, adv[q] + 0x52, 1); } }
      int av = tu16(t, T_J[0] + 0x12) < tu16(t, adv[0] + 0x12) ? J_RIGHT : J_LEFT, s = t->stable % 40;
      if (s < 3) on(t, 0, J_DOWN); else if (s < 6) { on(t, 0, J_DOWN); on(t, 0, av); }
      else if (s < 10) { on(t, 0, av); if (s >= 7) on(t, 0, BOUTON1); }
      else if (s < 30) { on(t, 0, av); if (s % 6 < 2) on(t, 0, BOUTON4); }
    }
  } else t->stable = 0;
  char st[160];
  snprintf(st, sizeof st, "%04x %04x %04x | J1 %02x %02x %02x | J2 %02x %02x %02x", p0, p4, p8, tu8(t, T_J[0] + 1), tu8(t, T_J[0] + 5),
           tu8(t, T_J[0] + 0x103), tu8(t, T_J[1] + 1), tu8(t, T_J[1] + 5), tu8(t, T_J[1] + 0x103));
  if (strcmp(st, t->last)) { fprintf(t->jl, "%6ld : %s\n", t->k, st); strcpy(t->last, st); }
}
/* LISTE = "00.Z/01.Z2,..." ; options .iX / .iA / .iV (ism), .m0-.m7 (mode, 4-7 = S-ISM), .e+N / .e-N (Start + droite / gauche au
   menu des modes), .v+ / .v- (idem a la validation de la version), .vS
   (Start seul tenu a la validation de la version), .g (Start tenu a la validation du perso), .r (Select tenu a la validation
   du perso : roulette) */
static void tournee_liste(tournee_t *t, const char *l) {
  t->nliste = 0;
  while (*l && t->nliste < 16) {
    for (int j = 0; j < 2; j++) {
      unsigned b = 0; char f[4] = "Z3"; int n = 0;
      if (sscanf(l, "%x.%3[A-Z0-9]%n", &b, f, &n) >= 1) { t->liste[t->nliste][j].base = (int)b; strcpy(t->liste[t->nliste][j].fam, f); l += n; }
      spec_t *sp = &t->liste[t->nliste][j]; sp->ism = sp->mode = sp->ex = sp->exv = sp->exg = sp->roul = 0;
      for (;;) {
        if (l[0] == '.' && l[1] == 'i') { sp->ism = l[2] == 'X' ? -1 : l[2] == 'V' ? 1 : 0; l += 3; }
        else if (l[0] == '.' && l[1] == 'm' && l[2] >= '0' && l[2] <= '7') { sp->mode = l[2] - '0'; l += 3; }
        else if (l[0] == '.' && l[1] == 'e' && (l[2] == '+' || l[2] == '-') && l[3] >= '1' && l[3] <= '9') {
          sp->ex = (l[2] == '-' ? -1 : 1) * (l[3] - '0'); l += 4; }
        else if (l[0] == '.' && l[1] == 'v' && (l[2] == '+' || l[2] == '-' || l[2] == 'S')) { sp->exv = l[2] == '-' ? -1 : l[2] == 'S' ? 2 : 1; l += 3; }
        else if (l[0] == '.' && l[1] == 'g') { sp->exg = 1; l += 2; }
        else if (l[0] == '.' && l[1] == 'r') { sp->roul = 1; l += 2; }
        else break;
      }
      if (*l == '/') l++;
    }
    t->nliste++;
    if (*l == ',') l++; else break;
  }
}
