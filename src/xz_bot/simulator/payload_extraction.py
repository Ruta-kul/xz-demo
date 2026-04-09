"""Stage 3: Payload Extraction - Multi-layer deobfuscation of the hidden payload."""

from __future__ import annotations

from rich.columns import Columns
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

_EXTRACTION_SCRIPT = """\
#!/bin/bash
# --- Reconstructed extraction pipeline (simplified) ---
# This is what build-to-host.m4 effectively executes:

# Step 1: Read the disguised payload from a "test fixture"
cat tests/files/bad-3-corrupt_lzma2.xz \\
                                                                  \\
  | tr "\\t \\-_" " \\t_\\-"                                      \\
                                                                  \\
  | head -c 7966                                                  \\
                                                                  \\
  | xz -d --single-stream                                        \\
                                                                  \\
  | /bin/bash
# The resulting shell script:
#   - Extracts a second payload from good-large_compressed.lzma
#   - Decompresses it through another xz -d layer
#   - Compiles the resulting C source into liblzma_la-crc64-fast.o
#   - Patches the Makefile to link this object into liblzma.so
"""

_LAYER_DESCRIPTIONS = [
    (
        "Layer 0: Disguised Container",
        "tests/files/bad-3-corrupt_lzma2.xz",
        "A file named to look like a corrupt test fixture. Actually contains "
        "obfuscated data with characters rearranged via a simple substitution cipher.",
    ),
    (
        "Layer 1: Character Substitution",
        "tr '\\t -_' ' \\t_-'",
        "A tr command swaps tabs, spaces, hyphens, and underscores to partially "
        "decode the stream. This is a trivial cipher but effective at defeating "
        "casual inspection and grep-based scanning.",
    ),
    (
        "Layer 2: Byte Extraction",
        "head -c 7966",
        "Extracts exactly 7,966 bytes from the decoded stream. The precise "
        "byte count acts as an implicit integrity check.",
    ),
    (
        "Layer 3: LZMA Decompression",
        "xz -d --single-stream",
        "Decompresses the extracted bytes using the xz utility itself. "
        "Ironic: the backdoor uses xz to decompress its own payload.",
    ),
    (
        "Layer 4: Shell Execution",
        "/bin/bash",
        "Executes the decompressed data as a bash script. This script "
        "performs the second-stage extraction.",
    ),
    (
        "Layer 5: Second Payload",
        "good-large_compressed.lzma",
        "The bash script extracts another payload from a second test fixture "
        "file, applies AWK transformations, and decompresses again.",
    ),
    (
        "Layer 6: Compilation",
        "gcc -shared -o ...",
        "The final decompressed output is C source code compiled into an "
        "x86_64 ELF shared object file (the actual backdoor).",
    ),
]


class PayloadExtractionStage(Stage):
    """Stage 3: Multi-layer deobfuscation pipeline to extract the backdoor."""

    id = "payload_extraction"
    name = "Payload Extraction & Deobfuscation"
    order = 3

    # ------------------------------------------------------------------
    # explain
    # ------------------------------------------------------------------
    def explain(self, console: Console) -> None:
        console.print()
        console.print(
            Rule(
                "[bold red]Stage 3: Payload Extraction & Deobfuscation[/]",
                style="red",
            )
        )
        console.print()

        overview = Markdown(
            "The backdoor payload was hidden in plain sight inside **test fixture files** "
            "(`tests/files/`). These files were named to appear as intentionally corrupt "
            "test data, but actually contained the backdoor code wrapped in **multiple "
            "layers of obfuscation**.\n\n"
            "The extraction used a **Russian-nesting-doll approach**: each layer revealed "
            "the next, making static analysis extremely difficult."
        )
        console.print(Panel(overview, title="Overview", border_style="red"))
        console.print()

        # Layer-by-layer breakdown
        console.print("[bold]Deobfuscation Layers[/]")
        console.print()

        tree = Tree("[bold red]bad-3-corrupt_lzma2.xz[/]")
        node = tree
        for i, (title, cmd, desc) in enumerate(_LAYER_DESCRIPTIONS):
            style = "cyan" if i < 3 else "yellow" if i < 5 else "red"
            child = node.add(f"[{style}]{title}[/]")
            child.add(f"[dim]{cmd}[/]")
            child.add(f"{desc}")
            if i < len(_LAYER_DESCRIPTIONS) - 1:
                node = child

        console.print(Panel(tree, title="Extraction Pipeline", border_style="blue"))
        console.print()

        # Why this was hard to detect
        stealth = Table(
            title="Why Detection Was Difficult",
            show_header=True,
            header_style="bold white on dark_red",
            expand=True,
        )
        stealth.add_column("Factor", style="bold", width=30)
        stealth.add_column("Explanation")
        stealth.add_row(
            "Binary test fixtures are normal",
            "XZ projects legitimately need compressed test files, so these didn't look unusual",
        )
        stealth.add_row(
            "No suspicious strings",
            "The obfuscation ensured no recognizable shell commands or C code appeared in the raw file",
        )
        stealth.add_row(
            "Self-referential tooling",
            "The payload used xz itself to decompress - no external tools needed",
        )
        stealth.add_row(
            "Byte-exact extraction",
            "head -c with a precise count meant even small changes would break the payload silently",
        )
        stealth.add_row(
            "Multi-stage design",
            "Each layer needed to be decoded before the next was visible, defeating automated scanners",
        )
        console.print(stealth)
        console.print()

        # Entropy note
        console.print(
            Panel(
                Text.assemble(
                    ("Detection hint: ", "bold green"),
                    ("The test fixture files had ", ""),
                    ("unusually high Shannon entropy", "bold"),
                    (" (~7.99 bits/byte) compared to legitimately corrupt ", ""),
                    ("LZMA data. Entropy analysis could have flagged these files ", ""),
                    ("as suspiciously well-compressed for 'corrupt' test data.", ""),
                ),
                border_style="green",
            )
        )

    # ------------------------------------------------------------------
    # demonstrate
    # ------------------------------------------------------------------
    def demonstrate(self, console: Console) -> None:
        console.print()
        console.print(
            Rule("[bold red]Extraction Pipeline Script[/]", style="red")
        )
        console.print()

        console.print(
            Panel(
                Syntax(
                    _EXTRACTION_SCRIPT,
                    "bash",
                    theme="monokai",
                    line_numbers=True,
                ),
                title="Reconstructed Extraction Pipeline",
                subtitle="[dim]Simplified for educational purposes[/]",
                border_style="red",
            )
        )
        console.print()

        # Layer summary cards
        cards = []
        for i, (title, cmd, _desc) in enumerate(_LAYER_DESCRIPTIONS):
            style = "cyan" if i < 3 else "yellow" if i < 5 else "red"
            cards.append(
                Panel(
                    f"[dim]{cmd}[/]",
                    title=f"[{style}]L{i}[/]",
                    border_style=style,
                    width=38,
                )
            )

        console.print(Columns(cards, equal=False, expand=True))
        console.print()

        # File entropy comparison
        entropy_table = Table(
            title="File Entropy Analysis (Illustrative)",
            show_header=True,
            header_style="bold white on dark_blue",
            expand=True,
        )
        entropy_table.add_column("File", style="bold")
        entropy_table.add_column("Entropy (bits/byte)", justify="center")
        entropy_table.add_column("Assessment", justify="center")
        entropy_table.add_row(
            "bad-3-corrupt_lzma2.xz",
            "[red]7.993[/]",
            "[red]Suspicious - near-perfect compression[/]",
        )
        entropy_table.add_row(
            "good-1-check-crc32.xz",
            "[green]6.842[/]",
            "[green]Normal for legitimate test data[/]",
        )
        entropy_table.add_row(
            "good-large_compressed.lzma",
            "[red]7.988[/]",
            "[red]Suspicious - contains second-stage payload[/]",
        )
        entropy_table.add_row(
            "random noise (reference)",
            "[dim]8.000[/]",
            "[dim]Maximum theoretical entropy[/]",
        )
        console.print(entropy_table)

    # ------------------------------------------------------------------
    # indicators / model
    # ------------------------------------------------------------------
    def get_indicators(self) -> list[str]:
        return [
            "Test fixture files with unusually high entropy (~8.0 bits/byte)",
            "Shell pipelines using tr, head, tail, xz in build or test scripts",
            "Binary .xz or .lzma files in test directories that don't match expected formats",
            "Build scripts referencing test fixture files outside of test execution",
            "Byte-exact extraction commands (head -c with specific counts)",
            "Self-referential decompression (using xz to unpack data within xz project)",
        ]

    def get_attack_stage(self) -> AttackStage:
        return AttackStage(
            id=self.id,
            name=self.name,
            order=self.order,
            description=(
                "The backdoor payload was hidden inside test fixture files using "
                "multiple layers of obfuscation including character substitution, "
                "byte extraction, LZMA decompression, and shell script execution."
            ),
            technical_detail=(
                "bad-3-corrupt_lzma2.xz contained obfuscated data that was decoded "
                "via tr character substitution, extracted with head -c 7966, "
                "decompressed with xz -d, and executed as a shell script. This "
                "second stage extracted further payload from good-large_compressed.lzma "
                "and compiled it into the backdoor ELF object file."
            ),
            indicators=self.get_indicators(),
            mitigations=[
                "Run entropy analysis on all binary test fixtures",
                "Flag build scripts that reference test data files",
                "Monitor for shell pipelines with tr/head/tail in build macros",
                "Verify test fixtures match their stated purpose (e.g., actually corrupt)",
            ],
        )
