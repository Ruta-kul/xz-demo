"""Stage 5: Unauthorized Access - SSH pre-auth RCE via crafted certificate."""

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

_KILL_CHAIN_OVERVIEW = """\
The final stage is the actual exploitation: a **pre-authentication remote code
execution** (RCE) backdoor triggered via specially crafted SSH certificates.

### The Kill Chain

1. Attacker connects to a vulnerable SSH server
2. Attacker presents an SSH certificate with a **crafted payload in the N field**
   (the RSA public key modulus)
3. sshd calls `RSA_public_decrypt()` to verify the certificate
4. The **hijacked** `RSA_public_decrypt()` (from Stage 4) intercepts the call
5. Backdoor extracts and decrypts the payload from the certificate's N field
6. If the payload passes Ed448 signature verification (attacker's private key),
   the command is executed via `system()`
7. The attacker achieves **pre-auth RCE as root**
"""

_BACKDOOR_RSA_PSEUDOCODE = """\
// Simplified pseudocode of the backdoored RSA_public_decrypt
int _backdoor_rsa_decrypt(int flen, const unsigned char *from,
                          unsigned char *to, RSA *rsa, int padding)
{
    // Extract the RSA modulus (N) from the certificate
    const BIGNUM *n = RSA_get0_n(rsa);
    unsigned char *n_bytes = BN_bn2bin(n);

    // Check for the backdoor magic bytes at a specific offset
    if (memcmp(n_bytes + MAGIC_OFFSET, BACKDOOR_MAGIC, 16) == 0) {

        // Extract the encrypted command payload
        unsigned char *payload = n_bytes + PAYLOAD_OFFSET;
        size_t payload_len = extract_length(n_bytes);

        // Verify Ed448 signature (only the attacker has the private key)
        if (ed448_verify(payload, payload_len, ATTACKER_PUBKEY)) {

            // Decrypt the command using ChaCha20
            char *command = chacha20_decrypt(payload, payload_len);

            // Execute the command as root (sshd runs as root pre-auth)
            system(command);  // <-- Pre-auth Remote Code Execution
        }
    }

    // Fall through to legitimate RSA_public_decrypt
    return real_RSA_public_decrypt(flen, from, to, rsa, padding);
}
"""


class UnauthorizedAccessStage(Stage):
    """Stage 5: Full kill chain from SSH connection to pre-auth RCE."""

    id = "unauthorized_access"
    name = "Unauthorized Access (Pre-Auth RCE)"
    order = 5

    # ------------------------------------------------------------------
    # explain
    # ------------------------------------------------------------------
    def explain(self, console: Console) -> None:
        console.print()
        console.print(
            Rule(
                "[bold red on white] Stage 5: Unauthorized Access - Pre-Auth RCE [/]",
                style="red",
            )
        )
        console.print()

        console.print(
            Panel(
                Markdown(_KILL_CHAIN_OVERVIEW),
                title="The Full Kill Chain",
                border_style="red",
            )
        )
        console.print()

        # Certificate abuse explanation
        cert_panel = Text.assemble(
            ("SSH Certificate Abuse\n\n", "bold underline"),
            ("SSH certificates contain an RSA public key with a ", ""),
            ("modulus (N)", "bold cyan"),
            (" field. This N field is a large number (typically 2048-4096 bits) ", ""),
            ("that is normally the product of two primes.\n\n", ""),
            ("The attacker ", ""),
            ("crafted a certificate", "bold"),
            (" where the N field contained:\n", ""),
            (" - Magic bytes identifying it as a backdoor trigger\n", "dim"),
            (" - An Ed448 digital signature (proving attacker identity)\n", "dim"),
            (" - A ChaCha20-encrypted command payload\n", "dim"),
            (" - Padding to make it look like a valid RSA modulus\n\n", "dim"),
            ("The certificate is ", ""),
            ("syntactically valid", "bold"),
            (" - it passes all SSH protocol checks. The payload is only ", ""),
            ("interpreted by the backdoor code.", ""),
        )
        console.print(Panel(cert_panel, title="Trigger Mechanism", border_style="yellow"))
        console.print()

        # Crypto used by the backdoor
        crypto_table = Table(
            title="Cryptographic Primitives in the Backdoor",
            show_header=True,
            header_style="bold white on dark_red",
            expand=True,
        )
        crypto_table.add_column("Algorithm", style="bold", width=20)
        crypto_table.add_column("Purpose", width=30)
        crypto_table.add_column("Detail")
        crypto_table.add_row(
            "Ed448",
            "Authentication",
            "Verifies the command came from the attacker (not random noise). "
            "Only the attacker's Ed448 private key can produce valid signatures.",
        )
        crypto_table.add_row(
            "ChaCha20",
            "Encryption",
            "Encrypts the command payload so network observers cannot see "
            "what command is being executed.",
        )
        crypto_table.add_row(
            "RSA (abused)",
            "Transport",
            "The SSH certificate's N field carries the payload. The RSA math "
            "is never actually performed on the crafted modulus.",
        )
        console.print(crypto_table)
        console.print()

        # Impact
        console.print(
            Panel(
                Text.assemble(
                    ("Impact: ", "bold red"),
                    ("Any system running a vulnerable sshd (linked against backdoored ", ""),
                    ("liblzma via systemd) could be ", ""),
                    ("fully compromised remotely", "bold red"),
                    (" without any authentication. The attacker would gain ", ""),
                    ("root-level command execution", "bold red"),
                    (" before the SSH handshake completes.\n\n", ""),
                    ("Affected versions: ", "bold"),
                    ("xz-utils 5.6.0 and 5.6.1\n", ""),
                    ("CVE: ", "bold"),
                    ("CVE-2024-3094 (CVSS 10.0 Critical)", "red"),
                ),
                title="Severity Assessment",
                border_style="bold red",
            )
        )

    # ------------------------------------------------------------------
    # demonstrate
    # ------------------------------------------------------------------
    def demonstrate(self, console: Console) -> None:
        console.print()
        console.print(
            Rule("[bold red]Attack Flow Diagram[/]", style="red")
        )
        console.print()

        # Flow diagram using Tree
        tree = Tree("[bold]SSH Connection to Pre-Auth RCE[/]")

        # Attacker side
        attacker = tree.add("[bold cyan]Attacker[/]")
        craft = attacker.add("[cyan]1. Craft SSH certificate with payload in N field[/]")
        craft.add("[dim]Ed448-sign the command, ChaCha20-encrypt, embed in RSA modulus[/]")
        connect = attacker.add("[cyan]2. Connect to target SSH server[/]")
        connect.add("[dim]ssh -i crafted_cert target_host[/]")

        # Server side
        server = tree.add("[bold yellow]Vulnerable sshd[/]")
        recv = server.add("[yellow]3. Receive certificate during key exchange[/]")
        recv.add("[dim]Standard SSH protocol handling[/]")

        verify = server.add("[yellow]4. Call RSA_public_decrypt() to verify[/]")
        verify.add("[dim]Normal OpenSSL certificate verification path[/]")

        # Backdoor activation
        backdoor = tree.add("[bold red]Backdoor (hijacked RSA_public_decrypt)[/]")
        check = backdoor.add("[red]5. Check N field for magic bytes[/]")
        check.add("[dim]If no magic bytes: fall through to real RSA_public_decrypt[/]")

        sig = backdoor.add("[red]6. Verify Ed448 signature[/]")
        sig.add("[dim]Confirms command originated from the attacker[/]")

        decrypt = backdoor.add("[red]7. Decrypt command payload (ChaCha20)[/]")
        decrypt.add("[dim]Extracts plaintext shell command[/]")

        execute = backdoor.add("[bold red]8. system(command) -> PRE-AUTH RCE AS ROOT[/]")
        execute.add("[red]Full system compromise achieved[/]")

        console.print(Panel(tree, title="Kill Chain", border_style="red"))
        console.print()

        # Pseudocode
        console.print(
            Panel(
                Syntax(
                    _BACKDOOR_RSA_PSEUDOCODE,
                    "c",
                    theme="monokai",
                    line_numbers=True,
                ),
                title="[red]Backdoored RSA_public_decrypt (Pseudocode)[/]",
                subtitle="[dim]Reconstructed and simplified for education[/]",
                border_style="red",
            )
        )
        console.print()

        # What saved us
        discovery = Table(
            title="How It Was Discovered",
            show_header=True,
            header_style="bold white on dark_green",
            expand=True,
        )
        discovery.add_column("Detail", style="bold", width=24)
        discovery.add_column("Value")
        discovery.add_row(
            "Discoverer",
            "Andres Freund (Microsoft / PostgreSQL developer)",
        )
        discovery.add_row(
            "Initial symptom",
            "~500ms delay in SSH logins on Debian Sid benchmarking system",
        )
        discovery.add_row(
            "Investigation",
            "Profiled sshd, traced CPU time to liblzma CRC functions",
        )
        discovery.add_row(
            "Report date",
            "March 28, 2024 (oss-security mailing list)",
        )
        discovery.add_row(
            "Time to CVE",
            "< 24 hours from report to CVE-2024-3094",
        )
        discovery.add_row(
            "Distro impact",
            "Fedora 40/Rawhide, Debian Sid, openSUSE Tumbleweed (testing only)",
        )
        console.print(discovery)

    # ------------------------------------------------------------------
    # indicators / model
    # ------------------------------------------------------------------
    def get_indicators(self) -> list[str]:
        return [
            "Unusual SSH certificate fields (oversized or structured N modulus values)",
            "Pre-authentication code paths invoking system() or exec()",
            "RSA_public_decrypt behavior changes (timing, return values)",
            "Unexpected CPU usage during SSH key exchange (profiling anomaly)",
            "liblzma loaded in sshd process without direct compression use",
            "Ed448 or ChaCha20 references in a compression library",
        ]

    def get_attack_stage(self) -> AttackStage:
        return AttackStage(
            id=self.id,
            name=self.name,
            order=self.order,
            description=(
                "The attacker achieves pre-authentication remote code execution by "
                "sending a crafted SSH certificate whose RSA modulus (N field) contains "
                "an Ed448-signed, ChaCha20-encrypted command payload."
            ),
            technical_detail=(
                "When sshd verifies an SSH certificate, it calls RSA_public_decrypt "
                "which has been hijacked (Stage 4). The backdoor checks the RSA modulus "
                "for magic bytes, verifies an Ed448 signature to confirm attacker "
                "identity, decrypts the ChaCha20-encrypted payload, and executes it "
                "via system(). This runs as root before authentication completes, "
                "giving the attacker full pre-auth RCE."
            ),
            indicators=self.get_indicators(),
            mitigations=[
                "Update xz-utils to a patched version immediately",
                "Audit liblzma for unexpected symbol resolution behavior",
                "Minimize shared library dependencies in security-critical daemons",
                "Deploy SSH certificate pinning and anomaly detection",
                "Use process sandboxing (seccomp, pledge) to limit system() calls",
            ],
        )
