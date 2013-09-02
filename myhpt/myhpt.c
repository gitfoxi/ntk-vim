// A version of hpt which accepts the full contents of a configuration file on
// stdin or can read it if given on the command line.
//
// This way you can send multi-line strings
#include <stdio.h>

#include "tpi_c.h"
#include "adiUserI.h"
#include "ci_types.h"
#include "libcicpi.h"
#include "stdbool.h"

void usage() {
    fprintf(stderr,
"Usage:\n\
\n\
    myhpt [file]\n\
    myhpt < file\n\
\n\
Input should be an HP (Agilent/Verigy/Advantest) 93k configuration file.\n\
You can give the input as a filename on the command line or pipe it through\n\
stdin.\n\
\n\
If the filename is like:\n\
\n\
    file.gz\n\
    file.bz2\n\
    file.xz\n\
\n\
then the appropriate tool will be used to send a decompressed stream.\n\
smarTest must be running or expect a nasty crash.\n\
");
}


// Open a possibly-compressed file for reading using the file extension to
// select a decompression tool
FILE* fopen_compressed(char *filename) {
    int len;
    char* command = NULL;
    bool use_pipe = true;
    FILE* f;

    len = strlen(filename);

    if(memcmp(filename + len - 3, ".gz", 3) == 0) {
        asprintf(&command, "/usr/bin/gzip -dc %s", filename);
    }
    else if(memcmp(filename + len - 3, ".bz2", 4) == 0) {
        asprintf(&command, "bzip2 -dc %s", filename);
    }
    else if(memcmp(filename + len - 3, ".bz2", 3) == 0) {
        asprintf(&command, "xz -dc %s", filename);
    }
    else {
        use_pipe = false;
    }

    if(use_pipe) {
        f = popen(command, "r");
        if(f == NULL) {
            perror(command);
        }
    }
    else {
        f = fopen(filename, "rt");
        if(f == NULL) {
            perror(command);
        }
    }
        
    if(command) {
        free(command);
    }

    return f;
}

int main(int argc, char* argv[])
{
    FILE *fin;

    if(argc == 1) {
        fin = stdin;
    }
    else if(argc == 2) {
        if(argv[1][0] == '-') {
            usage();
            exit(1);
        }
        fin = fopen_compressed(argv[1]);
        if(fin == NULL) {
            fprintf(stderr, "Error: Failed to open file: %s\n", argv[1]);
            usage();
            exit(1);
        }
    }
    else {
        usage();
        exit(1);
    }

    HpInit();

    char *task_str;
    char answ_str[65535];  // TODO: What is maximum answ_str length?
    INT32 task_len, answ_len, ret_state;
    char *bindata_start;
    size_t n;
    int bindata_len;
    char bindata_clen[10];
    int read_len;

    while(!feof(fin)) {
        answ_len = sizeof(answ_str);
        task_str = NULL;  // getline will allocate
        n = 0;
        task_len = getline(&task_str, &n, fin);
        if(task_len <= 0) {
            // EOF: Shutdown
            exit(0);
        }
        bindata_start = strstr(task_str, "#90");
        if(memcmp("hp93000", task_str, strlen("hp93000")) == 0) {
            printf("Discarding %s", task_str);
            free(task_str);
            continue;
        }

        if(bindata_start) {
            memcpy(bindata_clen, bindata_start + 2, 9);
            bindata_clen[9] = 0;
            bindata_len = atol(bindata_clen);
            printf("bindata_len: %d\n", bindata_len);
            task_str = realloc(task_str, task_len + bindata_len + 1024);
            // I'm worried that I don't quite understand why the magic number
            // is 12 but, yay, I just loaded a timing file.
            read_len = (int)(bindata_len - task_len + (bindata_start - task_str + 12));
            printf("reading %d more bytes\n", read_len);
            task_len += fread(task_str + task_len, 1, read_len, fin);
        }

        printf("task_str: ");
        fwrite(task_str, task_len, 1, stdout);
        printf("task_len: %d\n", (int)task_len);
        // TODO: 0 : ok, -1 : warning, -2 to -999 : error, -1000 break (whatever that means)
        HpFwTask(task_str, &task_len, answ_str, &answ_len, &ret_state);
        *(answ_str + answ_len) = 0;
        printf("Answer: %s\n", answ_str);
        printf("Answer Length: %d\n", (int)answ_len);
        printf("Return: %d\n", (int)ret_state);
        task_len = 0;
        answ_len = sizeof(answ_str);
        fflush(fin);
        if(task_str) {
            free(task_str);
        }
    }

    exit(CI_CALL_PASS);

    HpTerm();
}
