"""Stage 2: Build System Injection - Modifying autotools to inject code at build time."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from xz_bot.common.models import AttackStage
from xz_bot.simulator.stages import Stage

# Annotated excerpt of the malicious m4 macro (simplified for education)
_M4_INJECTION_CODE = """\
# build-to-host.m4 -- MODIFIED by Jia Tan
# This macro runs during ./configure && make

AC_DEFUN([gl_BUILD_TO_HOST], [
  # ... normal autotools boilerplate ...

  # === INJECTED BLOCK START ===
  # The following line was added to the distributed tarball
  # but NOT present in the git repository (tarball-only attack).

  gl_[$1]_config='sed "r\\n" $gl_am_configmake | \\
      eval $gl_path_map | \\
      $gl_[$1]_prefix -d 2>/dev/null'

  # This pipeline:
  #   1. Reads the "config" file (actually test fixture data)
  #   2. Pipes through tr (character substitution to deobfuscate)
  #   3. Pipes through head -c (extracts a specific byte range)
  #   4. Decompresses with xz -d
  #   5. Executes the result as a shell script
  #   6. The shell script compiles a .o file and links it into liblzma
  # === INJECTED BLOCK END ===
])
"""

_BUILD_PIPELINE_OVERVIEW = """\
The injection was hidden inside `m4/build-to-host.m4`, an **autotools** macro file
that runs during the `./configure && make` build process.

**Key detail**: The malicious code existed **only in release tarballs**, not in the
git repository. This made it invisible to anyone reviewing the git history.

### The Build Pipeline (Normal vs. Compromised)

```
Normal:    ./configure -> Makefile -> gcc -> liblzma.so
Backdoor:  ./configure -> build-to-host.m4 EXTRACTS payload
                       -> payload COMPILES to liblzma_la-crc64-fast.o
                       -> gcc LINKS backdoor object into liblzma.so
```
"""


class BuildInjectionStage(Stage):
    """Stage 2: How build-to-host.m4 was modified to inject code during make."""

    id = "build_injection"
    name = "Build System Injection"
    order = 2

    # ------------------------------------------------------------------
    # explain
    # ------------------------------------------------------------------
    def explain(self, console: Console) -> None:
        console.print()
        console.print(
            Rule(
                "[bold yellow]Stage 2: Build System Injection[/]",
                style="yellow",
            )
        )
        console.print()

        console.print(
            Panel(
                Markdown(_BUILD_PIPELINE_OVERVIEW),
                title="How the Build Was Hijacked",
                border_style="yellow",
            )
        )
        console.print()

        # Autotools pipeline diagram
        tree = Tree("[bold]Autotools Build Pipeline[/]")
        configure = tree.add("[green]./configure[/]")
        configure.add("[green]Runs aclocal -> reads m4/*.m4 macros[/]")
        m4_node = configure.add("[bold yellow]m4/build-to-host.m4 (COMPROMISED)[/]")
        m4_node.add("[yellow]Extracts obfuscated script from test fixtures[/]")
        m4_node.add("[yellow]Deobfuscates via tr | head | xz -d | sh[/]")
        m4_node.add("[red]Compiles backdoor C code into .o object file[/]")

        make = tree.add("[green]make[/]")
        make.add("[green]Compiles liblzma source files normally[/]")
        link = make.add("[bold red]Links backdoor .o into liblzma.so[/]")
        link.add("[red]liblzma_la-crc64-fast.o replaces legitimate CRC64 code[/]")

        install = tree.add("[green]make install[/]")
        install.add("[red]Installs compromised liblzma.so system-wide[/]")

        console.print(Panel(tree, title="Build Flow", border_style="blue"))
        console.print()

        # Why tarballs only?
        tarball_note = Text.assemble(
            ("Why tarball-only?\n\n", "bold underline"),
            ("The malicious m4 macro was ", ""),
            ("only present in release tarballs", "bold red"),
            (", not in the git repository.\n", ""),
            ("Autotools projects typically ship pre-generated ", ""),
            ("configure scripts and m4 macros in tarballs. ", ""),
            ("Most distro packagers build from tarballs, not git.\n\n", ""),
            ("This meant:\n", "bold"),
            (" - git log / git diff showed nothing suspicious\n", ""),
            (" - Code review of the repo missed the injection\n", ""),
            (" - Only tarball-level diffing could catch it", ""),
        )
        console.print(Panel(tarball_note, title="Stealth Mechanism", border_style="red"))
        console.print()

        # Conditions for activation
        conditions = Table(
            title="Backdoor Activation Conditions",
            show_header=True,
            header_style="bold white on dark_red",
            expand=True,
        )
        conditions.add_column("Condition", style="bold")
        conditions.add_column("Purpose")
        conditions.add_row(
            "Linux only (uname -s)",
            "Avoids triggering on macOS/BSD where behavior differs",
        )
        conditions.add_row(
            "x86_64 architecture",
            "Payload is compiled x86_64 object code",
        )
        conditions.add_row(
            "Building with gcc + gnu ld",
            "Relies on GNU-specific linker features (IFUNC)",
        )
        conditions.add_row(
            "Building as part of a Debian/RPM package",
            "Targets distro builds, not developer machines",
        )
        conditions.add_row(
            "TERM not set (non-interactive)",
            "Ensures it runs in automated build environments only",
        )
        console.print(conditions)

    # ------------------------------------------------------------------
    # demonstrate
    # ------------------------------------------------------------------
    def demonstrate(self, console: Console) -> None:
        console.print()
        console.print(
            Rule("[bold yellow]Annotated Injection Code[/]", style="yellow")
        )
        console.print()

        console.print(
            Panel(
                Syntax(
                    _M4_INJECTION_CODE,
                    "bash",
                    theme="monokai",
                    line_numbers=True,
                ),
                title="m4/build-to-host.m4 (malicious excerpt)",
                subtitle="[dim]Simplified for educational purposes[/]",
                border_style="yellow",
            )
        )
        console.print()

        # Step-by-step what the pipeline does
        steps = Table(
            title="Injection Pipeline Steps",
            show_header=True,
            header_style="bold white on dark_blue",
            expand=True,
        )
        steps.add_column("#", width=3, justify="center")
        steps.add_column("Command", style="bold cyan", width=28)
        steps.add_column("Description")
        steps.add_row("1", "sed 'r\\n' $configmake", "Reads the disguised payload from test fixture files")
        steps.add_row("2", "tr '\\t -_' ' \\t_-'", "Character substitution to partially deobfuscate")
        steps.add_row("3", "head -c $BYTES", "Extracts a precise byte range from the stream")
        steps.add_row("4", "xz -d", "Decompresses the extracted LZMA-compressed data")
        steps.add_row("5", "sh", "Executes the decompressed shell script")
        steps.add_row("6", "(script) gcc -shared ...", "Compiles backdoor C code into a shared object")
        steps.add_row("7", "(script) cp .o ...", "Replaces legitimate CRC64 object file in build tree")
        console.print(steps)

    # ------------------------------------------------------------------
    # indicators / model
    # ------------------------------------------------------------------
    def get_indicators(self) -> list[str]:
        return [
            "Modified .m4 files in release tarballs not matching git repository",
            "Shell pipelines involving tr, head, tail, xz in build macros",
            "Conditional build behavior based on OS, architecture, or TERM variable",
            "References to test fixture files from within build scripts",
            "Object files appearing in build tree without corresponding source",
            "Differences between git checkout and release tarball contents",
        ]

    def get_attack_stage(self) -> AttackStage:
        return AttackStage(
            id=self.id,
            name=self.name,
            order=self.order,
            description=(
                "The autotools build macro build-to-host.m4 was modified in release "
                "tarballs to extract and compile a hidden backdoor during make."
            ),
            technical_detail=(
                "The injected m4 macro used a multi-step shell pipeline to extract "
                "obfuscated data from test fixture files, decompress it, and execute "
                "the resulting script which compiled backdoor object code and linked "
                "it into liblzma. The injection only existed in tarballs, not git."
            ),
            indicators=self.get_indicators(),
            mitigations=[
                "Diff release tarballs against git repository contents",
                "Use reproducible builds to detect tarball tampering",
                "Review m4 macros for shell execution patterns",
                "Build from git sources rather than tarballs when possible",
            ],
        )
