# ============================================================
# EDUCATIONAL SAMPLE - Safe Makefile.am showing suspicious hook
# patterns similar to the XZ Utils backdoor.
# ============================================================

lib_LTLIBRARIES = liblzma_demo.la

liblzma_demo_la_SOURCES = src/liblzma_demo.c

# === EDUCATIONAL NOTE ===
# In the real attack, a post-build hook was used to replace
# the compiled .o file with the backdoored version:
#
#   am__post_install_cmd = \
#     if test -f "$(backdoor_obj)"; then \
#       cp "$(backdoor_obj)" "$(DESTDIR)$(libdir)/liblzma.so.5.6.1"; \
#     fi
#
# The line below is a SAFE demonstration of the pattern:
am__post_install_cmd = @echo "DEMO: Post-install hook point (safe)"

# Normal test target
TESTS = tests/test_basic
