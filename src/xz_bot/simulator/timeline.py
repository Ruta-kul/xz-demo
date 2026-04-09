"""Timeline data for the XZ Utils backdoor attack (CVE-2024-3094)."""

from __future__ import annotations

from xz_bot.common.models import TimelineEvent


def get_timeline_events() -> list[TimelineEvent]:
    """Return a chronological list of key events in the XZ backdoor attack."""
    return [
        TimelineEvent(
            date="2021-01-26",
            title="First Jia Tan patch",
            description=(
                "Jia Tan submits a first contribution to the XZ Utils mailing list: "
                "a trivial documentation fix. This begins the trust-building campaign."
            ),
            phase="trust_building",
            stage_id="social_engineering",
        ),
        TimelineEvent(
            date="2021-03-15",
            title="Test contributions begin",
            description=(
                "Jia Tan starts contributing small test improvements, building a "
                "track record of helpful, low-risk contributions."
            ),
            phase="trust_building",
            stage_id="social_engineering",
        ),
        TimelineEvent(
            date="2022-02-17",
            title="Build system involvement",
            description=(
                "Jia Tan begins touching CMake build files with minor cleanups, "
                "gradually expanding scope from tests to build infrastructure."
            ),
            phase="trust_building",
            stage_id="social_engineering",
        ),
        TimelineEvent(
            date="2022-06-07",
            title="Sockpuppet pressure campaign",
            description=(
                "Accounts 'Dennis Ens' and 'Jigar Kumar' appear on the mailing "
                "list pressuring Lasse Collin to add a co-maintainer, citing slow "
                "progress and maintainer burnout."
            ),
            phase="trust_building",
            stage_id="social_engineering",
        ),
        TimelineEvent(
            date="2022-09-27",
            title="IFUNC resolvers introduced",
            description=(
                "Jia Tan adds IFUNC-based CRC32/CRC64 implementations. This is "
                "the mechanism that will later be abused for the GOT hijack."
            ),
            phase="trust_building",
            stage_id="ifunc_hijack",
        ),
        TimelineEvent(
            date="2022-11-30",
            title="Jia Tan gains commit access",
            description=(
                "After sustained contributions and external pressure, Jia Tan is "
                "granted direct commit access to the XZ Utils repository."
            ),
            phase="trust_building",
            stage_id="social_engineering",
        ),
        TimelineEvent(
            date="2023-01-11",
            title="Suspicious test fixtures added",
            description=(
                "Binary test fixture files including bad-3-corrupt_lzma2.xz are "
                "added to the test suite. These will later contain the backdoor payload."
            ),
            phase="injection",
            stage_id="payload_extraction",
        ),
        TimelineEvent(
            date="2023-06-27",
            title="Test fixtures updated",
            description=(
                "Test fixture files are replaced with versions containing the "
                "obfuscated backdoor code. Files are named to appear as "
                "intentionally corrupt test data."
            ),
            phase="injection",
            stage_id="payload_extraction",
        ),
        TimelineEvent(
            date="2024-02-15",
            title="build-to-host.m4 modified",
            description=(
                "The autotools build macro is modified in the release tarball to "
                "extract and compile the hidden payload during make. This is the "
                "primary injection vector."
            ),
            phase="injection",
            stage_id="build_injection",
        ),
        TimelineEvent(
            date="2024-02-23",
            title="Final payload staged",
            description=(
                "Test fixtures receive their final update with the production "
                "backdoor payload. The extraction pipeline is fully operational."
            ),
            phase="injection",
            stage_id="payload_extraction",
        ),
        TimelineEvent(
            date="2024-02-24",
            title="xz-5.6.0 released",
            description=(
                "First release containing the backdoor. The tarball is distributed "
                "to early-adopter Linux distributions."
            ),
            phase="exploitation",
            stage_id="unauthorized_access",
        ),
        TimelineEvent(
            date="2024-03-09",
            title="xz-5.6.1 released",
            description=(
                "Updated release with refined backdoor code. Picked up by Fedora "
                "Rawhide, Debian Sid, and openSUSE Tumbleweed testing repositories."
            ),
            phase="exploitation",
            stage_id="unauthorized_access",
        ),
        TimelineEvent(
            date="2024-03-28",
            title="Andres Freund discovers the backdoor",
            description=(
                "Microsoft engineer Andres Freund notices a 500ms SSH login delay "
                "on a Debian Sid benchmarking system. Investigation traces the "
                "slowdown to liblzma and reveals the backdoor."
            ),
            phase="discovery",
        ),
        TimelineEvent(
            date="2024-03-29",
            title="CVE-2024-3094 assigned",
            description=(
                "Public disclosure on the oss-security mailing list. CVE-2024-3094 "
                "is assigned with a CVSS score of 10.0 (Critical). Major distros "
                "begin emergency rollbacks within hours."
            ),
            phase="discovery",
        ),
        TimelineEvent(
            date="2024-03-29",
            title="Repository access revoked",
            description=(
                "Jia Tan's commit access is revoked. The XZ Utils repository is "
                "locked down. Investigations by multiple security teams begin. "
                "The identity behind Jia Tan remains unknown."
            ),
            phase="discovery",
        ),
    ]
