"""Flask routes for the XZ-Bot web dashboard."""
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
    return jsonify({
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
    })
