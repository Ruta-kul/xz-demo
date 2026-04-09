/*
 * main.c -- A clean, normal C program.
 *
 * This file serves as a baseline for scanner comparison.  It contains
 * no suspicious patterns: no IFUNC, no dlsym, no eval, no obfuscation.
 */

#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    printf("Hello from the xz-bot clean project!\n");
    printf("This file is a baseline with no suspicious patterns.\n");
    return EXIT_SUCCESS;
}
