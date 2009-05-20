// Small utility to colorify the track information
//
// Shell.FM doesn't seem to be able to update the remaining second information.
//
// Using the following in shell-fm
//   np-file = /tmp/shell-fm-nowplaying
//   np-file-format = %t|%l|%a
//
// Using the following in conky
//   ${if_running shell-fm}${execp ~/bin/conky-shell-fm}$endif

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>

// For shell-fm
/*
const char *proc_path = "/proc/";
const char *cmdline = "/cmdline";
const size_t proc_len = 6;
const size_t cmdline_len = 8;
*/
const char *nowplaying_path = "/tmp/shell-fm-nowplaying";
const char *sep = "|";

/*
char *get_path_to_cmdline(char *pid) {
	size_t result_len = proc_len + strlen(pid) + cmdline_len;
	char *result;

	result = malloc((result_len + 1) * sizeof *result);
	strcpy(result, proc_path);
	strcat(result, pid);
	strcat(result, cmdline);
	result[result_len] = '\0';
	return result;
	}

bool shellfm_running() {
	struct dirent *dp;
	DIR *dir = opendir(proc_path);
	int i;
	char *cmdline_path;
	FILE *f;
	char cmdline[9];
	bool found = false;

	while ((dp=readdir(dir)) != NULL && !found) {
		// Find directory name is in all numbers
		for (i=0; i<strlen(dp->d_name); i++)
			if (dp->d_name[i] < '0' || dp->d_name[i] > '9')
				break;
		if (i < strlen(dp->d_name))
			continue;
		cmdline_path = get_path_to_cmdline(dp->d_name);
		// Check if this is shell-fm
		if ((f = fopen(cmdline_path, "r")) != (FILE *) 0)
			if (fgets(cmdline, sizeof(cmdline), f) != NULL)
				if (strcmp(cmdline, "shell-fm") == 0)
					found = true;
		fclose(f);
		free(cmdline_path);
		cmdline_path = NULL;
		}
	closedir(dir);
	return found;
	}
*/
void do_shellfm() {
	FILE *f;
	char buffer[300];
	char *bufp = buffer;
	char **bp = &bufp;
	char *tok;
	const int info_len = 3;
	char *info[info_len];
	int i;

	if ((f = fopen(nowplaying_path, "r")) == (FILE *) 0)
		return;
	if (fgets(buffer, 300, f) == NULL)
		goto f_close;

	i = -1;
	while (tok = strsep(bp, sep), ++i < info_len)
		info[i] = tok;
	printf("${alignc}${color lightgreen}Last.fm$color\n");
	printf("${alignc}${color red}%s$color\n", info[0]);
	printf("${alignc}${color green}%s$color\n", info[1]);
	printf("${alignc}${color cyan}%s$color\n", info[2]);
f_close:
	fclose(f);
	}

int main () {
//	if (shellfm_running())
		do_shellfm();
	return 0;
	}
