"""Stage 4: IFUNC Hijack - Replacing CRC64 resolver to hook RSA_public_decrypt."""

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

_IFUNC_NORMAL_CODE = """\
// Normal IFUNC resolver for CRC64 - selects hardware-accelerated
// implementation at load time based on CPU features.

#include <immintrin.h>

static crc64_func_type
crc64_resolve(void)
{
    // Check for PCLMUL (Carry-Less Multiplication) support
    if (__builtin_cpu_supports("pclmul") &&
        __builtin_cpu_supports("sse4.1")) {
        return &crc64_clmul;  // Use hardware-accelerated version
    }
    return &crc64_generic;    // Fall back to software implementation
}

// IFUNC attribute tells the dynamic linker to call crc64_resolve()
// at load time to select the actual implementation.
extern uint64_t crc64(const uint8_t *, size_t, uint64_t)
    __attribute__((ifunc("crc64_resolve")));
"""

_IFUNC_BACKDOOR_CODE = """\
// BACKDOOR IFUNC resolver - injected via the compiled .o object file.
// This REPLACES the legitimate crc64_resolve at link time.

static void *
crc64_resolve(void)
{
    // Step 1: Perform legitimate CRC64 resolver work (camouflage)
    void *crc_impl = _resolve_crc64_hw();

    // Step 2: BACKDOOR - Walk the Global Offset Table (GOT) to find
    // OpenSSL's RSA_public_decrypt function pointer
    Elf64_Sym *sym = _find_symbol("RSA_public_decrypt");

    if (sym != NULL) {
        // Step 3: Overwrite the GOT entry for RSA_public_decrypt
        // with our backdoor function
        void **got_entry = _get_got_slot(sym);
        *got_entry = (void *)_backdoor_rsa_decrypt;
    }

    // Return the legitimate CRC64 implementation so
    // crc64() still works correctly (no functional change visible)
    return crc_impl;
}

// _backdoor_rsa_decrypt() intercepts RSA public key operations
// during SSH authentication to check for attacker's trigger.
"""

_GOT_PLT_EXPLANATION = """\
### How IFUNC and GOT/PLT Work

**IFUNC** (Indirect Function) is a GNU extension that allows a function's
implementation to be selected **at load time** by the dynamic linker (`ld.so`).

```
Program calls crc64()
    -> PLT stub (Procedure Linkage Table)
    -> GOT entry (Global Offset Table)
    -> First call: invokes crc64_resolve() to pick implementation
    -> Subsequent calls: jumps directly to chosen implementation
```

The backdoor exploited this by **replacing** `crc64_resolve()` with a version
that, in addition to resolving CRC64, also **patched the GOT entry** for
`RSA_public_decrypt` to point to the attacker's function.

This is particularly insidious because:
1. IFUNC resolvers run **very early** during program startup
2. They execute **before** most security monitoring is active
3. The GOT modification persists for the lifetime of the process
"""


class IFUNCHijackStage(Stage):
    """Stage 4: ELF IFUNC resolver abuse to hijack RSA_public_decrypt."""

    id = "ifunc_hijack"
    name = "IFUNC Resolver Hijack"
    order = 4

    # ------------------------------------------------------------------
    # explain
    # ------------------------------------------------------------------
    def explain(self, console: Console) -> None:
        console.print()
        console.print(
            Rule(
                "[bold red]Stage 4: IFUNC Resolver Hijack[/]",
                style="red",
            )
        )
        console.print()

        console.print(
            Panel(
                Markdown(_GOT_PLT_EXPLANATION),
                title="IFUNC / GOT / PLT Mechanism",
                border_style="blue",
            )
        )
        console.print()

        # Attack flow
        tree = Tree("[bold]IFUNC Hijack Attack Flow[/]")

        load = tree.add("[green]1. sshd starts and loads liblzma.so[/]")
        load.add("[dim]Dynamic linker processes IFUNC symbols[/]")

        resolve = tree.add("[yellow]2. crc64_resolve() is called by ld.so[/]")
        resolve.add("[dim]Backdoor resolver replaces legitimate one via linker priority[/]")

        legit = tree.add("[green]3. Legitimate CRC64 resolution proceeds[/]")
        legit.add("[dim]Correct hardware-accelerated implementation selected (camouflage)[/]")

        hijack = tree.add("[bold red]4. GOT entry for RSA_public_decrypt overwritten[/]")
        hijack.add("[red]Attacker's function pointer replaces OpenSSL's[/]")
        hijack.add("[red]All future calls to RSA_public_decrypt go to backdoor[/]")

        persist = tree.add("[red]5. sshd runs normally with backdoor active[/]")
        persist.add("[dim]No visible errors, no log entries, CRC64 works correctly[/]")

        console.print(Panel(tree, title="Attack Sequence", border_style="red"))
        console.print()

        # Why IFUNC was the perfect vehicle
        why_table = Table(
            title="Why IFUNC Was the Perfect Attack Vector",
            show_header=True,
            header_style="bold white on dark_red",
            expand=True,
        )
        why_table.add_column("Property", style="bold", width=30)
        why_table.add_column("Advantage for Attacker")
        why_table.add_row(
            "Runs at load time",
            "Executes before main(), before security tools initialize",
        )
        why_table.add_row(
            "Resolver has full code execution",
            "Can perform arbitrary operations including GOT patching",
        )
        why_table.add_row(
            "Legitimate use in xz/liblzma",
            "CRC hardware detection is a valid reason for IFUNC usage",
        )
        why_table.add_row(
            "No runtime overhead after setup",
            "Single execution at startup, then the hook persists silently",
        )
        why_table.add_row(
            "Difficult to audit",
            "IFUNC resolvers are rarely reviewed; considered low-level plumbing",
        )
        console.print(why_table)
        console.print()

        console.print(
            Panel(
                Text.assemble(
                    ("Critical insight: ", "bold green"),
                    ("The backdoor did not modify any OpenSSL source code or binary. ", ""),
                    ("It modified liblzma, which is loaded into sshd's address space ", ""),
                    ("because systemd links against liblzma for journal compression. ", ""),
                    ("The attack crossed ", ""),
                    ("library boundaries", "bold"),
                    (" via the shared process address space.", ""),
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
            Rule("[bold red]IFUNC Code Comparison[/]", style="red")
        )
        console.print()

        console.print(
            Panel(
                Syntax(
                    _IFUNC_NORMAL_CODE,
                    "c",
                    theme="monokai",
                    line_numbers=True,
                ),
                title="[green]Normal crc64_resolve() - Legitimate IFUNC[/]",
                border_style="green",
            )
        )
        console.print()

        console.print(
            Panel(
                Syntax(
                    _IFUNC_BACKDOOR_CODE,
                    "c",
                    theme="monokai",
                    line_numbers=True,
                ),
                title="[red]Backdoored crc64_resolve() - GOT Hijack[/]",
                subtitle="[dim]Reconstructed and simplified for education[/]",
                border_style="red",
            )
        )
        console.print()

        # Address space diagram
        addr_table = Table(
            title="sshd Process Address Space",
            show_header=True,
            header_style="bold white on dark_blue",
            expand=True,
        )
        addr_table.add_column("Component", style="bold", width=28)
        addr_table.add_column("Role", width=30)
        addr_table.add_column("Status")
        addr_table.add_row(
            "sshd (main binary)",
            "SSH server daemon",
            "[green]Unmodified[/]",
        )
        addr_table.add_row(
            "libcrypto.so (OpenSSL)",
            "RSA_public_decrypt and crypto",
            "[green]Unmodified[/]",
        )
        addr_table.add_row(
            "libsystemd.so",
            "Systemd integration",
            "[green]Unmodified[/]",
        )
        addr_table.add_row(
            "liblzma.so (xz)",
            "LZMA compression for journals",
            "[bold red]BACKDOORED[/]",
        )
        addr_table.add_row(
            "GOT (Global Offset Table)",
            "Function pointer dispatch",
            "[bold red]RSA_public_decrypt PATCHED[/]",
        )
        console.print(addr_table)

    # ------------------------------------------------------------------
    # indicators / model
    # ------------------------------------------------------------------
    def get_indicators(self) -> list[str]:
        return [
            "IFUNC resolvers performing operations beyond simple CPU feature detection",
            "IFUNC resolvers referencing symbols from unrelated libraries (e.g., OpenSSL)",
            "GOT/PLT manipulation code outside of the dynamic linker",
            "Object files overriding existing symbols at link time without source changes",
            "liblzma loaded into processes that don't directly use compression (e.g., sshd via systemd)",
            "Function pointers in GOT not matching expected library addresses",
        ]

    def get_attack_stage(self) -> AttackStage:
        return AttackStage(
            id=self.id,
            name=self.name,
            order=self.order,
            description=(
                "The backdoor abused ELF IFUNC resolvers to replace crc64_resolve() "
                "with a version that also patched the GOT entry for RSA_public_decrypt, "
                "redirecting OpenSSL crypto calls to the attacker's code."
            ),
            technical_detail=(
                "The injected crc64_resolve() IFUNC resolver executed during dynamic "
                "linking (before main). It performed legitimate CRC64 hardware detection "
                "as camouflage, then walked the GOT to find and replace the function "
                "pointer for RSA_public_decrypt with a backdoor function. This worked "
                "because liblzma was loaded into sshd's address space via libsystemd."
            ),
            indicators=self.get_indicators(),
            mitigations=[
                "Audit IFUNC resolvers for operations beyond CPU feature detection",
                "Monitor GOT entries at runtime for unexpected modifications",
                "Reduce unnecessary library dependencies in security-critical processes",
                "Use RELRO (Relocation Read-Only) to protect GOT entries",
            ],
        )
