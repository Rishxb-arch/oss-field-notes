// LD_PRELOAD shim: deny AMX tile permission (arch_prctl ARCH_REQ_XCOMP_PERM) so ORT's MLAS
// falls back from AMX kernels. Everything else passes through to the real syscall().
#define _GNU_SOURCE
#include <stdarg.h>
#include <errno.h>
#include <dlfcn.h>
#include <sys/syscall.h>
#include <stdio.h>
long syscall(long n, ...) {
  va_list ap; va_start(ap, n);
  long a[6]; for (int i = 0; i < 6; i++) a[i] = va_arg(ap, long);
  va_end(ap);
  if (n == SYS_arch_prctl && a[0] == 0x1023) { fprintf(stderr, "[noamx] denied ARCH_REQ_XCOMP_PERM\n"); errno = EPERM; return -1; }
  static long (*real)(long, ...) = 0;
  if (!real) real = (long (*)(long, ...))dlsym(RTLD_NEXT, "syscall");
  return real(n, a[0], a[1], a[2], a[3], a[4], a[5]);
}
