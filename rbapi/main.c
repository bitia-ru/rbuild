#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <errno.h>
#include "json.h"


extern char** environ;


void usage(const char* arg, FILE* stream)
{
  fprintf(stream, "%s <server> <funcname> [args...]\n", arg);
}


int exchange(char* addr, char* data, char** resp, size_t* resp_len)
{
  int sock;
  size_t i;
  char* port;
  struct addrinfo *info;
  struct sockaddr *seladdr;
  size_t addr_len = strlen(addr);
  struct addrinfo hints;

  memset(&hints, 0, sizeof(struct addrinfo));
  hints.ai_family = AF_INET;

  for (i = 0; i < addr_len; i++) {
    if (addr[i] == ':') {
      addr[i] = '\0';
      port = addr+i+1;
      break;
    }
  }

  if (i == addr_len) {
    fprintf(stderr, "Bad argument 'server': should be like hostname:port");
    exit(EINVAL);
  }

  if (getaddrinfo(addr, port, &hints, &info) != 0) {
    perror("Bad argument 'server'");
    exit(errno);
  }

  seladdr = info->ai_addr;

  sock = socket(AF_INET, SOCK_STREAM, 0);

  if(sock < 0) {
    perror("Can't create socket");
    exit(errno);
  }

  if (connect(sock, seladdr, sizeof(*seladdr)) < 0) {
    fprintf (
             stderr,
             "Can't establish connection with %s:%s: %s\n",
             addr,
             port,
             strerror(errno)
            );
    exit(errno);
  }

  size_t data_len = strlen(data);

  size_t res = send(sock, &data_len, 4, 0);

  if (res != 4) {
    perror("Communication error");
    exit(errno);
  }

  char ch;

  res = recv(sock, &ch, 1, 0);

  if (res == -1 || ch != 'Y') {
    perror("Communication error");
    exit(errno);
  }

  for (size_t sended = 0; sended < data_len;) {
    res = send(sock, data+sended, data_len-sended, 0);

    if (res == -1) {
      perror("Communication error");
      exit(errno);
    }

    sended += res;
  }

  res = recv(sock, &data_len, 4, 0);

  if (res != 4) {
    perror("Communication error");
    exit(errno);
  }

  if (data_len > 1024*1024) {
    fprintf(stderr, "Response too long");
    exit(EREMOTEIO);
  }

  ch = 'Y', res = send(sock, &ch, 1, 0);

  if (res != 1)
    exit(1);

  *resp = malloc(data_len+1);
  *resp_len = data_len;

  for (size_t sended = 0; sended < data_len;) {
    res = recv(sock, (*resp)+sended, data_len-sended, 0);

    if (res == -1) {
      perror("Communication error");
      exit(errno);
    }

    sended += res;
  }

  (*resp)[data_len] = '\0';

  free(data);
  freeaddrinfo(info);

  return 0;
}


int main(int argc, char* argv[])
{
  if (argc < 3) {
    usage(argv[0], stderr);
    exit(EINVAL);
  }

  JsonNode* msg = json_mkobject();

  char* addr = argv[1];
  char* funcname = argv[2];

  argv = argv+3;
  argc -= 3;

  json_append_member(msg, "funcname", json_mkstring(funcname));

  JsonNode* args = json_mkarray();

  for (int i = 0; i < argc; i++)
    json_append_element(args, json_mkstring(argv[i]));

  json_append_member(msg, "args", args);

  JsonNode* env = json_mkobject();

  for (size_t i = 0; environ[i]; i++) {
    char* envstr = environ[i];
    size_t envstr_len = strlen(envstr), j;

    for (j = 0; j < envstr_len; j++) {
      if (envstr[j] == '=') {
        envstr[j] = '\0';
        json_append_member(env, envstr, json_mkstring(envstr+j+1));
        break;
      }
    }

    if (j == envstr_len) {
      fprintf(stderr, "Bad environment.");
      exit(EINVAL);
    }
  }

  json_append_member(msg, "env", env);

  char* msg_str = json_stringify(msg, "  ");

  char* resp;
  size_t resp_len;

  if (exchange(addr, msg_str, &resp, &resp_len) != 0) {
    perror("Communication error");
    exit(errno);
  }

  JsonNode* jresp = json_decode(resp);

  if (jresp == NULL) {
    fprintf(stderr, "Response error: JSON validation failed");
    exit(EINVAL);
  }

  JsonNode* jretval = json_find_member(jresp, "retval");

  if (jretval == NULL || jretval->tag != JSON_NUMBER) {
    fprintf(stderr, "Response error: retval field not found");
    exit(EINVAL);
  }

  JsonNode* jret_stderr = json_find_member(jresp, "stderr");

  if (jret_stderr != NULL) {
    if (jret_stderr->tag != JSON_STRING) {
      fprintf(stderr, "Response error: stderr field should be string");
      exit(EINVAL);
    }

    fputs(jret_stderr->string_, stderr);
  }

  JsonNode* jret_stdout = json_find_member(jresp, "stdout");

  if (jret_stdout != NULL) {
    if (jret_stdout->tag != JSON_STRING) {
      fprintf(stderr, "Response error: stderr field should be string");
      exit(EINVAL);
    }

    fputs(jret_stdout->string_, stdout);
  }

  int retval = (int)jretval->number_;

  json_delete(msg);

  return retval;
}

