// HSFA : 2e QSound (rejeu des sons de SFA1 / SFA2 pour Hyper, hsfa_rejeu.h). Copie instanciable de l'emulateur HLE
// du DL-1425 de qs_c.cpp (superctr, Valley Bell ; licence BSD-3-Clause, comme qsoundhle.cpp de MAME) : l'etat du chip
// est dans un objet, la ROM d'echantillons est fournie par l'hote. Meme semantique que le qsound_hle_device de MAME
// utilise par le fork (2e QSound « qsound_hsfa ») : en particulier la banque est lue sans tester le bit 15.
// Un echantillon toutes les 2496 periodes de 60 MHz (24 038 Hz). C++98.
#pragma once
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

namespace hsfa_qs {

#define HSFA_QS_CLAMP(x, lo, hi) (((x) > (hi)) ? (hi) : (((x) < (lo)) ? (lo) : (x)))

static const int16_t dry_mix[33] = {
	-16384,-16384,-16384,-16384,-16384,-16384,-16384,-16384,
	-16384,-16384,-16384,-16384,-16384,-16384,-16384,-16384,
	-16384,-14746,-13107,-11633,-10486,-9175,-8520,-7209,
	-6226,-5226,-4588,-3768,-3277,-2703,-2130,-1802,
	0
};
static const int16_t wet_mix[33] = {
	0,-1638,-1966,-2458,-2949,-3441,-4096,-4669,
	-4915,-5120,-5489,-6144,-7537,-8831,-9339,-9830,
	-10240,-10322,-10486,-10568,-10650,-11796,-12288,-12288,
	-12534,-12648,-12780,-12829,-12943,-13107,-13418,-14090,
	-16384
};
static const int16_t linear_mix[33] = {
	-16379,-16338,-16257,-16135,-15973,-15772,-15531,-15251,
	-14934,-14580,-14189,-13763,-13303,-12810,-12284,-11729,
	-11729,-11144,-10531,-9893,-9229,-8543,-7836,-7109,
	-6364,-5604,-4829,-4043,-3246,-2442,-1631,-817,
	0
};
static const int16_t filter_data[5][95] = {
	{	0,0,0,6,44,-24,-53,-10,59,-40,-27,1,39,-27,56,127,174,36,-13,49,
		212,142,143,-73,-20,66,-108,-117,-399,-265,-392,-569,-473,-71,95,-319,-218,-230,331,638,
		449,477,-180,532,1107,750,9899,3828,-2418,1071,-176,191,-431,64,117,-150,-274,-97,-238,165,
		166,250,-19,4,37,204,186,-6,140,-77,-1,1,18,-10,-151,-149,-103,-9,55,23,
		-102,-97,-11,13,-48,-27,5,18,-61,-30,64,72,0,0,0 },
	{	0,0,0,85,24,-76,-123,-86,-29,-14,-20,-7,6,-28,-87,-89,-5,100,154,160,
		150,118,41,-48,-78,-23,59,83,-2,-176,-333,-344,-203,-66,-39,2,224,495,495,280,
		432,1340,2483,5377,1905,658,0,97,347,285,35,-95,-78,-82,-151,-192,-171,-149,-147,-113,
		-22,71,118,129,127,110,71,31,20,36,46,23,-27,-63,-53,-21,-19,-60,-92,-69,
		-12,25,29,30,40,41,29,30,46,39,-15,-74,0,0,0 },
	{	0,0,0,23,42,47,29,10,2,-14,-54,-92,-93,-70,-64,-77,-57,18,94,113,
		87,69,67,50,25,29,58,62,24,-39,-131,-256,-325,-234,-45,58,78,223,485,496,
		127,6,857,2283,2683,4928,1328,132,79,314,189,-80,-90,35,-21,-186,-195,-99,-136,-258,
		-189,82,257,185,53,41,84,68,38,63,77,14,-60,-71,-71,-120,-151,-84,14,29,
		-8,7,66,69,12,-3,54,92,52,-6,-15,-2,0,0,0 },
	{	0,0,0,2,-28,-37,-17,0,-9,-22,-3,35,52,39,20,7,-6,2,55,121,
		129,67,8,1,9,-6,-16,16,66,96,118,130,75,-47,-92,43,223,239,151,219,
		440,475,226,206,940,2100,2663,4980,865,49,-33,186,231,103,42,114,191,184,116,29,
		-47,-72,-21,60,96,68,31,32,63,87,76,39,7,14,55,85,67,18,-12,-3,
		21,34,29,6,-27,-49,-37,-2,16,0,-21,-16,0,0,0 },
	{	0,0,0,48,7,-22,-29,-10,24,54,59,29,-36,-117,-185,-213,-185,-99,13,90,
		83,24,-5,23,53,47,38,56,67,57,75,107,16,-242,-440,-355,-120,-33,-47,152,
		501,472,-57,-292,544,1937,2277,6145,1240,153,47,200,152,36,64,134,74,-82,-208,-266,
		-268,-188,-42,65,74,56,89,133,114,44,-3,-1,17,29,29,-2,-76,-156,-187,-151,
		-85,-31,-5,7,20,32,24,-5,-20,6,48,62,0,0,0 }
};
static const int16_t filter_data2[209] = {
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,
	-371,-196,-268,-512,-303,-315,-184,-76,276,-256,298,196,990,236,1114,-126,4377,6549,791,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,-16384,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
};
static const int16_t adpcm_step[16] = { 154, 154, 128, 102, 77, 58, 58, 58, 58, 58, 58, 58, 77, 102, 128, 154 };

enum { ST_INIT1 = 0x288, ST_INIT2 = 0x61a, ST_REFRESH1 = 0x039, ST_REFRESH2 = 0x04f, ST_NORMAL1 = 0x314, ST_NORMAL2 = 0x6b2 };

struct voix { uint16_t bank; int16_t addr; uint16_t phase; uint16_t rate; int16_t loop_len; int16_t end_addr; int16_t volume; int16_t echo; };
struct adpcm { uint16_t start_addr; uint16_t end_addr; uint16_t bank; int16_t volume; uint16_t flag; int16_t cur_vol; int16_t step_size; uint16_t cur_addr; };
struct fir { int32_t tap_count; int32_t delay_pos; int16_t table_pos; int16_t taps[95]; int16_t delay_line[95]; };
struct retard { int16_t delay; int16_t volume; int16_t write_pos; int16_t read_pos; int16_t delay_line[51]; };
struct echo_t { uint16_t end_pos; int16_t feedback; int16_t length; int16_t last_sample; int16_t delay_line[1024]; int16_t delay_pos; };

// etat complet (sauvegarde d'un bloc)
struct etat_t {
	int16_t out[2];
	voix voice[16];
	adpcm adp[3];
	uint16_t voice_pan[19];
	int16_t voice_output[19];
	echo_t echo;
	fir filter[2], alt_filter[2];
	retard wet[2], dry[2];
	uint16_t state, next_state, delay_update, data_latch;
	int32_t state_counter;
	uint8_t ready_flag, pad[3];
};

class qsound {
public:
	etat_t c;
	const uint8_t *rom;           // ROM d'echantillons (taille puissance de 2, lecture en miroir comme MAME)
	uint32_t masque;

	qsound() : rom(NULL), masque(0)
	{
		memset(&c, 0, sizeof(c));
		for (int i = 0; i < 33; i++) {
			pan[0][0][i] = dry_mix[i]; pan[1][0][i] = dry_mix[32 - i];
			pan[0][1][i] = wet_mix[i]; pan[1][1][i] = wet_mix[32 - i];
			pan[0][0][i + 0x30] = linear_mix[i]; pan[1][0][i + 0x30] = linear_mix[32 - i];
		}
		carte();
	}
	void fixe_rom(const uint8_t *r, uint32_t taille) { rom = r; masque = taille ? taille - 1 : 0; }
	void reset() { c.ready_flag = 0; c.out[0] = c.out[1] = 0; c.state = 0; c.state_counter = 0; }
	void ecrit(uint8_t reg, uint16_t val)
	{
		uint16_t *d = reg_map[reg];
		if (d) *d = val;
		c.ready_flag = 0;
	}
	void echantillon()
	{
		switch (c.state) {
		default: case ST_INIT1: case ST_INIT2: etat_init(); return;
		case ST_REFRESH1: refresh1(); return;
		case ST_REFRESH2: refresh2(); return;
		case ST_NORMAL1: case ST_NORMAL2: normal(); return;
		}
	}

private:
	int16_t pan[2][2][98];
	uint16_t *reg_map[256];

	void carte()
	{
		for (int i = 0; i < 256; i++) reg_map[i] = NULL;
		for (int i = 0; i < 16; i++) {
			reg_map[(i << 3) + 0] = &c.voice[(i + 1) % 16].bank;
			reg_map[(i << 3) + 1] = (uint16_t*)&c.voice[i].addr;
			reg_map[(i << 3) + 2] = &c.voice[i].rate;
			reg_map[(i << 3) + 3] = &c.voice[i].phase;
			reg_map[(i << 3) + 4] = (uint16_t*)&c.voice[i].loop_len;
			reg_map[(i << 3) + 5] = (uint16_t*)&c.voice[i].end_addr;
			reg_map[(i << 3) + 6] = (uint16_t*)&c.voice[i].volume;
			reg_map[i + 0x80] = &c.voice_pan[i];
			reg_map[i + 0xba] = (uint16_t*)&c.voice[i].echo;
		}
		for (int i = 0; i < 3; i++) {
			reg_map[(i << 2) + 0xca] = &c.adp[i].start_addr;
			reg_map[(i << 2) + 0xcb] = &c.adp[i].end_addr;
			reg_map[(i << 2) + 0xcc] = &c.adp[i].bank;
			reg_map[(i << 2) + 0xcd] = (uint16_t*)&c.adp[i].volume;
			reg_map[i + 0xd6] = &c.adp[i].flag;
			reg_map[i + 0x90] = &c.voice_pan[16 + i];
		}
		reg_map[0x93] = (uint16_t*)&c.echo.feedback;
		reg_map[0xd9] = &c.echo.end_pos;
		reg_map[0xe2] = &c.delay_update;
		reg_map[0xe3] = &c.next_state;
		for (int i = 0; i < 2; i++) {
			reg_map[(i << 1) + 0xda] = (uint16_t*)&c.filter[i].table_pos;
			reg_map[(i << 1) + 0xde] = (uint16_t*)&c.wet[i].delay;
			reg_map[(i << 1) + 0xe4] = (uint16_t*)&c.wet[i].volume;
			reg_map[(i << 1) + 0xdb] = (uint16_t*)&c.alt_filter[i].table_pos;
			reg_map[(i << 1) + 0xdf] = (uint16_t*)&c.dry[i].delay;
			reg_map[(i << 1) + 0xe5] = (uint16_t*)&c.dry[i].volume;
		}
	}
	// qsoundhle.cpp : bank &= 0x7fff ; read_byte((bank << 16) | address) (ROM en miroir)
	int16_t lit(uint16_t bank, uint16_t addr) const
	{
		if (!rom) return 0;
		uint32_t a = ((uint32_t(bank) & 0x7FFF) << 16) | addr;
		return int16_t(uint16_t(rom[a & masque]) << 8);
	}
	static const int16_t *table_filtre(uint16_t off)
	{
		if (off >= 0xf2e && off < 0xfff) return &filter_data2[off - 0xf2e];
		int i = (int(off) - 0xd53) / 95;
		if (i >= 0 && i < 5) return filter_data[i];
		return NULL;
	}
	void etat_init()
	{
		int mode = (c.state == ST_INIT2) ? 1 : 0;
		if (c.state_counter >= 2) { c.state_counter = 0; c.state = c.next_state; return; }
		else if (c.state_counter == 1) { c.state_counter++; return; }
		memset(c.voice, 0, sizeof(c.voice)); memset(c.adp, 0, sizeof(c.adp));
		memset(c.filter, 0, sizeof(c.filter)); memset(c.alt_filter, 0, sizeof(c.alt_filter));
		memset(c.wet, 0, sizeof(c.wet)); memset(c.dry, 0, sizeof(c.dry)); memset(&c.echo, 0, sizeof(c.echo));
		for (int i = 0; i < 19; i++) { c.voice_pan[i] = 0x120; c.voice_output[i] = 0; }
		for (int i = 0; i < 16; i++) c.voice[i].bank = 0x8000;
		for (int i = 0; i < 3; i++) c.adp[i].bank = 0x8000;
		if (mode == 0) {
			c.wet[0].delay = 0; c.dry[0].delay = 46; c.wet[1].delay = 0; c.dry[1].delay = 48;
			c.filter[0].table_pos = 0xdb2; c.filter[1].table_pos = 0xe11;
			c.echo.end_pos = 0x554 + 6; c.next_state = ST_REFRESH1;
		} else {
			c.wet[0].delay = 1; c.dry[0].delay = 0; c.wet[1].delay = 0; c.dry[1].delay = 0;
			c.filter[0].table_pos = 0xf73; c.filter[1].table_pos = 0xfa4;
			c.alt_filter[0].table_pos = 0xf73; c.alt_filter[1].table_pos = 0xfa4;
			c.echo.end_pos = 0x53c + 6; c.next_state = ST_REFRESH2;
		}
		c.wet[0].volume = 0x3fff; c.dry[0].volume = 0x3fff; c.wet[1].volume = 0x3fff; c.dry[1].volume = 0x3fff;
		c.delay_update = 1; c.ready_flag = 0; c.state_counter = 1;
	}
	void refresh1()
	{
		for (int ch = 0; ch < 2; ch++) {
			c.filter[ch].delay_pos = 0; c.filter[ch].tap_count = 95;
			const int16_t *t = table_filtre(c.filter[ch].table_pos);
			if (t) memcpy(c.filter[ch].taps, t, 95 * sizeof(int16_t));
		}
		c.state = c.next_state = ST_NORMAL1;
	}
	void refresh2()
	{
		for (int ch = 0; ch < 2; ch++) {
			c.filter[ch].delay_pos = 0; c.filter[ch].tap_count = 45;
			const int16_t *t = table_filtre(c.filter[ch].table_pos);
			if (t) memcpy(c.filter[ch].taps, t, 45 * sizeof(int16_t));
			c.alt_filter[ch].delay_pos = 0; c.alt_filter[ch].tap_count = 44;
			t = table_filtre(c.alt_filter[ch].table_pos);
			if (t) memcpy(c.alt_filter[ch].taps, t, 44 * sizeof(int16_t));
		}
		c.state = c.next_state = ST_NORMAL2;
	}
	int16_t pcm(int n, int32_t *echo_out)
	{
		voix *v = &c.voice[n];
		int16_t output = int16_t((v->volume * lit(v->bank, uint16_t(v->addr))) >> 14);
		*echo_out += (output * v->echo) << 2;
		int32_t np = v->rate + ((v->addr << 12) | (v->phase >> 4));
		if ((np >> 12) >= v->end_addr) np -= (v->loop_len << 12);
		np = HSFA_QS_CLAMP(np, -0x8000000, 0x7FFFFFF);
		v->addr = int16_t(np >> 12);
		v->phase = uint16_t((np << 4) & 0xffff);
		return output;
	}
	void adpcm_maj(int n, int nibble)
	{
		adpcm *v = &c.adp[n];
		int8_t step;
		if (!nibble) {
			if (v->cur_addr == v->end_addr) v->cur_vol = 0;
			if (v->flag) { c.voice_output[16 + n] = 0; v->flag = 0; v->step_size = 10; v->cur_vol = v->volume; v->cur_addr = v->start_addr; }
			step = int8_t(lit(v->bank, v->cur_addr) >> 8);
		} else step = int8_t(lit(v->bank, v->cur_addr++) >> 4);
		step >>= 4;
		int32_t delta = ((1 + abs(step << 1)) * v->step_size) >> 1;
		if (step <= 0) delta = -delta;
		delta += c.voice_output[16 + n];
		delta = HSFA_QS_CLAMP(delta, -32768, 32767);
		c.voice_output[16 + n] = int16_t((delta * v->cur_vol) >> 16);
		v->step_size = int16_t((adpcm_step[8 + step] * v->step_size) >> 6);
		v->step_size = HSFA_QS_CLAMP(v->step_size, 1, 2000);
	}
	static int16_t echo(echo_t *r, int32_t input)
	{
		int32_t old_sample = r->delay_line[r->delay_pos];
		int32_t last_sample = r->last_sample;
		r->last_sample = int16_t(old_sample);
		old_sample = (old_sample + last_sample) >> 1;
		int32_t ns = input + ((old_sample * r->feedback) << 2);
		r->delay_line[r->delay_pos++] = int16_t(ns >> 16);
		if (r->delay_pos >= r->length) r->delay_pos = 0;
		return int16_t(old_sample);
	}
	static int32_t applique_fir(fir *f, int16_t input)
	{
		int32_t output = 0, tap = 0;
		for (; tap < (f->tap_count - 1); tap++) {
			output -= (f->taps[tap] * f->delay_line[f->delay_pos++]) << 2;
			if (f->delay_pos >= f->tap_count - 1) f->delay_pos = 0;
		}
		output -= (f->taps[tap] * input) << 2;
		f->delay_line[f->delay_pos++] = input;
		if (f->delay_pos >= f->tap_count - 1) f->delay_pos = 0;
		return output;
	}
	static int32_t applique_retard(retard *d, int32_t input)
	{
		d->delay_line[d->write_pos++] = int16_t(input >> 16);
		if (d->write_pos >= 51) d->write_pos = 0;
		int32_t output = d->delay_line[d->read_pos++] * d->volume;
		if (d->read_pos >= 51) d->read_pos = 0;
		return output;
	}
	static void maj_retard(retard *d)
	{
		int16_t nr = int16_t((d->write_pos - d->delay) % 51);
		if (nr < 0) nr += 51;
		d->read_pos = nr;
	}
	void normal()
	{
		int32_t echo_input = 0;
		c.ready_flag = 0x80;
		if (c.state == ST_NORMAL2) c.echo.length = int16_t(c.echo.end_pos - 0x53c);
		else c.echo.length = int16_t(c.echo.end_pos - 0x554);
		c.echo.length = HSFA_QS_CLAMP(c.echo.length, 0, 1024);
		for (int v = 0; v < 16; v++) c.voice_output[v] = pcm(v, &echo_input);
		adpcm_maj(c.state_counter % 3, c.state_counter / 3);
		int16_t eo = echo(&c.echo, echo_input);
		for (int ch = 0; ch < 2; ch++) {
			int32_t wet = (ch == 1) ? eo << 14 : 0;
			int32_t dry = (ch == 0) ? eo << 14 : 0;
			for (int v = 0; v < 19; v++) {
				uint16_t pi = uint16_t(c.voice_pan[v] - 0x110);
				if (pi > 97) pi = 97;
				dry -= (c.voice_output[v] * pan[ch][0][pi]);
				wet -= (c.voice_output[v] * pan[ch][1][pi]);
			}
			dry = HSFA_QS_CLAMP(dry, -0x1fffffff, 0x1fffffff) << 2;
			wet = HSFA_QS_CLAMP(wet, -0x1fffffff, 0x1fffffff) << 2;
			wet = applique_fir(&c.filter[ch], int16_t(wet >> 16));
			if (c.state == ST_NORMAL2) dry = applique_fir(&c.alt_filter[ch], int16_t(dry >> 16));
			int32_t output = applique_retard(&c.wet[ch], wet) + applique_retard(&c.dry[ch], dry);
			output = ((output + 0x2000) & ~0x3fff) >> 14;
			c.out[ch] = int16_t(HSFA_QS_CLAMP(output, -0x7fff, 0x7fff));
			if (c.delay_update) { maj_retard(&c.wet[ch]); maj_retard(&c.dry[ch]); }
		}
		c.delay_update = 0;
		c.state_counter++;
		if (c.state_counter > 5) { c.state_counter = 0; c.state = c.next_state; }
	}
};

} // namespace hsfa_qs
