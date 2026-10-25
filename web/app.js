// WhyCode Frontend Application Client

document.addEventListener("DOMContentLoaded", () => {
  initHealthCheck();
  initTabs();
  initSampleChips();
  initInvestigate();
  initAsk();
  initSymbol();
  initChurn();
  initSearch();
});

// 1. System Health Check
async function initHealthCheck() {
  const badge = document.getElementById("healthBadge");
  const dot = document.getElementById("healthDot");
  const text = document.getElementById("healthText");

  try {
    const res = await fetch("/api/v1/health");
    if (!res.ok) throw new Error("Health check failed");
    const data = await res.json();

    dot.classList.remove("bg-amber-400", "animate-pulse");
    dot.classList.add("bg-emerald-400");
    text.textContent = `${data.model} (${data.provider})`;
  } catch (err) {
    dot.classList.remove("bg-amber-400");
    dot.classList.add("bg-rose-500");
    text.textContent = "Backend Offline";
  }
}

// 2. Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-tab");

      tabs.forEach((t) => t.classList.remove("active"));
      contents.forEach((c) => c.classList.remove("active"));

      tab.classList.add("active");
      document.getElementById(targetId).classList.add("active");

      // Auto-fetch churn when navigating to churn tab
      if (targetId === "tab-churn") {
        fetchChurnHotspots();
      }
    });
  });
}

// 3. Sample Query Chips
function initSampleChips() {
  document.querySelectorAll(".sample-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const targetId = chip.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (input) {
        input.value = chip.textContent.trim();
        input.focus();
      }
    });
  });
}

// 4. Agentic Investigation
function initInvestigate() {
  const form = document.getElementById("investigateForm");
  const btn = document.getElementById("investigateBtn");
  const spinner = document.getElementById("investigateSpinner");
  const resultContainer = document.getElementById("investigateResult");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("investigateQuery").value.trim();
    const maxSteps = parseInt(document.getElementById("investigateSteps").value, 10);
    if (!query) return;

    btn.disabled = true;
    spinner.classList.remove("hidden");
    resultContainer.classList.add("hidden");

    try {
      const res = await fetch("/api/v1/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, max_steps: maxSteps }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Investigation failed");
      }

      const data = await res.json();
      renderInvestigation(data);
      resultContainer.classList.remove("hidden");
    } catch (err) {
      alert("Investigation error: " + err.message);
    } finally {
      btn.disabled = false;
      spinner.classList.add("hidden");
    }
  });
}

function renderInvestigation(data) {
  document.getElementById("invSummary").innerHTML = marked.parse(data.summary || "No summary provided.");
  document.getElementById("investigateCitationsCount").textContent = `${data.citations.length} Citations Extracted`;

  // Root Causes
  const rcList = document.getElementById("invRootCauses");
  rcList.innerHTML = data.root_causes.length
    ? data.root_causes.map((rc) => `<li>${escapeHtml(rc)}</li>`).join("")
    : "<li class='text-slate-500'>No direct root causes extracted.</li>";

  // Affected Callers
  const affList = document.getElementById("invAffectedSymbols");
  affList.innerHTML = data.affected_symbols.length
    ? data.affected_symbols
        .map((s) => `<span class="px-2.5 py-1 rounded-md text-xs font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20">${escapeHtml(s)}</span>`)
        .join("")
    : "<span class='text-xs text-slate-500'>None detected.</span>";

  // Timeline
  const timeList = document.getElementById("invTimeline");
  timeList.innerHTML = data.timeline.length
    ? data.timeline.map((t) => `<li class="flex items-start space-x-2"><span class="text-blue-400 font-bold">▸</span><span>${escapeHtml(t)}</span></li>`).join("")
    : "<li class='text-slate-500'>No timeline events recorded.</li>";

  // Uncertainties
  const uncList = document.getElementById("invUncertainties");
  uncList.innerHTML = data.uncertainties.length
    ? data.uncertainties.map((u) => `<li>${escapeHtml(u)}</li>`).join("")
    : "<li class='text-slate-500'>None identified.</li>";

  // Full Raw Markdown
  document.getElementById("invRawMarkdown").innerHTML = marked.parse(data.raw_markdown);
}

// 5. Grounded Q&A
function initAsk() {
  const form = document.getElementById("askForm");
  const btn = document.getElementById("askBtn");
  const spinner = document.getElementById("askSpinner");
  const resultContainer = document.getElementById("askResult");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = document.getElementById("askQuestion").value.trim();
    const mode = document.getElementById("askMode").value;
    if (!question) return;

    btn.disabled = true;
    spinner.classList.remove("hidden");
    resultContainer.classList.add("hidden");

    try {
      const res = await fetch("/api/v1/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, mode, top_k: 4 }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Q&A failed");
      }

      const data = await res.json();
      renderAsk(data);
      resultContainer.classList.remove("hidden");
    } catch (err) {
      alert("Q&A error: " + err.message);
    } finally {
      btn.disabled = false;
      spinner.classList.add("hidden");
    }
  });
}

function renderAsk(data) {
  document.getElementById("askAnswer").innerHTML = marked.parse(data.answer);

  // Confidence Pill
  const pill = document.getElementById("confidencePill");
  const pct = (data.grounding_confidence * 100).toFixed(1);
  pill.textContent = `${pct}% Grounding Confidence`;

  if (data.grounding_confidence >= 0.8) {
    pill.className = "px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
  } else {
    pill.className = "px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30";
  }

  // Citations
  const citContainer = document.getElementById("askCitations");
  if (data.verified_citations.length) {
    citContainer.innerHTML = data.verified_citations
      .map((c) => {
        const badge = c.is_verified
          ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">VERIFIED</span>`
          : `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">UNVERIFIED</span>`;
        return `<div class="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
          <span class="font-mono text-slate-300">${escapeHtml(c.raw_citation)}</span>
          <div class="flex items-center space-x-3">
            <span class="text-slate-500 text-[11px]">${escapeHtml(c.reason)}</span>
            ${badge}
          </div>
        </div>`;
      })
      .join("");
  } else {
    citContainer.innerHTML = "<div class='text-xs text-slate-500'>No direct citations detected in answer.</div>";
  }

  // Sources
  const srcContainer = document.getElementById("askSources");
  srcContainer.innerHTML = data.sources
    .map(
      (s) => `<div class="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-cyan-400">
        ${escapeHtml(s.file_path)}:${s.start_line}-${s.end_line}
      </div>`
    )
    .join("");
}

// 6. AST Code Graph
function initSymbol() {
  const form = document.getElementById("symbolForm");
  const resultContainer = document.getElementById("symbolResult");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("symbolInput").value.trim();
    if (!name) return;

    try {
      const res = await fetch(`/api/v1/symbol/${encodeURIComponent(name)}`);
      if (!res.ok) throw new Error("Symbol inspection failed");
      const data = await res.json();

      renderSymbol(data);
      resultContainer.classList.remove("hidden");
    } catch (err) {
      alert("Symbol lookup error: " + err.message);
    }
  });
}

function renderSymbol(data) {
  // Definitions
  const defsEl = document.getElementById("symbolDefs");
  defsEl.innerHTML = data.definitions.length
    ? data.definitions
        .map(
          (d) => `<div class="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <div class="font-mono font-bold text-cyan-300">[${d.kind}] ${escapeHtml(d.name)}</div>
            <div class="text-slate-400 font-mono">${escapeHtml(d.file_path)}:${d.start_line}-${d.end_line}</div>
            ${d.docstring ? `<div class="text-slate-500 text-[11px] italic mt-1">${escapeHtml(d.docstring)}</div>` : ""}
          </div>`
        )
        .join("")
    : "<div class='text-slate-500'>No definitions found in AST.</div>";

  // Callers
  const callersEl = document.getElementById("symbolCallers");
  callersEl.innerHTML = data.callers.length
    ? data.callers
        .map(
          (c) => `<div class="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center font-mono">
            <span class="text-emerald-300">${escapeHtml(c.name)}</span>
            <span class="text-slate-500 text-[11px]">${escapeHtml(c.file_path)}:${c.start_line}</span>
          </div>`
        )
        .join("")
    : "<div class='text-slate-500'>No direct callers detected.</div>";

  // Callees
  const calleesEl = document.getElementById("symbolCallees");
  calleesEl.innerHTML = data.callees.length
    ? data.callees
        .map((c) => `<span class="px-2 py-1 bg-amber-500/10 text-amber-300 border border-amber-500/20 rounded font-mono text-[11px]">${escapeHtml(c)}</span>`)
        .join("")
    : "<div class='text-slate-500'>No outbound calls detected.</div>";

  // Git Churn
  const churnEl = document.getElementById("symbolChurn");
  if (data.histories.length) {
    churnEl.innerHTML = data.histories
      .map(
        (h) => `<div class="space-y-2">
          <div class="text-slate-300 font-mono">Total Git Revisions: <strong class="text-purple-400">${h.churn_count}</strong></div>
          <div class="space-y-1">
            ${h.commits
              .map(
                (c) => `<div class="p-2 rounded bg-slate-950 border border-slate-800 flex justify-between font-mono text-[11px]">
                  <span class="text-cyan-400">${c.commit_hash.slice(0, 8)}: ${escapeHtml(c.subject)}</span>
                  <span class="text-slate-500">${escapeHtml(c.author_name)} (${c.authored_at.slice(0, 10)})</span>
                </div>`
              )
              .join("")}
          </div>
        </div>`
      )
      .join("");
  } else {
    churnEl.innerHTML = "<div class='text-slate-500'>No Git modifications recorded for this symbol.</div>";
  }
}

// 7. Churn Hotspots
function initChurn() {
  document.getElementById("refreshChurnBtn").addEventListener("click", fetchChurnHotspots);
}

async function fetchChurnHotspots() {
  const tbody = document.getElementById("churnTableBody");
  tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-500">Refreshing hotspots...</td></tr>`;

  try {
    const res = await fetch("/api/v1/churn?limit=10");
    if (!res.ok) throw new Error("Failed to fetch churn data");
    const data = await res.json();

    if (!data.hotspots.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-500">No churn data available.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.hotspots
      .map(
        (h) => `<tr class="hover:bg-slate-900/80 transition-colors">
          <td class="p-4 font-bold text-slate-500">#${h.rank}</td>
          <td class="p-4 font-bold text-cyan-300">${escapeHtml(h.symbol_name)}</td>
          <td class="p-4 text-slate-400">[${h.kind}]</td>
          <td class="p-4 font-bold text-purple-400">${h.churn_count} revisions</td>
          <td class="p-4 text-slate-400">${escapeHtml(h.file_path)}:${h.start_line}</td>
          <td class="p-4 text-slate-400 truncate max-w-xs">${h.recent_commits[0] ? escapeHtml(h.recent_commits[0].subject) : "—"}</td>
        </tr>`
      )
      .join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-rose-500">Error: ${err.message}</td></tr>`;
  }
}

// 8. Code Search
function initSearch() {
  const form = document.getElementById("searchForm");
  const resultsContainer = document.getElementById("searchResults");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("searchInput").value.trim();
    const mode = document.getElementById("searchMode").value;
    if (!query) return;

    resultsContainer.innerHTML = "<div class='text-sm text-slate-500 font-mono'>Searching codebase...</div>";

    try {
      const res = await fetch("/api/v1/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, mode, top_k: 5 }),
      });

      if (!res.ok) throw new Error("Search failed");
      const data = await res.json();

      if (!data.results.length) {
        resultsContainer.innerHTML = "<div class='text-sm text-slate-500'>No matching code found.</div>";
        return;
      }

      resultsContainer.innerHTML = data.results
        .map(
          (r, idx) => `<div class="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-3 font-mono text-xs">
            <div class="flex items-center justify-between">
              <span class="text-cyan-400 font-bold">${idx + 1}. ${escapeHtml(r.file_path)}:${r.start_line}-${r.end_line}</span>
              <span class="text-slate-500">Score: ${r.score.toFixed(3)}</span>
            </div>
            <pre class="p-3 bg-slate-950 rounded-xl overflow-x-auto text-slate-300 font-mono text-[11px] border border-slate-800/80"><code>${escapeHtml(r.content)}</code></pre>
          </div>`
        )
        .join("");
    } catch (err) {
      resultsContainer.innerHTML = `<div class="text-sm text-rose-400">Search error: ${err.message}</div>`;
    }
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
