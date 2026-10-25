import React from 'react'
import {
  Sparkles,
  HelpCircle,
  Layers,
  Flame,
  Search,
  RefreshCw,
  ShieldCheck,
  Clock,
  AlertCircle,
  GitCommit,
} from 'lucide-react'
import { marked } from 'marked'

export interface InvestigationResult {
  query: string
  summary: string
  timeline: string[]
  root_causes: string[]
  affected_symbols: string[]
  citations: string[]
  uncertainties: string[]
  raw_markdown: string
}

export interface AskResult {
  question: string
  answer: string
  grounding_confidence: number
  sources: Array<{ file_path: string; start_line: number; end_line: number; chunk_id: string }>
  verified_citations: Array<{ raw_citation: string; is_verified: boolean; reason: string }>
  context_truncated: boolean
}

export interface SymbolResult {
  query: string
  definitions: Array<{
    name: string
    qualified_name: string
    kind: string
    file_path: string
    start_line: number
    end_line: number
    docstring: string | null
    parameters: string[]
  }>
  callers: Array<{ name: string; qualified_name: string; kind: string; file_path: string; start_line: number }>
  callees: string[]
  histories: Array<{
    symbol_name: string
    churn_count: number
    last_modified_at: string | null
    last_author: string | null
    commits: Array<{ commit_hash: string; author_name: string; authored_at: string; subject: string }>
  }>
}

export interface HotspotItem {
  rank: number
  symbol_name: string
  kind: string
  file_path: string
  start_line: number
  churn_count: number
  recent_commits: Array<{ commit_hash: string; author_name: string; authored_at: string; subject: string }>
}

export interface SearchChunk {
  chunk_id: string
  file_path: string
  start_line: number
  end_line: number
  content: string
  score: number
}

interface WorkbenchProps {
  activeTab: 'investigate' | 'ask' | 'symbol' | 'churn' | 'search'
  setActiveTab: (tab: 'investigate' | 'ask' | 'symbol' | 'churn' | 'search') => void
  invQuery: string
  setInvQuery: (q: string) => void
  invSteps: number
  setInvSteps: (s: number) => void
  invData: InvestigationResult | null
  handleInvestigate: (e: React.FormEvent) => void
  askQuery: string
  setAskQuery: (q: string) => void
  askMode: 'hybrid' | 'lexical' | 'semantic'
  setAskMode: (m: 'hybrid' | 'lexical' | 'semantic') => void
  askData: AskResult | null
  handleAsk: (e: React.FormEvent) => void
  symbolQuery: string
  setSymbolQuery: (q: string) => void
  symbolData: SymbolResult | null
  handleSymbol: (e: React.FormEvent) => void
  churnData: HotspotItem[]
  fetchChurn: () => void
  searchQuery: string
  setSearchQuery: (q: string) => void
  searchMode: 'hybrid' | 'lexical' | 'semantic'
  setSearchMode: (m: 'hybrid' | 'lexical' | 'semantic') => void
  searchResults: SearchChunk[]
  handleSearch: (e: React.FormEvent) => void
  loading: boolean
  repoName: string
}

export const Workbench: React.FC<WorkbenchProps> = ({
  activeTab,
  setActiveTab,
  invQuery,
  setInvQuery,
  invSteps,
  setInvSteps,
  invData,
  handleInvestigate,
  askQuery,
  setAskQuery,
  askMode,
  setAskMode,
  askData,
  handleAsk,
  symbolQuery,
  setSymbolQuery,
  symbolData,
  handleSymbol,
  churnData,
  fetchChurn,
  searchQuery,
  setSearchQuery,
  searchMode,
  setSearchMode,
  searchResults,
  handleSearch,
  loading,
  repoName,
}) => {
  return (
    <section id="workbench" className="py-20 border-b border-white/[0.06] relative">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 space-y-8">
        {/* Workbench Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-white/[0.06]">
          <div>
            <div className="inline-flex items-center space-x-2 text-cyan-400 font-mono text-xs uppercase tracking-wider mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Live Interactive Workbench</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-white">
              Investigate <span className="text-cyan-300 font-mono">{repoName}</span>
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Run autonomous agent archaeology, grounded Q&A with citation audit, AST dependency tracing, and Git churn analytics.
            </p>
          </div>

          <div className="text-xs font-mono text-slate-500 bg-white/[0.02] px-3.5 py-1.5 rounded-lg border border-white/[0.05] self-start md:self-auto">
            Target: <span className="text-slate-300">{repoName}</span>
          </div>
        </div>

        {/* Workbench Navigation Tab Bar */}
        <div className="flex space-x-1.5 p-1.5 rounded-2xl bg-[#0B0F19]/80 border border-white/[0.08] backdrop-blur-md overflow-x-auto">
          {[
            { id: 'investigate', label: 'Agent Archaeology', icon: Sparkles },
            { id: 'ask', label: 'Grounded Q&A', icon: HelpCircle },
            { id: 'symbol', label: 'AST Code Graph', icon: Layers },
            { id: 'churn', label: 'Git Churn Hotspots', icon: Flame },
            { id: 'search', label: 'Hybrid Code Search', icon: Search },
          ].map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2.5 rounded-xl text-xs font-medium transition-all flex items-center space-x-2 whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'bg-cyan-400/10 text-cyan-300 border border-cyan-400/30 shadow-lg shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03] border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* Tab 1: Agent Archaeology */}
        {activeTab === 'investigate' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 sm:p-8 rounded-2xl relative overflow-hidden border border-white/[0.08]">
              <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
              <div className="relative z-10">
                <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs uppercase tracking-wider mb-1">
                  <Sparkles className="w-4 h-4" />
                  <span>Stateful Software Archaeology</span>
                </div>
                <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-white mb-2">
                  Multi-Hop Code Investigation Agent
                </h3>
                <p className="text-slate-400 text-sm max-w-3xl leading-relaxed mb-6 font-normal">
                  Deconstructs diagnostic questions into targeted hypotheses, gathers multi-modal evidence across AST
                  callers, vector search, and Git commit diffs, reflects on sufficiency, and synthesizes an authoritative report.
                </p>

                <form onSubmit={handleInvestigate} className="space-y-4">
                  <textarea
                    rows={3}
                    value={invQuery}
                    onChange={(e) => setInvQuery(e.target.value)}
                    placeholder="e.g. Why did token validation change, what commits caused it, and what callers broke?"
                    className="w-full bg-[#05080F] border border-white/10 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-all font-sans"
                  />

                  {/* Sample Chips */}
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-mono text-slate-500">Inspiration:</span>
                    {[
                      'Why was SQLite chosen for vector indexing and how are embeddings stored?',
                      'How does CitationVerifier detect hallucinated file citations?',
                      'How does DiskCache construct cache keys to guarantee determinism?',
                    ].map((sample) => (
                      <button
                        key={sample}
                        type="button"
                        onClick={() => setInvQuery(sample)}
                        className="text-xs px-3 py-1 rounded-full bg-white/[0.03] hover:bg-cyan-500/10 border border-white/10 hover:border-cyan-400/40 text-slate-300 hover:text-cyan-300 transition-all cursor-pointer font-sans"
                      >
                        {sample}
                      </button>
                    ))}
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                    <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
                      <span>Reasoning Budget:</span>
                      <select
                        value={invSteps}
                        onChange={(e) => setInvSteps(Number(e.target.value))}
                        className="bg-[#05080F] border border-white/10 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:border-cyan-400"
                      >
                        <option value={2}>2 Steps (Rapid)</option>
                        <option value={3}>3 Steps (Standard)</option>
                        <option value={5}>5 Steps (Deep Archaeology)</option>
                      </select>
                    </div>

                    <button
                      type="submit"
                      disabled={loading || !invQuery.trim()}
                      className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-black font-semibold text-sm transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 cursor-pointer"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin text-black" />
                          <span>Investigating...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-black" />
                          <span>Run Agent Investigation</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>

            {/* Investigation Results */}
            {invData && (
              <div className="space-y-6">
                {/* Executive Summary Card */}
                <div className="glass-panel p-6 sm:p-8 rounded-2xl border-l-4 border-l-cyan-400 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-mono text-xs uppercase tracking-wider text-cyan-400 font-bold">
                      Executive Summary
                    </h3>
                    <span className="text-xs font-mono text-slate-400 bg-black/40 px-3 py-1 rounded-full border border-white/10">
                      {invData.citations.length} Grounded Citations
                    </span>
                  </div>
                  <div
                    className="prose text-sm text-slate-200 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: marked.parse(invData.summary) }}
                  />
                </div>

                {/* Bento Grid: Root Causes & Impacted Callers */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                    <h4 className="font-mono text-xs uppercase tracking-wider text-emerald-400 font-bold flex items-center space-x-2">
                      <ShieldCheck className="w-4 h-4" />
                      <span>Root Causes & Mechanisms</span>
                    </h4>
                    <ul className="space-y-2 text-xs text-slate-300">
                      {invData.root_causes.length ? (
                        invData.root_causes.map((rc, idx) => (
                          <li key={idx} className="flex items-start space-x-2">
                            <span className="text-emerald-400 font-bold">▸</span>
                            <span>{rc}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-500">No explicit root causes extracted.</li>
                      )}
                    </ul>
                  </div>

                  <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                    <h4 className="font-mono text-xs uppercase tracking-wider text-amber-400 font-bold flex items-center space-x-2">
                      <Layers className="w-4 h-4" />
                      <span>Impacted Callers & Scope</span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {invData.affected_symbols.length ? (
                        invData.affected_symbols.map((sym, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-1 rounded-md text-xs font-mono bg-amber-400/10 text-amber-300 border border-amber-400/20"
                          >
                            {sym}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-500">None detected.</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Bento Grid: Timeline & Gaps */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                    <h4 className="font-mono text-xs uppercase tracking-wider text-blue-400 font-bold flex items-center space-x-2">
                      <Clock className="w-4 h-4" />
                      <span>Historical Timeline & Commits</span>
                    </h4>
                    <ul className="space-y-2 text-xs text-slate-300">
                      {invData.timeline.length ? (
                        invData.timeline.map((item, idx) => (
                          <li key={idx} className="flex items-start space-x-2">
                            <span className="text-blue-400 font-bold">▸</span>
                            <span>{item}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-500">No timeline events recorded.</li>
                      )}
                    </ul>
                  </div>

                  <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                    <h4 className="font-mono text-xs uppercase tracking-wider text-purple-400 font-bold flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4" />
                      <span>Uncertainties & Gaps</span>
                    </h4>
                    <ul className="space-y-2 text-xs text-slate-400">
                      {invData.uncertainties.length ? (
                        invData.uncertainties.map((unc, idx) => (
                          <li key={idx} className="flex items-start space-x-2">
                            <span className="text-purple-400 font-bold">•</span>
                            <span>{unc}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-500">No unresolved gaps identified.</li>
                      )}
                    </ul>
                  </div>
                </div>

                {/* Raw Synthesis Markdown */}
                <details className="glass-panel p-4 rounded-xl text-xs font-mono border border-white/[0.06]">
                  <summary className="text-slate-400 cursor-pointer font-bold hover:text-cyan-300">
                    View Complete Raw Markdown Synthesis
                  </summary>
                  <div
                    className="mt-4 prose text-slate-300"
                    dangerouslySetInnerHTML={{ __html: marked.parse(invData.raw_markdown) }}
                  />
                </details>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Grounded Q&A */}
        {activeTab === 'ask' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 sm:p-8 rounded-2xl space-y-4 border border-white/[0.08]">
              <h3 className="text-xl font-bold text-white">Grounded Codebase Question Answering</h3>
              <p className="text-slate-400 text-sm">
                Generates answers strictly from retrieved code chunks and audits every statement with post-generation citation verification.
              </p>

              <form onSubmit={handleAsk} className="space-y-4">
                <textarea
                  rows={3}
                  value={askQuery}
                  onChange={(e) => setAskQuery(e.target.value)}
                  placeholder="e.g. How does ContextDistiller merge overlapping chunks and enforce character budgets?"
                  className="w-full bg-[#05080F] border border-white/10 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-sans"
                />

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                  <div className="flex items-center space-x-3 text-xs font-mono text-slate-400">
                    <span>Retrieval Mode:</span>
                    <select
                      value={askMode}
                      onChange={(e) => setAskMode(e.target.value as any)}
                      className="bg-[#05080F] border border-white/10 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none"
                    >
                      <option value="hybrid">Hybrid (Lexical + Dense Vector)</option>
                      <option value="lexical">Lexical (BM25)</option>
                      <option value="semantic">Semantic (Vector)</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={loading || !askQuery.trim()}
                    className="px-6 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-black font-semibold text-sm transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center space-x-2"
                  >
                    {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <HelpCircle className="w-4 h-4" />}
                    <span>Ask Codebase</span>
                  </button>
                </div>
              </form>
            </div>

            {askData && (
              <div className="space-y-6">
                {/* Confidence Meter */}
                <div className="glass-panel p-4 rounded-xl flex items-center justify-between border border-white/[0.06]">
                  <div className="text-xs font-mono text-slate-300">Grounding Confidence Audit</div>
                  <div className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-400/10 text-emerald-300 border border-emerald-400/30">
                    {(askData.grounding_confidence * 100).toFixed(1)}% Grounded
                  </div>
                </div>

                {/* Answer Card */}
                <div className="glass-panel p-6 sm:p-8 rounded-2xl space-y-3 border border-white/[0.08]">
                  <h4 className="font-mono text-xs uppercase tracking-wider text-cyan-400 font-bold">Answer</h4>
                  <div
                    className="prose text-sm text-slate-200 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: marked.parse(askData.answer) }}
                  />
                </div>

                {/* Citation Verifier Audit */}
                <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                  <h4 className="font-mono text-xs uppercase tracking-wider text-slate-400 font-bold">
                    Citation Grounding Ledger
                  </h4>
                  <div className="space-y-2">
                    {askData.verified_citations.map((c, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-[#05080F] border border-white/[0.06] flex items-center justify-between text-xs font-mono"
                      >
                        <span className="text-slate-300">{c.raw_citation}</span>
                        <div className="flex items-center space-x-3">
                          <span className="text-slate-500 text-[11px]">{c.reason}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              c.is_verified
                                ? 'bg-emerald-400/20 text-emerald-300 border border-emerald-400/30'
                                : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            }`}
                          >
                            {c.is_verified ? 'VERIFIED' : 'UNVERIFIED'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Sources */}
                <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                  <h4 className="font-mono text-xs uppercase tracking-wider text-slate-400 font-bold">
                    Retrieved Source References
                  </h4>
                  <div className="space-y-2">
                    {askData.sources.map((s, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-[#05080F] border border-white/[0.06] text-xs font-mono text-cyan-300"
                      >
                        {s.file_path}:{s.start_line}-{s.end_line}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: AST Code Graph */}
        {activeTab === 'symbol' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 sm:p-8 rounded-2xl space-y-4 border border-white/[0.08]">
              <h3 className="text-xl font-bold text-white">AST Symbol & Caller Dependency Graph</h3>
              <p className="text-slate-400 text-sm">
                Inspect functions, methods, and classes to trace who calls them and which Git commits modified their exact line spans.
              </p>

              <form onSubmit={handleSymbol} className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={symbolQuery}
                  onChange={(e) => setSymbolQuery(e.target.value)}
                  placeholder="e.g. DiskCache, CitationVerifier, CodebaseSearchService, ContextDistiller"
                  className="flex-1 bg-[#05080F] border border-white/10 rounded-xl px-4 py-2.5 text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
                <button
                  type="submit"
                  disabled={loading || !symbolQuery.trim()}
                  className="px-6 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-black font-semibold text-sm transition-all cursor-pointer"
                >
                  Inspect Symbol
                </button>
              </form>

              {/* Sample Chips */}
              <div className="flex flex-wrap items-center gap-2 pt-2">
                <span className="text-[11px] font-mono text-slate-500">Quick inspect:</span>
                {['DiskCache', 'CitationVerifier', 'CodebaseSearchService', 'ContextDistiller', 'ASTSymbolParser'].map(
                  (sym) => (
                    <button
                      key={sym}
                      type="button"
                      onClick={() => setSymbolQuery(sym)}
                      className="text-xs px-2.5 py-1 rounded-full bg-white/[0.03] hover:bg-cyan-500/10 border border-white/10 text-slate-300 font-mono cursor-pointer"
                    >
                      {sym}
                    </button>
                  )
                )}
              </div>
            </div>

            {symbolData && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Definitions */}
                  <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                    <h4 className="font-mono text-xs uppercase text-cyan-400 font-bold">Definitions</h4>
                    <div className="space-y-2">
                      {symbolData.definitions.map((d, idx) => (
                        <div key={idx} className="p-3 bg-[#05080F] rounded-xl border border-white/[0.06] space-y-1">
                          <div className="font-mono font-bold text-cyan-300 text-xs">
                            [{d.kind}] {d.name}
                          </div>
                          <div className="text-slate-400 font-mono text-[11px]">
                            {d.file_path}:{d.start_line}-{d.end_line}
                          </div>
                          {d.docstring && (
                            <div className="text-slate-500 text-[11px] italic mt-1 line-clamp-2">{d.docstring}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Callers (Dependents) */}
                  <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                    <h4 className="font-mono text-xs uppercase text-emerald-400 font-bold">
                      Callers ({symbolData.callers.length})
                    </h4>
                    <div className="space-y-2 max-h-80 overflow-y-auto">
                      {symbolData.callers.length ? (
                        symbolData.callers.map((c, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 bg-[#05080F] rounded-xl border border-white/[0.06] flex justify-between items-center font-mono text-xs"
                          >
                            <span className="text-emerald-300 font-medium">{c.name}</span>
                            <span className="text-slate-500 text-[11px] truncate max-w-[120px]">{c.file_path}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-slate-500">No direct callers detected.</div>
                      )}
                    </div>
                  </div>

                  {/* Callees */}
                  <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                    <h4 className="font-mono text-xs uppercase text-amber-400 font-bold">
                      Callees ({symbolData.callees.length})
                    </h4>
                    <div className="flex flex-wrap gap-1.5 max-h-80 overflow-y-auto">
                      {symbolData.callees.length ? (
                        symbolData.callees.map((c, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-amber-400/10 text-amber-300 border border-amber-400/20 rounded-md font-mono text-[11px]"
                          >
                            {c}
                          </span>
                        ))
                      ) : (
                        <div className="text-xs text-slate-500">No outbound calls detected.</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Git Churn Revisions */}
                <div className="glass-panel p-6 rounded-2xl space-y-3 border border-white/[0.08]">
                  <h4 className="font-mono text-xs uppercase text-purple-400 font-bold flex items-center space-x-2">
                    <GitCommit className="w-4 h-4" />
                    <span>Git Churn Revisions Touching This Symbol</span>
                  </h4>
                  <div className="space-y-2">
                    {symbolData.histories.map((h, idx) => (
                      <div key={idx} className="space-y-2">
                        <div className="text-xs font-mono text-slate-400">
                          Total Modifications: <span className="text-purple-300 font-bold">{h.churn_count}</span>
                        </div>
                        <div className="space-y-1.5">
                          {h.commits.map((c) => (
                            <div
                              key={c.commit_hash}
                              className="p-2.5 rounded-xl bg-[#05080F] border border-white/[0.06] flex items-center justify-between font-mono text-xs"
                            >
                              <div className="flex items-center space-x-2">
                                <span className="text-cyan-400 font-bold">{c.commit_hash.slice(0, 8)}</span>
                                <span className="text-slate-300">{c.subject}</span>
                              </div>
                              <span className="text-slate-500 text-[11px]">
                                {c.author_name} ({c.authored_at.slice(0, 10)})
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Churn Hotspots */}
        {activeTab === 'churn' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 border border-white/[0.08]">
              <div>
                <h3 className="text-xl font-bold text-white flex items-center space-x-2">
                  <Flame className="w-5 h-5 text-amber-400" />
                  <span>Codebase Churn Hotspots</span>
                </h3>
                <p className="text-slate-400 text-sm mt-1">
                  Functions and classes with the highest modification frequency across Git history.
                </p>
              </div>
              <button
                onClick={fetchChurn}
                className="px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 font-mono text-xs transition-all flex items-center space-x-2 cursor-pointer border border-white/10 self-start sm:self-auto"
              >
                <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
                <span>Refresh Hotspots</span>
              </button>
            </div>

            <div className="glass-panel rounded-2xl overflow-hidden border border-white/[0.08]">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#05080F] text-slate-400 border-b border-white/[0.08]">
                    <tr>
                      <th className="p-4">Rank</th>
                      <th className="p-4">Symbol Name</th>
                      <th className="p-4">Kind</th>
                      <th className="p-4">Total Revisions</th>
                      <th className="p-4">File Location</th>
                      <th className="p-4">Latest Modification</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04] text-slate-300">
                    {churnData.length ? (
                      churnData.map((h) => (
                        <tr key={h.symbol_name} className="hover:bg-white/[0.02] transition-colors">
                          <td className="p-4 font-bold text-slate-500">#{h.rank}</td>
                          <td className="p-4 font-bold text-cyan-300">{h.symbol_name}</td>
                          <td className="p-4 text-slate-400">[{h.kind}]</td>
                          <td className="p-4 font-bold text-purple-400">{h.churn_count} revisions</td>
                          <td className="p-4 text-slate-400">
                            {h.file_path}:{h.start_line}
                          </td>
                          <td className="p-4 text-slate-400 truncate max-w-xs">
                            {h.recent_commits[0]?.subject || '—'}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="p-8 text-center text-slate-500">
                          Loading churn data...
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Code Search */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 sm:p-8 rounded-2xl space-y-4 border border-white/[0.08]">
              <h3 className="text-xl font-bold text-white">Hybrid Code Search</h3>
              <p className="text-slate-400 text-sm">
                Reciprocal Rank Fusion uniting BM25 term matches and sentence-transformer cosine similarities.
              </p>
              <form onSubmit={handleSearch} className="space-y-4">
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search keywords or semantic query..."
                    className="flex-1 bg-[#05080F] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                  <button
                    type="submit"
                    disabled={loading || !searchQuery.trim()}
                    className="px-6 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-black font-semibold text-sm transition-all cursor-pointer"
                  >
                    Search
                  </button>
                </div>
                <div className="flex items-center space-x-4 text-xs font-mono text-slate-400">
                  <span>Search Mode:</span>
                  <select
                    value={searchMode}
                    onChange={(e) => setSearchMode(e.target.value as any)}
                    className="bg-[#05080F] border border-white/10 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none"
                  >
                    <option value="hybrid">Hybrid (Lexical + Dense Vector)</option>
                    <option value="lexical">Lexical (BM25)</option>
                    <option value="semantic">Semantic (Vector)</option>
                  </select>
                </div>
              </form>
            </div>

            <div className="space-y-4">
              {searchResults.map((r, idx) => (
                <div key={idx} className="glass-panel p-5 rounded-2xl space-y-3 font-mono text-xs border border-white/[0.08]">
                  <div className="flex items-center justify-between">
                    <span className="text-cyan-400 font-bold">
                      {idx + 1}. {r.file_path}:{r.start_line}-{r.end_line}
                    </span>
                    <span className="text-slate-500">Score: {r.score.toFixed(3)}</span>
                  </div>
                  <pre className="p-3.5 bg-[#05080F] rounded-xl overflow-x-auto text-slate-300 text-[11px] border border-white/[0.04]">
                    <code>{r.content}</code>
                  </pre>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
