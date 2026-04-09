dnl ============================================================
dnl EDUCATIONAL SAMPLE - This macro is completely inert.
dnl It mimics the structure of the weaponized build-to-host.m4
dnl used in the XZ Utils backdoor (CVE-2024-3094).
dnl ============================================================

dnl In the real attack, this macro was modified to inject a
dnl malicious script during the build process. The key trick
dnl was hiding the payload extraction inside a legitimate-looking
dnl autoconf macro.

AC_DEFUN([gl_BUILD_TO_HOST],
[
  dnl === STAGE 1: Legitimate-looking host detection ===
  dnl This part looks normal - detecting build vs host platform
  gl_cv_build_to_host_cross=no
  case "$build" in
    *-*-linux*)
      gl_cv_build_to_host_cross=yes
      ;;
  esac

  dnl === EDUCATIONAL NOTE ===
  dnl In the real attack, the following section contained:
  dnl   eval $(cat some_test_file | tr "A-Z" "a-z" | ... | xz -d)
  dnl This extracted a hidden shell script from a "test fixture"
  dnl file, decoded it through multiple transformation stages,
  dnl and executed it to inject the backdoor into the build.
  dnl
  dnl The line below is a SAFE REPLACEMENT showing the pattern:
  gl_cv_host_info="Educational demo - no payload here"
  AC_MSG_NOTICE([build-to-host: $gl_cv_host_info])

  dnl === STAGE 2: The injection point ===
  dnl The real attack modified CFLAGS here to compile the
  dnl backdoor object file and link it into liblzma:
  dnl   CFLAGS="$CFLAGS -include backdoor.h"
  dnl   LIBS="$LIBS backdoor.o"
  AC_MSG_NOTICE([CFLAGS unchanged - this is a safe demo])
])
