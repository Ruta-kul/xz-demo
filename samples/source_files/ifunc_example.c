/*
 * ifunc_example.c -- EDUCATIONAL / INERT
 *
 * Demonstrates the GNU IFUNC (Indirect Function) mechanism that was abused
 * in the XZ Utils backdoor to hijack liblzma's crc64 function at runtime.
 *
 * WHAT IS IFUNC?
 * --------------
 * IFUNC is a GCC/glibc feature that lets a library defer function binding
 * until load time.  Instead of the linker resolving a symbol to a fixed
 * address, it calls a "resolver" function once (during dlopen / program
 * startup).  The resolver returns a pointer to the actual implementation.
 *
 * Legitimate uses:
 *   - CPU feature detection (pick SSE4.2 vs. AVX2 vs. NEON at runtime)
 *   - liblzma used IFUNC to choose optimized CRC implementations
 *
 * HOW THE REAL ATTACK ABUSED IFUNC
 * ---------------------------------
 * 1. liblzma defined crc64_resolve() as the IFUNC resolver for lzma_crc64().
 * 2. The backdoor replaced the resolver so that, in addition to returning
 *    the correct CRC function pointer, it also:
 *      a. Located OpenSSH's RSA_public_decrypt via the GOT (Global Offset
 *         Table), walking the link map from _dl_audit_symbind_alt.
 *      b. Overwrote the GOT entry to point to the attacker's function.
 *      c. The attacker's function checked incoming SSH certificates for a
 *         magic Ed448 public key; if found, it extracted and executed an
 *         arbitrary command payload -- giving the attacker pre-auth RCE.
 * 3. Because the resolver runs during library load (before main()), the
 *    hijack happened invisibly, before any application code executed.
 *
 * PATTERN MARKERS (what scanners should flag)
 * - IFUNC resolvers that do anything beyond returning a function pointer
 * - Resolver functions that reference dlsym, GOT, link_map, or audit hooks
 * - Resolver bodies longer than ~20 lines (legitimate ones are short)
 * - Resolver functions that write to memory outside their own stack frame
 *
 * THIS FILE
 * ---------
 * Implements a completely benign IFUNC for a custom my_strlen().  The
 * resolver picks between a naive byte-at-a-time implementation and a
 * slightly optimized version based on a fake "CPU feature" flag.
 *
 * Compile:  gcc -Wall -Wextra -o ifunc_example ifunc_example.c
 * Run:      ./ifunc_example
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>

/* -----------------------------------------------------------------------
 * Implementation A: naive byte-at-a-time strlen
 * ----------------------------------------------------------------------- */
static size_t my_strlen_naive(const char *s)
{
    size_t len = 0;
    while (s[len] != '\0')
        len++;
    return len;
}

/* -----------------------------------------------------------------------
 * Implementation B: slightly less naive (reads in 4-byte chunks)
 * Still portable, still safe -- just a different algorithm choice.
 * ----------------------------------------------------------------------- */
static size_t my_strlen_fast(const char *s)
{
    const char *p = s;
    /* Align to 4-byte boundary first */
    while (((uintptr_t)p & 3) && *p)
        p++;
    /* Then count in larger steps (simplified for clarity) */
    while (*p)
        p++;
    return (size_t)(p - s);
}

/* -----------------------------------------------------------------------
 * IFUNC Resolver
 *
 * This function is called ONCE by the dynamic linker when the program
 * (or shared library) is loaded.  It must return a pointer to the
 * chosen implementation.
 *
 * EDUCATIONAL NOTE:
 *   In the real XZ attack, the resolver for lzma_crc64() contained
 *   hundreds of bytes of injected machine code that:
 *     - walked the link_map to find loaded libraries
 *     - located RSA_public_decrypt in libcrypto
 *     - installed a GOT hook to intercept SSH authentication
 *   A legitimate resolver should ONLY inspect CPU feature flags and
 *   return a function pointer.  Anything else is a red flag.
 * ----------------------------------------------------------------------- */
static int fake_has_fast_cpu_feature(void)
{
    /*
     * In real code this would call __builtin_cpu_supports("sse4.2")
     * or read CPUID / getauxval(AT_HWCAP).
     *
     * We just return 1 so the "fast" path is always selected.
     */
    return 1;
}

typedef size_t (*strlen_fn)(const char *);

/*
 * The resolver function itself.
 * Note: the return type is a generic function pointer; glibc casts it.
 */
static strlen_fn my_strlen_resolve(void)
{
    if (fake_has_fast_cpu_feature())
        return my_strlen_fast;
    else
        return my_strlen_naive;
}

/*
 * Declare my_strlen as an IFUNC -- the linker will call my_strlen_resolve()
 * at load time and bind my_strlen to whatever pointer it returns.
 *
 * SCANNER NOTE: any ifunc declaration is worth inspecting.  Check that
 * the resolver body is short, pure, and only returns a function pointer.
 */
size_t my_strlen(const char *s) __attribute__((ifunc("my_strlen_resolve")));

/* -----------------------------------------------------------------------
 * main -- exercise the IFUNC-resolved function
 * ----------------------------------------------------------------------- */
int main(void)
{
    const char *test_strings[] = {
        "hello",
        "xz-bot educational sample",
        "",
        "The quick brown fox jumps over the lazy dog",
        NULL
    };

    printf("IFUNC Educational Example\n");
    printf("=========================\n\n");
    printf("my_strlen is resolved via __attribute__((ifunc(\"my_strlen_resolve\")))\n");
    printf("The resolver picked: %s\n\n",
           fake_has_fast_cpu_feature() ? "my_strlen_fast" : "my_strlen_naive");

    for (int i = 0; test_strings[i] != NULL; i++) {
        size_t our_len = my_strlen(test_strings[i]);
        size_t std_len = strlen(test_strings[i]);
        printf("  \"%s\"  ->  my_strlen=%zu  strlen=%zu  %s\n",
               test_strings[i], our_len, std_len,
               (our_len == std_len) ? "[OK]" : "[MISMATCH]");
    }

    printf("\nAll checks passed.  This IFUNC resolver is benign.\n");
    return 0;
}
