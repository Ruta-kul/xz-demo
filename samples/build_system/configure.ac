dnl ============================================================
dnl EDUCATIONAL SAMPLE - Safe configure.ac demonstrating where
dnl the XZ backdoor hooked into the build system.
dnl ============================================================

AC_INIT([xz-demo], [5.6.1], [demo@example.com])
AM_INIT_AUTOMAKE([foreign])
AC_PROG_CC

dnl === EDUCATIONAL NOTE ===
dnl The real attack added a call to the weaponized m4 macro here.
dnl When `./configure` ran, it would trigger the payload extraction
dnl chain, ultimately injecting the backdoor into the build.
dnl
dnl The innocent-looking line below is where it happened:
gl_BUILD_TO_HOST

dnl Normal build configuration continues...
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
