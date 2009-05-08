// get-volume is a small utility for ALSA mixer volume, written for being used
// in Conky.
//
// This code is in Public Domain
//
// Reference:
//  http://www.alsa-project.org/alsa-doc/alsa-lib/index.html
//
// Author:
//  2009 Yu-Jie Lin
//
// Compile using:
//  gcc -lasound -o get-volume get-volume.c

#include <stdio.h>
#include "alsa/asoundlib.h"

const char *ATTACH = "default";
const snd_mixer_selem_channel_id_t CHANNEL = SND_MIXER_SCHN_FRONT_LEFT;
const char *SELEM_NAME = "Master";

void error_close_exit(char *errmsg, int err, snd_mixer_t *h_mixer) {
	if (err == 0)
		fprintf(stderr, errmsg);
	else
		fprintf(stderr, errmsg, snd_strerror(err));
	if (h_mixer != NULL)
		snd_mixer_close(h_mixer);
	exit(EXIT_FAILURE);
	}

int main(int argc, char** argv) {
	int err;
	long vol;
	long vol_min, vol_max;
	int switch_value;
	snd_mixer_t *h_mixer;
	snd_mixer_selem_id_t *sid;
	snd_mixer_elem_t *elem ;

	if ((err = snd_mixer_open(&h_mixer, 1)) < 0)
		error_close_exit("Mixer open error: %s\n", err, NULL);

	if ((err = snd_mixer_attach(h_mixer, ATTACH)) < 0)
		error_close_exit("Mixer attach error: %s\n", err, h_mixer);

	if ((err = snd_mixer_selem_register(h_mixer, NULL, NULL)) < 0)
		error_close_exit("Mixer simple element register error: %s\n", err, h_mixer);

	if ((err = snd_mixer_load(h_mixer)) < 0)
		error_close_exit("Mixer load error: %s\n", err, h_mixer);

	snd_mixer_selem_id_alloca(&sid);
	snd_mixer_selem_id_set_index(sid, 0);
	snd_mixer_selem_id_set_name(sid, SELEM_NAME);
    
	if ((elem = snd_mixer_find_selem(h_mixer, sid)) == NULL)
		error_close_exit("Cannot find simple element\n", 0, h_mixer);

	if (argc != 2)
		error_close_exit("Missing (switch|volume) as argument\n", 0, NULL);

	if (strcmp(argv[1], "volume") == 0) {
		snd_mixer_selem_get_playback_volume(elem, CHANNEL, &vol);
		snd_mixer_selem_get_playback_volume_range(elem, &vol_min, &vol_max);
		printf("%3.0f%%", 100.0 * vol / vol_max);
		}
	else if (strcmp(argv[1], "switch") == 0) {
		snd_mixer_selem_get_playback_switch(elem, CHANNEL, &switch_value);
		printf("%s", (switch_value == 1) ? "ON" : "OFF");
		}
	else if (strcmp(argv[1], "on") == 0) {
		snd_mixer_selem_get_playback_switch(elem, CHANNEL, &switch_value);
		printf("%s", (switch_value == 1) ? "ON" : "");
		}
	else if (strcmp(argv[1], "off") == 0) {
		snd_mixer_selem_get_playback_switch(elem, CHANNEL, &switch_value);
		printf("%s", (switch_value == 1) ? "" : "OFF");
		}
	else
		error_close_exit("Invalid argument. Using (switch|volume)\n", 0, NULL);

	snd_mixer_close(h_mixer);
	return 0;
	}
