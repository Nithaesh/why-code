import React, { useState, useEffect } from 'react'
import {
  Search,
  GitBranch,
  Flame,
  ShieldCheck,
  ExternalLink,
  GitCommit,
  Layers,
  Sparkles,
  RefreshCw,
  FolderGit2,
  AlertCircle,
  HelpCircle,
  Clock,
  ArrowRight
} from 'lucide-react'
import { marked } from 'marked'

interface HealthData {
  status: string
  version: string
  repo_path: string
  provider: string
  model: string
  has_api_key: boolean
}

interface InvestigationResult {
  query: string
  summary: string
  timeline: string[]
  root_causes: string[]
  affected_symbols: string[]
  citations: string[]
  uncertainties: string[]
  raw_markdown: string
}

interface AskResult {
  question: string
  answer: string
  grounding_confidence: number
  sources: Array<{ file_path: string; start_line: number; end_line: number; chunk_id: string }>
  verified_citations: Array<{ raw_citation: string; is_verified: boolean; reason: string }>
  context_truncated: boolean
}

interface SymbolResult {
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

interface HotspotItem {
  rank: number
  symbol_name: string
  kind: string
  file_path: string
  start_line: number
  churn_count: number
  recent_commits: Array<{ commit_hash: string; author_name: string; authored_at: string; subject: string }>
}

interface SearchChunk {
  chunk_id: string
  file_path: string
  start_line: number
  end_line: number
  content: string
  score: number
}

export function App() {
  const [activeTab, setActiveTab] = useState<'investigate' | 'ask' | 'symbol' | 'churn' | 'search'>('investigate')
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(false)
  const [cloneModalOpen, setCloneModalOpen] = useState(false)
  const [cloneUrl, setCloneUrl] = useState('')
  const [cloneLoading, setCloneLoading] = useState(false)
  const [cloneMessage, setCloneMessage] = useState<string | null>(null)

  // Tab 1: Investigate
  const [invQuery, setInvQuery] = useState('')
  const [invSteps, setInvSteps] = useState(3)
  const [invData, setInvData] = useState<InvestigationResult | null>(null)

  // Tab 2: Ask
  const [askQuery, setAskQuery] = useState('')
  const [askMode, setAskMode] = useState<'hybrid' | 'lexical' | 'semantic'>('hybrid')
  const [askData, setAskData] = useState<AskResult | null>(null)

  // Tab 3: Symbol
  const [symbolQuery, setSymbolQuery] = useState('')
  const [symbolData, setSymbolData] = useState<SymbolResult | null>(null)

  // Tab 4: Churn
  const [churnData, setChurnData] = useState<HotspotItem[]>([])

  // Tab 5: Search
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState<'hybrid' | 'lexical' | 'semantic'>('hybrid')
  const [searchResults, setSearchResults] = useState<SearchChunk[]>([])

  // Load Health Status
  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/v1/health')
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      }
    } catch {
      setHealth(null)
    }
  }

  useEffect(() => {
    fetchHealth()
  }, [])

  // Auto-fetch Churn Hotspots
  const fetchChurn = async () => {
    try {
      const res = await fetch('/api/v1/churn?limit=10')
      if (res.ok) {
        const data = await res.json()
        setChurnData(data.hotspots)
      }
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    if (activeTab === 'churn') {
      fetchChurn()
    }
  }, [activeTab])

  // Handle GitHub Repo Clone / Switch
  const handleCloneRepo = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!cloneUrl.trim()) return
    setCloneLoading(true)
    setCloneMessage(null)

    try {
      const res = await fetch('/api/v1/repo/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: cloneUrl.trim() }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Clone failed')
      setCloneMessage(`Loaded ${data.repo_name}!`)
      await fetchHealth()
      setTimeout(() => {
        setCloneModalOpen(false)
        setCloneMessage(null)
        setCloneUrl('')
      }, 1500)
    } catch (err: any) {
      setCloneMessage(`Error: ${err.message}`)
    } finally {
      setCloneLoading(false)
    }
  }

  // Handle Investigation
  const handleInvestigate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!invQuery.trim()) return
    setLoading(true)
    setInvData(null)

    try {
      const res = await fetch('/api/v1/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: invQuery, max_steps: invSteps }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Investigation failed')
      }
      const data = await res.json()
      setInvData(data)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Handle Ask Q&A
  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!askQuery.trim()) return
    setLoading(true)
    setAskData(null)

    try {
      const res = await fetch('/api/v1/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: askQuery, mode: askMode, top_k: 4 }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Q&A failed')
      }
      const data = await res.json()
      setAskData(data)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Handle Symbol Lookup
  const handleSymbol = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbolQuery.trim()) return
    setLoading(true)
    setSymbolData(null)

    try {
      const res = await fetch(`/api/v1/symbol/${encodeURIComponent(symbolQuery.trim())}`)
      if (!res.ok) throw new Error('Symbol lookup failed')
      const data = await res.json()
      setSymbolData(data)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Handle Code Search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setLoading(true)
    setSearchResults([])

    try {
      const res = await fetch('/api/v1/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, mode: searchMode, top_k: 5 }),
      })
      if (!res.ok) throw new Error('Search failed')
      const data = await res.json()
      setSearchResults(data.results)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const repoName = health?.repo_path ? health.repo_path.split(/[\\/]/).pop() : 'Loading...'

  return (
    <div className="min-h-screen bg-[#080C14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Header */}
      <header className="border-b border-white/[0.08] bg-[#0E1422]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-400 to-blue-600 flex items-center justify-center font-mono font-black text-black shadow-lg shadow-cyan-500/25 text-lg">
              W
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold tracking-tight text-white text-base">WhyCode</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-cyan-400/30 bg-cyan-400/10 text-cyan-300">
                  v0.1.0
                </span>
              </div>
              <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
                <span>Repository:</span>
                <button
                  onClick={() => setCloneModalOpen(true)}
                  className="font-mono text-cyan-300 hover:text-white underline decoration-cyan-400/40 transition-colors flex items-center space-x-1"
                >
                  <FolderGit2 className="w-3 h-3 text-cyan-400" />
                  <span>{repoName}</span>
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            {/* Clone GitHub Repo Button */}
            <button
              onClick={() => setCloneModalOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-white/10 hover:border-cyan-400/40 bg-white/[0.03] hover:bg-cyan-500/10 text-slate-300 hover:text-cyan-300 transition-all flex items-center space-x-1.5"
            >
              <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
              <span>Load GitHub Repo</span>
            </button>

            {/* Health Pill */}
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-white/[0.08] bg-black/30">
              <span className={`w-2 h-2 rounded-full ${health ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
              <span className="text-slate-300">{health ? `${health.model}` : 'Connecting...'}</span>
            </div>

            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="text-slate-400 hover:text-cyan-300 transition-colors flex items-center space-x-1"
            >
              <span>API</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="border-b border-white/[0.06] bg-[#0A0F1A]/60 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex space-x-1 py-2 overflow-x-auto">
          {[
            { id: 'investigate', label: 'Agent Investigation', icon: Sparkles },
            { id: 'ask', label: 'Grounded Q&A', icon: HelpCircle },
            { id: 'symbol', label: 'AST Code Graph', icon: Layers },
            { id: 'churn', label: 'Churn Hotspots', icon: Flame },
            { id: 'search', label: 'Code Search', icon: Search },
          ].map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-xl text-xs font-medium transition-all flex items-center space-x-2 cursor-pointer ${
                  isActive
                    ? 'bg-cyan-400/10 text-cyan-300 border border-cyan-400/30 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Main App Body */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex-1 w-full space-y-8">
        {/* ================= TAB 1: AGENT INVESTIGATION ================= */}
        {activeTab === 'investigate' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
              <div className="relative z-10">
                <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs uppercase tracking-wider mb-1">
                  <Sparkles className="w-4 h-4" />
                  <span>Stateful Software Archaeology</span>
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-white mb-2">
                  Multi-Hop Code Investigation Agent
                </h1>
                <p className="text-slate-400 text-sm max-w-3xl leading-relaxed mb-6">
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

                  <div className="flex items-center justify-between pt-2">
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
                      className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-black font-semibold text-sm transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 cursor-pointer"
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
                <div className="glass-panel p-6 rounded-2xl border-l-4 border-l-cyan-400 space-y-3">
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
                  <div className="glass-panel p-6 rounded-2xl space-y-3">
                    <h3 className="font-mono text-xs uppercase tracking-wider text-emerald-400 font-bold flex items-center space-x-2">
                      <ShieldCheck className="w-4 h-4" />
                      <span>Root Causes & Mechanisms</span>
                    </h3>
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

                  <div className="glass-panel p-6 rounded-2xl space-y-3">
                    <h3 className="font-mono text-xs uppercase tracking-wider text-amber-400 font-bold flex items-center space-x-2">
                      <Layers className="w-4 h-4" />
                      <span>Impacted Callers & Architectural Scope</span>
                    </h3>
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
                  <div className="glass-panel p-6 rounded-2xl space-y-3">
                    <h3 className="font-mono text-xs uppercase tracking-wider text-blue-400 font-bold flex items-center space-x-2">
                      <Clock className="w-4 h-4" />
                      <span>Historical Timeline & Commits</span>
                    </h3>
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

                  <div className="glass-panel p-6 rounded-2xl space-y-3">
                    <h3 className="font-mono text-xs uppercase tracking-wider text-purple-400 font-bold flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4" />
                      <span>Uncertainties & Acknowledged Gaps</span>
                    </h3>
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
                <details className="glass-panel p-4 rounded-xl text-xs font-mono">
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

        {/* ================= TAB 2: GROUNDED CODE Q&A ================= */}
        {activeTab === 'ask' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl space-y-4">
              <h2 className="text-xl font-bold text-white">Grounded Codebase Question Answering</h2>
              <p className="text-slate-400 text-sm">
                Generates answers strictly from retrieved code chunks and audits every statement with post-generation citation verification.
              </p>

              <form onSubmit={handleAsk} className="space-y-4">
                <textarea
                  rows={2}
                  value={askQuery}
                  onChange={(e) => setAskQuery(e.target.value)}
                  placeholder="e.g. How does ContextDistiller merge overlapping chunks and enforce character budgets?"
                  className="w-full bg-[#05080F] border border-white/10 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-sans"
                />

                <div className="flex items-center justify-between pt-2">
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
                    className="px-6 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-black font-semibold text-sm transition-all disabled:opacity-50 cursor-pointer flex items-center space-x-2"
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
                <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
                  <div className="text-xs font-mono text-slate-300">Grounding Confidence Audit</div>
                  <div className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-400/10 text-emerald-300 border border-emerald-400/30">
                    {(askData.grounding_confidence * 100).toFixed(1)}% Grounded
                  </div>
                </div>

                {/* Answer Card */}
                <div className="glass-panel p-6 rounded-2xl space-y-3">
                  <h3 className="font-mono text-xs uppercase tracking-wider text-cyan-400 font-bold">Answer</h3>
                  <div
                    className="prose text-sm text-slate-200"
                    dangerouslySetInnerHTML={{ __html: marked.parse(askData.answer) }}
                  />
                </div>

                {/* Citation Verifier Audit */}
                <div className="glass-panel p-6 rounded-2xl space-y-3">
                  <h3 className="font-mono text-xs uppercase tracking-wider text-slate-400 font-bold">
                    Citation Grounding Ledger
                  </h3>
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
                <div className="glass-panel p-6 rounded-2xl space-y-3">
                  <h3 className="font-mono text-xs uppercase tracking-wider text-slate-400 font-bold">
                    Retrieved Source References
                  </h3>
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

        {/* ================= TAB 3: AST CODE GRAPH ================= */}
        {activeTab === 'symbol' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl space-y-4">
              <h2 className="text-xl font-bold text-white">AST Symbol & Caller Dependency Graph</h2>
              <p className="text-slate-400 text-sm">
                Inspect functions, methods, and classes to trace who calls them and which Git commits modified their exact line spans.
              </p>

              <form onSubmit={handleSymbol} className="flex gap-3">
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
                  <div className="glass-panel p-6 rounded-2xl space-y-3">
                    <h3 className="font-mono text-xs uppercase text-cyan-400 font-bold">Definitions</h3>
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
                  <div className="glass-panel p-6 rounded-2xl space-y-3">
                    <h3 className="font-mono text-xs uppercase text-emerald-400 font-bold">
                      Callers ({symbolData.callers.length})
                    </h3>
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
                  <div className="glass-panel p-6 rounded-2xl space-y-3">
                    <h3 className="font-mono text-xs uppercase text-amber-400 font-bold">
                      Callees ({symbolData.callees.length})
                    </h3>
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
                <div className="glass-panel p-6 rounded-2xl space-y-3">
                  <h3 className="font-mono text-xs uppercase text-purple-400 font-bold flex items-center space-x-2">
                    <GitCommit className="w-4 h-4" />
                    <span>Git Churn Revisions Touching This Symbol</span>
                  </h3>
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

        {/* ================= TAB 4: CHURN HOTSPOTS ================= */}
        {activeTab === 'churn' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <Flame className="w-5 h-5 text-amber-400" />
                  <span>Codebase Churn Hotspots</span>
                </h2>
                <p className="text-slate-400 text-sm mt-1">
                  Functions and classes with the highest modification frequency across Git history.
                </p>
              </div>
              <button
                onClick={fetchChurn}
                className="px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 font-mono text-xs transition-all flex items-center space-x-2 cursor-pointer border border-white/10"
              >
                <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
                <span>Refresh</span>
              </button>
            </div>

            <div className="glass-panel rounded-2xl overflow-hidden border border-white/[0.08]">
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
        )}

        {/* ================= TAB 5: CODE SEARCH ================= */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl space-y-4">
              <h2 className="text-xl font-bold text-white">Hybrid Code Search</h2>
              <form onSubmit={handleSearch} className="space-y-4">
                <div className="flex gap-3">
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
                <div key={idx} className="glass-panel p-5 rounded-2xl space-y-3 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-cyan-400 font-bold">
                      {idx + 1}. {r.file_path}:{r.start_line}-{r.end_line}
                    </span>
                    <span className="text-slate-500">Score: {r.score.toFixed(3)}</span>
                  </div>
                  <pre className="p-3 bg-[#05080F] rounded-xl overflow-x-auto text-slate-300 text-[11px] border border-white/[0.04]">
                    <code>{r.content}</code>
                  </pre>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* GitHub Repo Clone Modal */}
      {cloneModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-panel max-w-lg w-full p-6 rounded-2xl border border-white/10 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-lg flex items-center space-x-2">
                <FolderGit2 className="w-5 h-5 text-cyan-400" />
                <span>Load Any GitHub Repository</span>
              </h3>
              <button
                onClick={() => setCloneModalOpen(false)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              WhyCode will clone the repository shallowly, scan its Python AST definitions and Git commits, and let you
              ask questions or investigate it immediately.
            </p>

            <form onSubmit={handleCloneRepo} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">GitHub Clone URL:</label>
                <input
                  type="text"
                  required
                  value={cloneUrl}
                  onChange={(e) => setCloneUrl(e.target.value)}
                  placeholder="https://github.com/pallets/flask"
                  className="w-full bg-[#05080F] border border-white/10 rounded-xl px-4 py-2.5 text-xs font-mono text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400"
                />
              </div>

              {cloneMessage && (
                <div
                  className={`p-3 rounded-xl text-xs font-mono ${
                    cloneMessage.startsWith('Error')
                      ? 'bg-rose-500/10 text-rose-300 border border-rose-500/30'
                      : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                  }`}
                >
                  {cloneMessage}
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setCloneModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={cloneLoading || !cloneUrl.trim()}
                  className="px-5 py-2 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-black font-semibold text-xs transition-all disabled:opacity-50 flex items-center space-x-1.5 cursor-pointer"
                >
                  {cloneLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ArrowRight className="w-3.5 h-3.5" />}
                  <span>{cloneLoading ? 'Cloning & Indexing...' : 'Clone & Load'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-white/[0.06] py-6 text-center text-xs text-slate-500 font-mono">
        WhyCode — Evidence-Backed Codebase Archaeology & GenAI Diagnostics • Powered by Gemini & FastAPI
      </footer>
    </div>
  )
}

export default App
