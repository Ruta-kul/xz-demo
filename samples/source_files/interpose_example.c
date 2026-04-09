/*
 * interpose_example.c -- EDUCATIONAL / INERT
 *
 * Demonstrates LD_PRELOAD-style symbol interposition by wrapping the
 * standard write() system call.  This technique is commonly used for:
 *   - Debugging / tracing (ltrace, libfaketime)
 *   - Sandboxing (libseccomp wrappers)
 *   - Instrumentation (coverage tools, fault injection)
 *
 * It is also a well-known attack vector: a malicious .so loaded via
 * LD_PRELOAD can silently intercept any dynamically-linked function.
 *
 * RELEVANCE TO THE XZ ATTACK
 * ---------------------------
 * The XZ backdoor did NOT use LD_PRELOAD directly.  Instead it abused
 * the IFUNC resolver mechanism (see ifunc_example.c) to achieve a
 * similar result: replacing a function pointer at load time.
 *
 * However, LD_PRELOAD interposition is a closely related pattern that
 * security scanners should also detect because:
 *   1. It can achieve the same effect (function hijacking) with less
 *      sophistication.
 *   2. Attackers may combine it with supply-chain compromises -- e.g.,
 *      a backdoored package installs a .so and adds it to /etc/ld.so.preload.
 *   3. Build systems that set LD_PRELOAD during `make check` or
 *      `make install` are suspicious.
 *
 * PATTERN MARKERS (what scanners should flag)
 * - Use of dlsym(RTLD_NEXT, ...) to obtain the "real" function pointer
 * - Shared libraries that define common libc symbols (write, read, open, ...)
 * - Build artifacts or install scripts that modify ld.so.preload
 * - Environment manipulation setting LD_PRELOAD or LD_LIBRARY_PATH
 *
 * THIS FILE
 * ---------
 * Wraps write() to prepend a harmless "[INTERPOSED]" tag to anything
 * written to stdout (fd 1).  All other file descriptors pass through
 * unmodified.  The wrapper calls the real write() via dlsym.
 *
 * Compile as shared library:
 *   gcc -shared -fPIC -Wall -Wextra -o interpose_example.so interpose_example.c -ldl
 *
 * Use with LD_PRELOAD:
 *   LD_PRELOAD=./interpose_example.so echo "hello world"
 *
 * Expected output:
 *   [INTERPOSED] hello world
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>

/* Type alias for the real write() signature */
typedef ssize_t (*real_write_t)(int fd, const void *buf, size_t count);

/*
 * Get a pointer to the real (libc) write() function.
 *
 * dlsym(RTLD_NEXT, "write") searches the next shared object in the
 * symbol resolution order -- i.e., the one that would have been found
 * if our interposer did not exist.
 *
 * SCANNER NOTE: dlsym(RTLD_NEXT, ...) is a strong indicator of symbol
 * interposition.  Flag any shared library that uses this pattern.
 */
static real_write_t get_real_write(void)
{
    static real_write_t real_fn = NULL;
    if (!real_fn) {
        real_fn = (real_write_t)dlsym(RTLD_NEXT, "write");
        if (!real_fn) {
            /* If dlsym fails we have no safe fallback; abort. */
            const char msg[] = "interpose_example: dlsym failed\n";
            /* Use syscall directly to avoid infinite recursion */
            syscall(1 /* SYS_write */, STDERR_FILENO, msg, sizeof(msg) - 1);
            _exit(1);
        }
    }
    return real_fn;
}

/*
 * Our interposed write().
 *
 * Because this symbol is named "write" and loaded via LD_PRELOAD, the
 * dynamic linker will resolve all write() calls to THIS function first.
 *
 * We add a harmless prefix to stdout writes and pass everything else
 * through unchanged.
 */
ssize_t write(int fd, const void *buf, size_t count)
{
    real_write_t real_write = get_real_write();

    /* Only interpose on stdout (fd 1) */
    if (fd == STDOUT_FILENO && count > 0) {
        const char prefix[] = "[INTERPOSED] ";
        /* Write the prefix first, then the original data */
        real_write(fd, prefix, sizeof(prefix) - 1);
    }

    /* Always call the real write() for the actual data */
    return real_write(fd, buf, count);
}

/*
 * Optional: constructor attribute runs when the .so is loaded.
 * Legitimate uses include one-time initialization.
 * Scanners should inspect __attribute__((constructor)) in shared libraries.
 */
__attribute__((constructor))
static void interpose_init(void)
{
    const char msg[] = "[interpose_example] loaded via LD_PRELOAD (educational)\n";
    real_write_t rw = get_real_write();
    rw(STDERR_FILENO, msg, sizeof(msg) - 1);
}
