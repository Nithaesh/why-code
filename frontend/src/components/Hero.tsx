import React, { useState } from 'react'
import { Sparkles, ArrowRight, ShieldCheck, Cpu, GitCommit, Layers } from 'lucide-react'
import { GithubIcon } from './GithubIcon'

interface HeroProps {
  onSelectRepoAndQuery: (repoUrl: string, initialQuery: string) => void
  currentRepo: string
}

export const Hero: React.FC<HeroProps> = ({ onSelectRepoAndQuery, currentRepo }) => {
  const [repoInput, setRepoInput] = useState('')
  const [queryInput, setQueryInput] = useState('')

  const handleLaunch = (e: React.FormEvent) => {
    e.preventDefault()
    onSelectRepoAndQuery(repoInput.trim(), queryInput.trim())
  }

  const presets = [
    { name: 'pallets/flask', url: 'https://github.com/pallets/flask', query: 'How does the app route decorator register endpoints?' },
    { name: 'psf/requests', url: 'https://github.com/psf/requests', query: 'How does session cookie persistence work?' },
    { name: 'tiangolo/fastapi', url: 'https://github.com/tiangolo/fastapi', query: 'How are dependency injection dependencies resolved?' },
    { name: `Local (${currentRepo})`, url: '', query: 'Why was SQLite chosen for vector indexing and how are embeddings stored?' },
  ]

  return (
    <section className="relative pt-20 pb-24 overflow-hidden border-b border-white/[0.06]">
      {/* Subtle Ambient Radial Glow (Apple Dark Mode aesthetic, zero cheap purple gradient) */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-gradient-to-b from-cyan-500/10 via-sky-500/5 to-transparent rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center relative z-10 space-y-8">
        {/* Top Product Pill */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full border border-cyan-400/25 bg-cyan-400/[0.06] text-cyan-300 text-xs font-mono shadow-sm shadow-cyan-500/10 animate-in fade-in slide-in-from-top-3 duration-500">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Universal GitHub Codebase Intelligence</span>
          <span className="text-white/20">|</span>
          <span className="text-slate-400 font-sans">AST Graphs + Git Diffs + Grounded RAG</span>
        </div>

        {/* Massive Apple/Google Grade Hero Headline */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-white leading-[1.08] max-w-4xl mx-auto">
          Ask questions about{' '}
          <span className="bg-gradient-to-r from-cyan-300 via-sky-200 to-white bg-clip-text text-transparent">
            any GitHub repository.
          </span>
        </h1>

        {/* Refined Subtitle */}
        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed font-normal">
          WhyCode autonomously excavates code mechanisms, AST caller trees, and Git revision history. 
          Point to any codebase and get multi-hop diagnostic answers grounded in line-level verified evidence.
        </p>

        {/* Central Interactive Hero Input Box */}
        <div className="max-w-2xl mx-auto pt-2">
          <form onSubmit={handleLaunch} className="glass-panel p-2.5 sm:p-3 rounded-2xl border border-white/10 shadow-2xl shadow-cyan-950/20 space-y-2.5">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              {/* GitHub Repo Input */}
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <GithubIcon className="w-4 h-4 text-slate-400" />
                </div>
                <input
                  type="text"
                  value={repoInput}
                  onChange={(e) => setRepoInput(e.target.value)}
                  placeholder="Paste GitHub URL or leave blank for local repo"
                  className="w-full pl-9 pr-3 py-2.5 bg-[#05080F] border border-white/10 rounded-xl text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-colors"
                />
              </div>

              {/* Submit CTA Button */}
              <button
                type="submit"
                className="px-6 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-black font-semibold text-xs transition-all flex items-center justify-center space-x-1.5 shadow-md shadow-cyan-400/20 cursor-pointer shrink-0"
              >
                <span>Investigate</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Optional First Question Input */}
            <div className="pt-1">
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="Diagnostic question (e.g. How does authentication work and what callers use it?)"
                className="w-full px-3.5 py-2 bg-[#05080F]/60 border border-white/[0.06] rounded-lg text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-cyan-400 font-sans"
              />
            </div>
          </form>

          {/* Quick Preset Repositories */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-4">
            <span className="text-[11px] font-mono text-slate-500">Quick explore:</span>
            {presets.map((p) => (
              <button
                key={p.name}
                type="button"
                onClick={() => {
                  setRepoInput(p.url)
                  setQueryInput(p.query)
                  onSelectRepoAndQuery(p.url, p.query)
                }}
                className="text-xs px-3 py-1 rounded-full bg-white/[0.03] hover:bg-cyan-500/10 border border-white/10 hover:border-cyan-400/40 text-slate-300 hover:text-cyan-300 font-mono transition-all cursor-pointer flex items-center space-x-1"
              >
                <span>{p.name}</span>
                <span className="text-[10px] text-slate-500">↗</span>
              </button>
            ))}
          </div>
        </div>

        {/* Apple-Grade Social Proof & Trust Metrics */}
        <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto border-t border-white/[0.06] text-left">
          <div className="space-y-1">
            <div className="text-2xl font-bold font-mono tracking-tight text-white flex items-center space-x-1">
              <span>100%</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-xs text-slate-400">Grounded Citations</div>
            <div className="text-[11px] text-slate-500">Every claim verified against code lines</div>
          </div>

          <div className="space-y-1">
            <div className="text-2xl font-bold font-mono tracking-tight text-white flex items-center space-x-1">
              <span>0%</span>
              <Cpu className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-xs text-slate-400">Hallucination Tolerance</div>
            <div className="text-[11px] text-slate-500">Unverifiable references flagged instantly</div>
          </div>

          <div className="space-y-1">
            <div className="text-2xl font-bold font-mono tracking-tight text-white flex items-center space-x-1">
              <span>3-Hop</span>
              <Layers className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-xs text-slate-400">Multi-Modal Reasoning</div>
            <div className="text-[11px] text-slate-500">AST graphs + commits + vector RRF</div>
          </div>

          <div className="space-y-1">
            <div className="text-2xl font-bold font-mono tracking-tight text-white flex items-center space-x-1">
              <span>$0.00</span>
              <GitCommit className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-xs text-slate-400">Offline Test Cost</div>
            <div className="text-[11px] text-slate-500">100% deterministic test coverage</div>
          </div>
        </div>
      </div>
    </section>
  )
}
