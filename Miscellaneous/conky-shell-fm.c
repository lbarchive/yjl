// Small utility to colorify the track information
//
// Using the following in shell-fm
//   np-file-format = %t|%l|%a
// and run with -i host -p port
//
// Using the following in conky
//   ${if_running shell-fm}${execp ~/bin/conky-shell-fm}$endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netdb.h>
#include <netinet/in.h>
#include <sys/socket.h>

const char *sep = "|";
const char *cmd_info = "info\n";

#define DEFAULT_HOST "localhost"  
#define DEFAULT_PORT "54311"

#define MAXDATASIZE 100 // max number of bytes we can get at once 

// get sockaddr, IPv4 or IPv6:
void *get_in_addr(struct sockaddr *sa)
{
    if (sa->sa_family == AF_INET) {
        return &(((struct sockaddr_in*)sa)->sin_addr);
    }

    return &(((struct sockaddr_in6*)sa)->sin6_addr);
}

char *fmt_time(int seconds, char * time) {
	int mm;
	int ss;

	mm = seconds / 60;
	ss = seconds - mm * 60;

	sprintf(time, "%02d:%02d", mm, ss);
	return time;
	}

void do_shellfm(char *buffer) {
	FILE *f;
	char *bufp = buffer;
	char **bp = &bufp;
	char *tok;
	const int info_len = 5;
	char *info[info_len];
	int i;
	int rm_time;
	int length;
	int el_time;
	char mmtime[7];
	char sstime[7];

	i = -1;
	while (tok = strsep(bp, sep), ++i < info_len)
		info[i] = tok;
	printf("${alignc}${color lightgreen}Last.fm$color\n");
	printf("${alignc}${color red}%s$color\n", info[0]);
	printf("${alignc}${color green}%s$color\n", info[1]);
	printf("${alignc}${color cyan}%s$color\n", info[2]);
	rm_time = atoi(info[3]);
	length = atoi(info[4]);
	el_time = length - rm_time;
	printf("${alignc}${color #ccddff}%s / %s$color\n", fmt_time(el_time, mmtime), fmt_time(length, sstime));
	}

int main(int argc, char *argv[]) {
    int sockfd, numbytes;  
    char buf[MAXDATASIZE];
    struct addrinfo hints, *servinfo, *p;
    int rv;
    char s[INET6_ADDRSTRLEN];

    if (argc == 2 && strcmp(argv[1], "-h") == 0) {
        fprintf(stderr,"usage: conky-shell-fm [hostname [port]]\ndefault: conky-shell-fm %s %s\n", DEFAULT_HOST, DEFAULT_PORT);
        exit(0);
    }

    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if ((rv = getaddrinfo((argc >= 2) ? argv[1] : DEFAULT_HOST,
			(argc == 3) ? argv[2] : DEFAULT_PORT, &hints, &servinfo)) != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
        return 1;
    }

    // loop through all the results and connect to the first we can
    for(p = servinfo; p != NULL; p = p->ai_next) {
        if ((sockfd = socket(p->ai_family, p->ai_socktype,
                p->ai_protocol)) == -1) {
            perror("conky-shell-fm: socket");
            continue;
        }

        if (connect(sockfd, p->ai_addr, p->ai_addrlen) == -1) {
            close(sockfd);
            perror("conky-shell-fm: connect");
            continue;
        }

        break;
    }

    if (p == NULL) {
        fprintf(stderr, "conky-shell-fm: failed to connect\n");
        return 2;
    }

    inet_ntop(p->ai_family, get_in_addr((struct sockaddr *)p->ai_addr),
            s, sizeof s);
    fprintf(stderr, "conky-shell-fm: connecting to %s\n", s);

    if ((numbytes = send(sockfd, cmd_info, strlen(cmd_info), 0)) == -1) {
        perror("conky-shell-fm: send");
        exit(1);
    }

    freeaddrinfo(servinfo); // all done with this structure

    if ((numbytes = recv(sockfd, buf, MAXDATASIZE-1, 0)) == -1) {
        perror("recv");
        exit(1);
    }

    buf[numbytes] = '\0';

    fprintf(stderr, "conky-shell-fm: received '%s'\n", buf);

    close(sockfd);

	do_shellfm(buf);

	return 0;
	}
