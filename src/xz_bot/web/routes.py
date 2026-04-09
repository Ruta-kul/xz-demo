"""Flask routes for the XZ-Bot web dashboard."""
import json
import math
from pathlib import Path

from flask import Blueprint, render_template, request, jsonify

from xz_bot.simulator.engine import SimulatorEngine
from xz_bot.simulator.timeline import get_timeline_events
from xz_bot.scanner.orchestrator import ScanOrchestrator

bp = Blueprint("main", __name__)

_engine = SimulatorEngine()
_scanner = ScanOrchestrator()


@bp.route("/")
def index():
    return render_template("dashboard.html")


@bp.route("/api/stages")
def api_stages():
    stages = []
    for s in _engine.stages:
        stage_data = s.get_attack_stage()
        stages.append({
            "id": stage_data.id,
            "name": stage_data.name,
            "order": stage_data.order,
            "description": stage_data.description,
            "technical_detail": stage_data.technical_detail,
            "indicators": stage_data.indicators,
            "mitigations": stage_data.mitigations,
        })
    return jsonify(stages)


@bp.route("/api/stages/<stage_id>")
def api_stage(stage_id):
    for s in _engine.stages:
        stage_data = s.get_attack_stage()
        if stage_data.id == stage_id:
            return jsonify({
                "id": stage_data.id,
                "name": stage_data.name,
                "order": stage_data.order,
                "description": stage_data.description,
                "technical_detail": stage_data.technical_detail,
                "indicators": stage_data.indicators,
                "mitigations": stage_data.mitigations,
            })
    return jsonify({"error": "Stage not found"}), 404


@bp.route("/api/timeline")
def api_timeline():
    events = get_timeline_events()
    return jsonify([
        {
            "date": e.date,
            "title": e.title,
            "description": e.description,
            "phase": e.phase,
            "phase_color": e.phase_color,
        }
        for e in events
    ])


@bp.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json(silent=True) or {}
    target_path = data.get("target_path", "")

    if not target_path:
        # Default to samples directory
        target_path = str(Path(__file__).resolve().parents[3] / "samples")

    if not Path(target_path).exists():
        return jsonify({"error": f"Path not found: {target_path}"}), 400

    report = _scanner.scan(target_path)
    return jsonify(_format_report(report))


def _format_report(report):
    """Convert a ScanReport to JSON-serializable dict."""
    return {
        "target_path": report.target_path,
        "timestamp": report.timestamp.isoformat(),
        "risk_score": report.risk_score,
        "summary": report.summary,
        "severity_counts": report.severity_counts,
        "total_findings": len(report.findings),
        "findings": [
            {
                "rule_id": f.rule_id,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "severity": f.severity.value,
                "category": f.category,
                "title": f.title,
                "description": f.description,
                "evidence": f.evidence[:200],
                "recommendation": f.recommendation,
            }
            for f in sorted(report.findings, key=lambda x: x.severity.score_weight, reverse=True)
        ],
        "agent_reports": {
            name: len(findings) for name, findings in report.agent_reports.items()
        },
    }


def _shannon_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of byte data."""
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    length = len(data)
    entropy = 0.0
    for count in freq:
        if count:
            p = count / length
            entropy -= p * math.log2(p)
    return entropy


@bp.route("/api/scan-compare", methods=["POST"])
def api_scan_compare():
    """Run scanner on clean and infected samples side by side."""
    samples_dir = Path(__file__).resolve().parents[3] / "samples"
    clean_dir = samples_dir / "clean_project"

    clean_report = _scanner.scan(str(clean_dir))
    infected_report = _scanner.scan(str(samples_dir))

    return jsonify({
        "clean": _format_report(clean_report),
        "infected": _format_report(infected_report),
    })


@bp.route("/api/entropy")
def api_entropy():
    """Compute Shannon entropy for all sample files."""
    samples_dir = Path(__file__).resolve().parents[3] / "samples"
    BLOCK_SIZE = 256
    skip_ext = {".pyc", ".egg", ".whl", ".so", ".o", ".png", ".jpg", ".gif", ".zip"}
    results = []

    for fpath in sorted(samples_dir.rglob("*")):
        if not fpath.is_file() or fpath.suffix in skip_ext:
            continue
        try:
            data = fpath.read_bytes()
        except OSError:
            continue
        if not data:
            continue

        overall = round(_shannon_entropy(data), 4)
        blocks = []
        for i in range(0, len(data), BLOCK_SIZE):
            block = data[i:i + BLOCK_SIZE]
            blocks.append(round(_shannon_entropy(block), 3))

        # Categorize
        rel = fpath.relative_to(samples_dir)
        parts = str(rel).lower()
        if "clean" in parts:
            category = "clean"
        elif "build" in parts or "m4" in fpath.suffix or fpath.name in ("Makefile.am", "configure.ac"):
            category = "build"
        elif "mock_commits" in fpath.name or fpath.suffix == ".json":
            category = "data"
        else:
            category = "source"

        results.append({
            "filename": fpath.name,
            "path": str(rel),
            "size": len(data),
            "overall_entropy": overall,
            "block_entropies": blocks,
            "category": category,
        })

    results.sort(key=lambda x: x["overall_entropy"], reverse=True)
    return jsonify(results)


@bp.route("/api/trust-graph")
def api_trust_graph():
    """Build trust graph data from mock commits."""
    commits_path = Path(__file__).resolve().parents[3] / "samples" / "git_history" / "mock_commits.json"
    with open(commits_path) as f:
        commits = json.load(f)

    # Build nodes
    nodes = [
        {"id": "jia_tan", "label": "Jia Tan", "type": "attacker", "commits": 0},
        {"id": "lasse_collin", "label": "Lasse Collin", "type": "maintainer", "commits": 0},
        {"id": "dennis_ens", "label": "Dennis Ens", "type": "sockpuppet"},
        {"id": "jigar_kumar", "label": "Jigar Kumar", "type": "sockpuppet"},
        {"id": "docs", "label": "Documentation", "type": "scope"},
        {"id": "tests", "label": "Tests", "type": "scope"},
        {"id": "build", "label": "Build System", "type": "scope", "critical": True},
        {"id": "core", "label": "Core Code", "type": "scope", "critical": True},
        {"id": "release", "label": "Releases", "type": "scope", "critical": True},
    ]

    edges = []
    scope_keywords = {
        "docs": ["readme", "doc", "typo", "comment"],
        "tests": ["test", "fixture", "check"],
        "build": ["build", "cmake", "makefile", "m4", "configure", "autotools", "cflags"],
        "core": ["crc", "ifunc", "lzma", "resolver", "function"],
        "release": ["release", "version", "5.6"],
    }

    for commit in commits:
        author = commit.get("author", "")
        msg = commit.get("message", "").lower()
        date = commit.get("date", "")
        phase = commit.get("phase", "trust_building")
        significance = commit.get("significance", "")

        author_id = author.lower().replace(" ", "_")

        # Count commits per author
        for node in nodes:
            if node["id"] == author_id:
                node["commits"] = node.get("commits", 0) + 1

        # Determine scope touched
        for scope, keywords in scope_keywords.items():
            if any(kw in msg or kw in significance.lower() for kw in keywords):
                edges.append({
                    "source": author_id,
                    "target": scope,
                    "phase": phase,
                    "date": date[:7],
                    "label": commit.get("message", "")[:50],
                })

        # Sockpuppet pressure edges
        if "pressure" in significance.lower() or "sockpuppet" in significance.lower():
            if "dennis" in author.lower():
                edges.append({
                    "source": "dennis_ens", "target": "lasse_collin",
                    "type": "pressure", "phase": phase, "date": date[:7],
                    "label": "Pressure to add co-maintainer",
                })
            elif "jigar" in author.lower():
                edges.append({
                    "source": "jigar_kumar", "target": "lasse_collin",
                    "type": "pressure", "phase": phase, "date": date[:7],
                    "label": "Complains about slow progress",
                })

    phases = [
        {"name": "Trust Building", "start": "2021-01", "end": "2022-05", "color": "#388bfd"},
        {"name": "Pressure", "start": "2022-06", "end": "2022-09", "color": "#d29922"},
        {"name": "Takeover", "start": "2022-10", "end": "2023-12", "color": "#f85149"},
        {"name": "Attack", "start": "2024-01", "end": "2024-03", "color": "#da3633"},
    ]

    return jsonify({"nodes": nodes, "edges": edges, "phases": phases})
