# XZ-Bot

**Interactive CVE-2024-3094 Vulnerability Lab powered by Agentic AI**

An educational tool that dissects the XZ Utils supply chain backdoor through interactive visualizations, autonomous AI-powered vulnerability scanning, and hands-on exploration.

## Features

### Kill Chain Visualization
5-stage attack flow diagram showing the full progression from social engineering to pre-auth RCE. Click each stage for technical deep-dives.

### Agentic AI Scanner
Four autonomous agents collaborate to detect supply-chain backdoor patterns:
- **Supply Chain Agent** -- Build systems, m4 macros, CI pipelines
- **Backdoor Agent** -- IFUNC resolvers, GOT/PLT hooks, crypto function hijacking
- **Obfuscation Agent** -- Entropy analysis, encoding detection, steganography
- **Social Engineering Agent** -- Commit history anomalies, contributor patterns

### Live Attack Replay
Animated SVG visualization showing the kill chain in real time -- from crafted SSH certificate to pre-auth RCE through the IFUNC resolver hijack.

### Entropy Heatmap
Shannon entropy analysis of all sample files with block-level heatmaps. High-entropy test fixtures (>7.5 bits/byte) reveal disguised backdoor payloads.

### Contributor Trust Graph
Force-directed graph visualization of the social engineering campaign. Watch Jia Tan escalate from documentation patches to release control through sockpuppet pressure.

### Side-by-Side Comparison
Run the scanner against clean and infected projects simultaneously to see the stark difference in risk scores and findings.

### Interactive Quiz
8-question CTF-style quiz covering every aspect of CVE-2024-3094 -- from social engineering tactics to crypto primitives.

### Backdoor Dissection Lab
Layer-by-layer code walkthrough of the backdoor mechanics:
1. Build system injection (m4 macro)
2. Payload extraction pipeline
3. IFUNC resolver hijack
4. RSA_public_decrypt hook
5. Pre-auth RCE trigger

### Process Memory Map
SVG diagram of the sshd address space showing normal vs. backdoored execution flow through the GOT/PLT, liblzma, and libcrypto regions.

### Additional Features
- **Report Export** -- Download scan results as a styled HTML report
- **Dark/Light Theme** -- Toggle between dark (default) and light mode
- **Keyboard Shortcuts** -- Press 1-8 to switch tabs, ? for help
- **Attack Timeline** -- Chronological view of the 3-year campaign

## Quick Start

```bash
# Install
pip install -e .

# Web Dashboard (recommended)
python -m xz_bot web --port 8080

# Terminal UI
python -m xz_bot tui

# CLI Scanner
python -m xz_bot scan samples/
```

## Project Structure

```
xz-bot/
  src/xz_bot/
    scanner/          # Agentic AI vulnerability scanner
      agents/         # 4 autonomous scanning agents
      orchestrator.py # Agent coordination & scoring
      rules.py        # Detection rule definitions
    simulator/        # Attack stage simulator
      engine.py       # 5-stage kill chain engine
      stages/         # Individual stage implementations
      timeline.py     # Historical event data
    web/              # Flask web dashboard
      routes.py       # API endpoints
      templates/      # HTML templates
      static/         # CSS + JS
    tui/              # Textual terminal UI
    cli.py            # Click CLI
  samples/            # Educational sample files (inert)
    clean_project/    # Baseline clean project
    build_scripts/    # Backdoored build system samples
    git_history/      # Mock commit history
```

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: Vanilla JS, CSS (glassmorphism), SVG, Canvas
- **TUI**: Textual framework
- **CLI**: Click
- **Scanner**: Custom rule engine with 4 autonomous agents

## Disclaimer

This is an **educational tool only**. All samples are inert and safe. No malicious code is executed. The scanner demonstrates detection techniques against known patterns from CVE-2024-3094.

## License

MIT
