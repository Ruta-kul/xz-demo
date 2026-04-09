"""Pattern rule definitions for the XZ-Bot vulnerability scanner.

Defines ~25 rules across four categories modeled on the XZ Utils backdoor
(CVE-2024-3094) attack chain: supply chain compromise, backdoor insertion,
obfuscation techniques, and social engineering indicators.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from xz_bot.common.models import RiskLevel


@dataclass
class PatternRule:
    """A single detection rule backed by a compiled regex."""

    id: str  # e.g. "SC-001"
    name: str
    pattern: re.Pattern
    file_globs: list[str]
    severity: RiskLevel
    category: str
    description: str
    recommendation: str


# ---------------------------------------------------------------------------
# Supply Chain rules (SC-001 .. SC-008)
# ---------------------------------------------------------------------------
SUPPLY_CHAIN_RULES: list[PatternRule] = [
    PatternRule(
        id="SC-001",
        name="Build script injection hook",
        pattern=re.compile(
            r"am__post_install_cmd\s*=\s*.*(?:cp|mv|install)\b", re.IGNORECASE
        ),
        file_globs=["Makefile*", "*.am", "*.mk"],
        severity=RiskLevel.CRITICAL,
        category="supply_chain",
        description=(
            "A post-install hook in the build system copies or replaces "
            "files after compilation, a technique used in the XZ backdoor "
            "to swap legitimate object files with backdoored versions."
        ),
        recommendation="Audit all post-install hooks and verify no binary replacement occurs.",
    ),
    PatternRule(
        id="SC-002",
        name="Eval in Makefile / build script",
        pattern=re.compile(r"\beval\s+[\"\$\(]", re.IGNORECASE),
        file_globs=["Makefile*", "*.am", "*.mk", "*.m4", "configure*", "*.sh"],
        severity=RiskLevel.HIGH,
        category="supply_chain",
        description=(
            "Use of eval in build scripts can execute dynamically "
            "constructed commands, hiding malicious payloads."
        ),
        recommendation="Replace eval with explicit commands and audit the evaluated expression.",
    ),
    PatternRule(
        id="SC-003",
        name="Network fetch in build process",
        pattern=re.compile(
            r"\b(?:curl|wget|fetch|aria2c)\b.*(?:https?://|ftp://)", re.IGNORECASE
        ),
        file_globs=["Makefile*", "*.am", "*.mk", "*.m4", "configure*", "*.sh", "Dockerfile", "*.yml", "*.yaml"],
        severity=RiskLevel.HIGH,
        category="supply_chain",
        description=(
            "Build scripts downloading resources at build time can fetch "
            "malicious payloads from attacker-controlled servers."
        ),
        recommendation="Pin all external resources by hash and use vendored dependencies.",
    ),
    PatternRule(
        id="SC-004",
        name="Conditional dist/release behavior",
        pattern=re.compile(
            r"(?:if\s+.*\bdist\b|ifdef\s+DIST|dist[-_]hook)", re.IGNORECASE
        ),
        file_globs=["Makefile*", "*.am", "*.mk", "configure*"],
        severity=RiskLevel.MEDIUM,
        category="supply_chain",
        description=(
            "Build behavior that differs between development and distribution "
            "tarballs can hide backdoor injection that only activates in releases."
        ),
        recommendation="Ensure build behavior is identical between dev and dist builds.",
    ),
    PatternRule(
        id="SC-005",
        name="M4 macro abuse (gl_BUILD_TO_HOST)",
        pattern=re.compile(
            r"(?:gl_BUILD_TO_HOST|AC_DEFUN\(\[gl_BUILD_TO_HOST\])", re.IGNORECASE
        ),
        file_globs=["*.m4", "configure*", "*.ac"],
        severity=RiskLevel.CRITICAL,
        category="supply_chain",
        description=(
            "The gl_BUILD_TO_HOST macro was weaponized in the XZ backdoor "
            "to trigger payload extraction during configure."
        ),
        recommendation="Audit all custom m4 macros; compare against upstream gnulib.",
    ),
    PatternRule(
        id="SC-006",
        name="Test fixture reference in build logic",
        pattern=re.compile(
            r"(?:test.*/.*\.(?:xz|lzma|gz|bz2)|tests?[/_](?:files|fixtures|data)/)",
            re.IGNORECASE,
        ),
        file_globs=["Makefile*", "*.am", "*.mk", "*.m4", "configure*", "*.sh"],
        severity=RiskLevel.HIGH,
        category="supply_chain",
        description=(
            "Build scripts referencing compressed test fixtures may be "
            "extracting hidden payloads disguised as test data, as in the "
            "XZ attack."
        ),
        recommendation="Verify test fixtures are not consumed by build logic.",
    ),
    PatternRule(
        id="SC-007",
        name="Build script modifies CFLAGS/LDFLAGS",
        pattern=re.compile(
            r"(?:CFLAGS|LDFLAGS|LIBS)\s*[\+:]?=.*(?:-include|\.o\b|\.so\b)",
            re.IGNORECASE,
        ),
        file_globs=["Makefile*", "*.am", "*.mk", "*.m4", "configure*", "*.ac"],
        severity=RiskLevel.HIGH,
        category="supply_chain",
        description=(
            "Dynamically injecting object files or forced includes via "
            "compiler/linker flags can silently link backdoor code."
        ),
        recommendation="Audit all CFLAGS/LDFLAGS modifications for unexpected object files.",
    ),
    PatternRule(
        id="SC-008",
        name="Post-build hook (am__post_install)",
        pattern=re.compile(
            r"am__(?:post_install|install_exec|append)_cmd", re.IGNORECASE
        ),
        file_globs=["Makefile*", "*.am", "*.mk"],
        severity=RiskLevel.HIGH,
        category="supply_chain",
        description=(
            "Automake internal variables controlling post-install behavior "
            "can be hijacked to run arbitrary commands after build."
        ),
        recommendation="Ensure no custom am__ variables override automake internals.",
    ),
]

# ---------------------------------------------------------------------------
# Backdoor rules (BD-001 .. BD-008)
# ---------------------------------------------------------------------------
BACKDOOR_RULES: list[PatternRule] = [
    PatternRule(
        id="BD-001",
        name="IFUNC resolver usage",
        pattern=re.compile(
            r"(?:__attribute__\s*\(\s*\(\s*ifunc|\.type\s+\w+,\s*@gnu_indirect_function)",
            re.IGNORECASE,
        ),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc", "*.S", "*.s"],
        severity=RiskLevel.CRITICAL,
        category="backdoor",
        description=(
            "GNU IFUNC resolvers execute at load time before main() and "
            "can redirect function calls to malicious implementations."
        ),
        recommendation="Verify all IFUNC resolvers are legitimate and upstream-approved.",
    ),
    PatternRule(
        id="BD-002",
        name="dlsym with RTLD_NEXT",
        pattern=re.compile(r"dlsym\s*\(\s*RTLD_NEXT", re.IGNORECASE),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc"],
        severity=RiskLevel.HIGH,
        category="backdoor",
        description=(
            "Using dlsym(RTLD_NEXT, ...) to interpose library functions "
            "is a classic technique for hooking and redirecting calls."
        ),
        recommendation="Audit all RTLD_NEXT usage for unauthorized function interposition.",
    ),
    PatternRule(
        id="BD-003",
        name="GOT/PLT manipulation",
        pattern=re.compile(
            r"(?:_GLOBAL_OFFSET_TABLE_|\.got\.plt|got_entry|plt_entry|\.rela\.plt)",
            re.IGNORECASE,
        ),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc", "*.S", "*.s", "*.ld"],
        severity=RiskLevel.CRITICAL,
        category="backdoor",
        description=(
            "Direct manipulation of the Global Offset Table or Procedure "
            "Linkage Table enables redirecting function calls at runtime."
        ),
        recommendation="Ensure GOT/PLT references are limited to linker scripts and toolchain code.",
    ),
    PatternRule(
        id="BD-004",
        name="RSA_public_decrypt reference",
        pattern=re.compile(
            r"\bRSA_public_decrypt\b", re.IGNORECASE
        ),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc"],
        severity=RiskLevel.CRITICAL,
        category="backdoor",
        description=(
            "RSA_public_decrypt was the target function in the XZ backdoor. "
            "Its interception allowed the attacker to bypass SSH authentication."
        ),
        recommendation="Verify all RSA_public_decrypt calls are from legitimate OpenSSL usage.",
    ),
    PatternRule(
        id="BD-005",
        name="system() call in crypto/auth paths",
        pattern=re.compile(
            r"\bsystem\s*\(\s*[\"']", re.IGNORECASE
        ),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc"],
        severity=RiskLevel.HIGH,
        category="backdoor",
        description=(
            "Calls to system() in libraries, especially in crypto or "
            "authentication code paths, can execute arbitrary commands."
        ),
        recommendation="Replace system() with exec-family calls; never use in library code.",
    ),
    PatternRule(
        id="BD-006",
        name="Suspicious LD_PRELOAD reference",
        pattern=re.compile(r"\bLD_PRELOAD\b", re.IGNORECASE),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc", "*.sh", "Makefile*", "*.am"],
        severity=RiskLevel.HIGH,
        category="backdoor",
        description=(
            "LD_PRELOAD forces a shared library to load before all others, "
            "enabling function interposition across the entire process."
        ),
        recommendation="Remove LD_PRELOAD usage unless required for documented debugging.",
    ),
    PatternRule(
        id="BD-007",
        name="Embedded binary blob pattern",
        pattern=re.compile(
            r"(?:unsigned\s+char\s+\w+\[\]\s*=\s*\{(?:\s*0x[0-9a-fA-F]{2}\s*,){16,}|"
            r"\\x[0-9a-fA-F]{2}(?:\\x[0-9a-fA-F]{2}){15,})",
        ),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc"],
        severity=RiskLevel.HIGH,
        category="backdoor",
        description=(
            "Large embedded binary data arrays can contain obfuscated "
            "shellcode or encrypted backdoor payloads."
        ),
        recommendation="Audit all embedded binary data; verify provenance and purpose.",
    ),
    PatternRule(
        id="BD-008",
        name="Function pointer table modification",
        pattern=re.compile(
            r"(?:\.gnu\.hash|__libc_start_main|_dl_fixup|__tls_get_addr)",
            re.IGNORECASE,
        ),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc", "*.S", "*.s"],
        severity=RiskLevel.HIGH,
        category="backdoor",
        description=(
            "References to dynamic linker internals suggest attempts to "
            "hook or modify the program loading process."
        ),
        recommendation="Ensure dynamic linker symbol references are limited to toolchain code.",
    ),
]

# ---------------------------------------------------------------------------
# Obfuscation rules (OB-001 .. OB-006)
# ---------------------------------------------------------------------------
OBFUSCATION_RULES: list[PatternRule] = [
    PatternRule(
        id="OB-001",
        name="High-entropy data pattern",
        pattern=re.compile(
            r"[A-Za-z0-9+/=]{64,}"  # long base64-like strings
        ),
        file_globs=["*"],
        severity=RiskLevel.MEDIUM,
        category="obfuscation",
        description=(
            "Long strings of high-entropy data may contain encoded or "
            "encrypted payloads hidden in source files."
        ),
        recommendation="Decode and audit all high-entropy strings; verify they are legitimate.",
    ),
    PatternRule(
        id="OB-002",
        name="tr/head/tail pipeline obfuscation",
        pattern=re.compile(
            r"\btr\b.*\|.*(?:head|tail|cut|sed)\b", re.IGNORECASE
        ),
        file_globs=["*"],
        severity=RiskLevel.HIGH,
        category="obfuscation",
        description=(
            "Chained tr/head/tail pipelines were used in the XZ attack to "
            "decode hidden payloads through multiple transformation stages."
        ),
        recommendation="Audit all text-processing pipelines for hidden payload extraction.",
    ),
    PatternRule(
        id="OB-003",
        name="Base64 decoding in build/script",
        pattern=re.compile(
            r"\b(?:base64\s+(?:-d|--decode)|openssl\s+(?:enc|base64))\b",
            re.IGNORECASE,
        ),
        file_globs=["Makefile*", "*.am", "*.mk", "*.m4", "configure*", "*.sh", "*.py", "*.yml", "*.yaml"],
        severity=RiskLevel.HIGH,
        category="obfuscation",
        description=(
            "Base64 decoding in build scripts or automation can extract "
            "hidden payloads from innocuous-looking encoded data."
        ),
        recommendation="Remove base64 decoding from build scripts; use plain-text configuration.",
    ),
    PatternRule(
        id="OB-004",
        name="Compressed archive extraction in build",
        pattern=re.compile(
            r"\b(?:xz\s+-d|unxz|gzip\s+-d|gunzip|tar\s+(?:xf|xzf|xjf))\b",
            re.IGNORECASE,
        ),
        file_globs=["Makefile*", "*.am", "*.mk", "*.m4", "configure*", "*.sh"],
        severity=RiskLevel.HIGH,
        category="obfuscation",
        description=(
            "Decompressing archives during the build process can extract "
            "hidden backdoor components from test fixtures or data files."
        ),
        recommendation="Verify all archive extraction in build scripts is for legitimate resources.",
    ),
    PatternRule(
        id="OB-005",
        name="Hex-encoded strings",
        pattern=re.compile(
            r"(?:\\x[0-9a-fA-F]{2}){8,}"
        ),
        file_globs=["*"],
        severity=RiskLevel.MEDIUM,
        category="obfuscation",
        description=(
            "Long sequences of hex-encoded bytes may contain obfuscated "
            "strings, commands, or shellcode."
        ),
        recommendation="Decode and audit all hex-encoded data for hidden commands.",
    ),
    PatternRule(
        id="OB-006",
        name="Obfuscated variable names",
        pattern=re.compile(
            r"\b(?:[a-z]{1,2}[0-9]{3,}|_[A-Z]{10,}|[lI1O0]{6,})\b"
        ),
        file_globs=["*.c", "*.h", "*.cpp", "*.cc", "*.py", "*.sh"],
        severity=RiskLevel.LOW,
        category="obfuscation",
        description=(
            "Excessively short or deliberately confusing variable names "
            "can obscure malicious logic."
        ),
        recommendation="Rename obfuscated variables to descriptive names; review surrounding logic.",
    ),
]

# ---------------------------------------------------------------------------
# Social Engineering rules (SE-001 .. SE-003)
# ---------------------------------------------------------------------------
SOCIAL_ENGINEERING_RULES: list[PatternRule] = [
    PatternRule(
        id="SE-001",
        name="Pressure to merge/release",
        pattern=re.compile(
            r"(?:please\s+(?:merge|release|push)|urgent(?:ly)?|"
            r"need(?:ed)?\s+(?:this|asap)|block(?:ing|ed)\s+(?:release|merge))",
            re.IGNORECASE,
        ),
        file_globs=["*.json", "*.md", "*.txt"],
        severity=RiskLevel.MEDIUM,
        category="social_engineering",
        description=(
            "Commit messages or PR descriptions applying social pressure "
            "to merge or release quickly can indicate social engineering."
        ),
        recommendation="Review contributor history; do not rush reviews due to external pressure.",
    ),
    PatternRule(
        id="SE-002",
        name="New contributor touching build system",
        pattern=re.compile(
            r"(?:configure|Makefile|CMakeLists|\.m4|build\.gradle|\.github/workflows)",
            re.IGNORECASE,
        ),
        file_globs=["*.json", "*.md", "*.txt"],
        severity=RiskLevel.MEDIUM,
        category="social_engineering",
        description=(
            "Commits from relatively new contributors modifying build "
            "system files warrants extra scrutiny."
        ),
        recommendation="Require senior maintainer review for all build system changes.",
    ),
    PatternRule(
        id="SE-003",
        name="Suspicious commit velocity spike",
        pattern=re.compile(
            r"(?:rapid\s+commits|burst\s+of\s+changes|multiple\s+commits?\s+in)",
            re.IGNORECASE,
        ),
        file_globs=["*.json", "*.md", "*.txt"],
        severity=RiskLevel.LOW,
        category="social_engineering",
        description=(
            "A sudden spike in commit frequency from a contributor can "
            "indicate automated or scripted changes designed to overwhelm review."
        ),
        recommendation="Review high-velocity commit bursts individually; check for build changes.",
    ),
]

# ---------------------------------------------------------------------------
# Consolidated list
# ---------------------------------------------------------------------------
ALL_RULES: list[PatternRule] = (
    SUPPLY_CHAIN_RULES
    + BACKDOOR_RULES
    + OBFUSCATION_RULES
    + SOCIAL_ENGINEERING_RULES
)

RULES_BY_ID: dict[str, PatternRule] = {r.id: r for r in ALL_RULES}
RULES_BY_CATEGORY: dict[str, list[PatternRule]] = {}
for _rule in ALL_RULES:
    RULES_BY_CATEGORY.setdefault(_rule.category, []).append(_rule)
