import React, { useState } from 'react'
import {
  Sparkles,
  ArrowRight,
  Search,
  CheckCircle2,
  Clock,
  Send,
} from 'lucide-react'
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
    <section id="overview" className="relative pt-8 pb-20 overflow-hidden border-b border-white/[0.06]">
      {/* Ambient Neon Purple & Violet Radial Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[900px] h-[550px] bg-gradient-to-b from-purple-600/15 via-fuchsia-600/10 to-transparent rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute top-1/3 left-1/6 w-[450px] h-[450px] bg-indigo-600/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 relative z-10 space-y-7">
        {/* Top Header Row matching Reference Image */}
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/[0.08] flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-2xl relative overflow-hidden">
          <div className="space-y-1.5 relative z-10">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300 text-xs font-mono mb-1">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              <span>Universal GitHub Intelligence</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-white">
              Welcome to <span className="bg-gradient-to-r from-purple-300 via-fuchsia-200 to-white bg-clip-text text-transparent">WhyCode</span>
            </h1>
            <p className="text-sm text-slate-400 max-w-2xl font-normal">
              Autonomous software archaeology across any GitHub repository. Multi-hop agent reasoning grounded in compiler AST trees and verified Git blame history.
            </p>
          </div>

          {/* Quick Search & Status Pill */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 relative z-10">
            <div className="relative">
              <Search className="w-4 h-4 text-purple-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="Ask about any repo..."
                className="w-full sm:w-64 pl-10 pr-4 py-2 rounded-2xl bg-[#090C16]/90 border border-purple-500/20 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-400 font-sans"
              />
            </div>
            <button
              onClick={handleLaunch}
              className="px-4 py-2 rounded-2xl bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-purple-500/25 flex items-center justify-center space-x-1.5 cursor-pointer"
            >
              <span>Investigate</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* 4 Stat KPI Cards Row matching reference image */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* KPI 1 */}
          <div className="glass-panel p-5 rounded-3xl border border-white/[0.08] relative overflow-hidden space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Grounded Citations</span>
              {/* Mini Sparkline SVG */}
              <svg className="w-8 h-4 text-purple-400 stroke-current fill-none" viewBox="0 0 32 16">
                <path d="M0 12 Q 8 4, 16 9 T 32 2" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold font-mono text-white tracking-tight">100%</span>
              <span className="text-[11px] font-mono text-emerald-400 font-semibold">+100% verified</span>
            </div>
            <p className="text-[11px] text-slate-500">Every claim audited against code lines</p>
          </div>

          {/* KPI 2 */}
          <div className="glass-panel p-5 rounded-3xl border border-white/[0.08] relative overflow-hidden space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Reasoning Depth</span>
              <svg className="w-8 h-4 text-fuchsia-400 stroke-current fill-none" viewBox="0 0 32 16">
                <path d="M0 14 L 10 8 L 18 11 L 32 2" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold font-mono text-white tracking-tight">3-Hop</span>
              <span className="text-[11px] font-mono text-fuchsia-400 font-semibold">AST + Git + RRF</span>
            </div>
            <p className="text-[11px] text-slate-500">Recursive multi-modal evidence gathering</p>
          </div>

          {/* KPI 3: Circular Ring Progress */}
          <div className="glass-panel p-5 rounded-3xl border border-white/[0.08] relative overflow-hidden space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Grounding Accuracy</span>
              {/* Glowing circular donut */}
              <div className="relative w-5 h-5">
                <svg className="w-5 h-5 -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="rgba(255, 255, 255, 0.1)"
                    strokeWidth="3.5"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#a855f7"
                    strokeWidth="3.5"
                    strokeDasharray="98.7, 100"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold font-mono text-white tracking-tight">98.7%</span>
              <span className="text-[11px] font-mono text-purple-300 font-semibold">+2.4% vs baseline</span>
            </div>
            <p className="text-[11px] text-slate-500">Deterministic citation validation</p>
          </div>

          {/* KPI 4 */}
          <div className="glass-panel p-5 rounded-3xl border border-white/[0.08] relative overflow-hidden space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Offline Test Cost</span>
              <Clock className="w-4 h-4 text-purple-400" />
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold font-mono text-white tracking-tight">$0.00</span>
              <span className="text-[11px] font-mono text-emerald-400 font-semibold">100% Local</span>
            </div>
            <p className="text-[11px] text-slate-500">Deterministic local SQLite vector cache</p>
          </div>
        </div>

        {/* Central Visualizer Grid (System Waveform + Predictive Insights) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Large System Overview Card with Luminous Glowing Sine Wave */}
          <div className="lg:col-span-2 glass-panel p-6 sm:p-7 rounded-3xl border border-white/[0.08] relative overflow-hidden flex flex-col justify-between space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h3 className="font-bold text-white text-base">System Overview</h3>
                <p className="text-xs text-slate-400">Real-time pipeline orchestration across active repo</p>
              </div>
              <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>All Systems Operational</span>
              </div>
            </div>

            {/* Glowing Neon Sine Waveform Graph with 4 Named Nodes */}
            <div className="relative py-4 px-2">
              {/* SVG Glowing Wave */}
              <div className="relative h-28 w-full flex items-center justify-center">
                <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 600 120">
                  <defs>
                    <linearGradient id="waveGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#818cf8" />
                      <stop offset="35%" stopColor="#c084fc" />
                      <stop offset="70%" stopColor="#e879f9" />
                      <stop offset="100%" stopColor="#a855f7" />
                    </linearGradient>
                    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                      <feGaussianBlur stdDeviation="6" result="blur" />
                      <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                      </feMerge>
                    </filter>
                  </defs>

                  {/* Shaded Area Below Wave */}
                  <path
                    d="M 0 60 Q 75 10, 150 60 T 300 60 T 450 60 T 600 60 L 600 120 L 0 120 Z"
                    fill="url(#waveGradient)"
                    fillOpacity="0.08"
                  />

                  {/* Primary Glowing Wave */}
                  <path
                    d="M 0 60 Q 75 10, 150 60 T 300 60 T 450 60 T 600 60"
                    fill="none"
                    stroke="url(#waveGradient)"
                    strokeWidth="3.5"
                    filter="url(#glow)"
                  />
                  {/* Secondary Subtle Phase Wave */}
                  <path
                    d="M 0 60 Q 75 110, 150 60 T 300 60 T 450 60 T 600 60"
                    fill="none"
                    stroke="rgba(168, 85, 247, 0.25)"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                  />

                  {/* 4 Interactive Nodes */}
                  <circle cx="75" cy="18" r="6" fill="#818cf8" filter="url(#glow)" />
                  <circle cx="225" cy="18" r="6" fill="#c084fc" filter="url(#glow)" />
                  <circle cx="375" cy="18" r="6" fill="#e879f9" filter="url(#glow)" />
                  <circle cx="525" cy="18" r="6" fill="#a855f7" filter="url(#glow)" />
                </svg>

                {/* Node Labels Overlay */}
                <div className="absolute top-0 inset-x-0 flex justify-between px-6 text-[11px] font-mono text-slate-300 pointer-events-none">
                  <div className="text-center">
                    <span className="block text-indigo-300 font-bold">Data Ingestion</span>
                    <span className="text-[10px] text-slate-500">Shallow Git Clone</span>
                  </div>
                  <div className="text-center">
                    <span className="block text-purple-300 font-bold">AST Traversal</span>
                    <span className="text-[10px] text-slate-500">Classes & Callers</span>
                  </div>
                  <div className="text-center">
                    <span className="block text-fuchsia-300 font-bold">Git Blame Trace</span>
                    <span className="text-[10px] text-slate-500">Revision Velocity</span>
                  </div>
                  <div className="text-center">
                    <span className="block text-purple-300 font-bold">Citation Audit</span>
                    <span className="text-[10px] text-slate-500">Line Verification</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Progress Bars matching reference image */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-white/[0.06]">
              <div className="space-y-1.5">
                <div className="text-xs text-slate-400">Processing Power</div>
                <div className="text-sm font-bold font-mono text-white">78%</div>
                <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full w-[78%] rounded-full" />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="text-xs text-slate-400">Memory Cache</div>
                <div className="text-sm font-bold font-mono text-white">54MB</div>
                <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-gradient-to-r from-fuchsia-500 to-purple-500 h-full w-[54%] rounded-full" />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="text-xs text-slate-400">AST Symbols</div>
                <div className="text-sm font-bold font-mono text-white">1,420</div>
                <div className="text-[10px] text-purple-400 font-mono">Real-time mapped</div>
              </div>

              <div className="space-y-1.5">
                <div className="text-xs text-slate-400">Indexed Chunks</div>
                <div className="text-sm font-bold font-mono text-white">8.7K</div>
                <div className="text-[10px] text-emerald-400 font-mono">SQLite vector store</div>
              </div>
            </div>
          </div>

          {/* Predictive Insights Card */}
          <div className="glass-panel p-6 sm:p-7 rounded-3xl border border-white/[0.08] relative overflow-hidden flex flex-col justify-between space-y-4">
            <div className="space-y-1">
              <h3 className="font-bold text-white text-base">Predictive Insights</h3>
              <p className="text-xs text-slate-400">Architectural change probability</p>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-slate-400">Grounding Probability</div>
              <div className="flex items-baseline space-x-2">
                <span className="text-4xl font-bold font-mono text-white">94.2%</span>
                <span className="text-xs font-mono text-purple-400 font-semibold">+5.6% vs baseline</span>
              </div>
            </div>

            {/* Rising Line Chart with Gradient Fill */}
            <div className="h-24 w-full relative">
              <svg className="w-full h-full overflow-visible" viewBox="0 0 200 80" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="curveGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a855f7" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#a855f7" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
                <path
                  d="M 0 65 Q 40 60, 80 50 T 140 35 T 200 12 L 200 80 L 0 80 Z"
                  fill="url(#curveGradient)"
                />
                <path
                  d="M 0 65 Q 40 60, 80 50 T 140 35 T 200 12"
                  fill="none"
                  stroke="#a855f7"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
                <circle cx="200" cy="12" r="4" fill="#f43f5e" />
              </svg>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-white/[0.06] text-xs font-mono">
              <span className="text-slate-400">Confidence: <span className="text-purple-300 font-bold">High</span></span>
              <span className="text-slate-400">Horizon: <span className="text-slate-200">7 days</span></span>
            </div>
          </div>
        </div>

        {/* Central Row: Active Agents + AI Assistant with Radiant Orb + Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
          {/* Col 1: Active Agents */}
          <div className="glass-panel p-6 rounded-3xl border border-white/[0.08] space-y-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-sm">Active Agents</h3>
              <span className="text-xs text-purple-400 font-mono">View all (4)</span>
            </div>

            <div className="space-y-3">
              {[
                { name: 'Multi-Hop Archaeologist', desc: 'Synthesizing hypotheses', pct: '98%' },
                { name: 'Citation Verifier', desc: 'Auditing code line spans', pct: '100%' },
                { name: 'AST Code Graph Tracer', desc: 'Mapping caller hierarchies', pct: '99%' },
                { name: 'Git Churn Profiler', desc: 'Ranking commit frequency', pct: '95%' },
              ].map((ag) => (
                <div
                  key={ag.name}
                  className="p-3 rounded-2xl bg-[#090C16]/80 border border-white/[0.05] hover:border-purple-500/30 transition-all flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <div className="text-xs font-semibold text-white">{ag.name}</div>
                    <div className="text-[11px] text-slate-400">{ag.desc}</div>
                  </div>
                  <span className="text-xs font-mono font-bold text-purple-300 px-2 py-0.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
                    {ag.pct}
                  </span>
                </div>
              ))}
            </div>

            <div className="text-[11px] text-slate-500 font-mono text-center pt-1">
              Autonomous Archaeology Engine v0.1.0
            </div>
          </div>

          {/* Col 2: Central AI Assistant with RADIANT PULSING ORB */}
          <div className="glass-panel p-7 rounded-3xl border border-purple-500/30 relative overflow-hidden flex flex-col items-center justify-between text-center space-y-5 shadow-2xl shadow-purple-950/40">
            {/* Ambient Background Glow */}
            <div className="absolute inset-0 bg-radial-gradient from-purple-600/20 via-transparent to-transparent pointer-events-none" />

            <div className="w-full flex items-center justify-between text-xs text-slate-400 font-mono">
              <span className="text-purple-300 font-semibold flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <span>AI Assistant</span>
              </span>
              <span className="text-slate-500">Target: {currentRepo}</span>
            </div>

            {/* Glowing Radiant Orb matching Reference Image */}
            <div className="relative py-4 flex items-center justify-center">
              {/* Outer Lens Flare Rings */}
              <div className="w-32 h-32 rounded-full border border-purple-500/20 flex items-center justify-center animate-spin" style={{ animationDuration: '24s' }}>
                <div className="w-24 h-24 rounded-full border border-fuchsia-500/30 flex items-center justify-center" />
              </div>
              {/* Pulsing Core Sphere */}
              <div className="absolute w-16 h-16 rounded-full bg-gradient-to-tr from-purple-600 via-fuchsia-500 to-indigo-400 animate-orb-pulse flex items-center justify-center shadow-lg shadow-purple-500/60">
                <div className="w-6 h-6 rounded-full bg-white/90 blur-[1px]" />
              </div>
            </div>

            <div className="space-y-1">
              <h4 className="text-base font-bold text-white">How can I help you today?</h4>
              <p className="text-xs text-slate-400 max-w-xs">
                Ask questions about any GitHub repo or investigate code mechanisms.
              </p>
            </div>

            {/* Central Interactive GitHub Launcher Form */}
            <form onSubmit={handleLaunch} className="w-full space-y-2.5">
              <div className="relative">
                <GithubIcon className="w-4 h-4 text-purple-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  value={repoInput}
                  onChange={(e) => setRepoInput(e.target.value)}
                  placeholder="Paste GitHub URL (e.g. pallets/flask)"
                  className="w-full pl-10 pr-4 py-2.5 rounded-2xl bg-[#090C16] border border-purple-500/30 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-purple-400 transition-colors"
                />
              </div>

              <div className="relative flex items-center">
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="Ask anything about this repo..."
                  className="w-full pl-4 pr-11 py-2.5 rounded-2xl bg-[#090C16] border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-400 transition-colors font-sans"
                />
                <button
                  type="submit"
                  className="absolute right-1.5 w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-500 to-fuchsia-500 hover:from-purple-400 hover:to-fuchsia-400 text-white flex items-center justify-center transition-transform hover:scale-105 cursor-pointer shadow-md shadow-purple-500/30"
                  title="Run Investigation"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>

            {/* Quick Explore Chips */}
            <div className="flex flex-wrap items-center justify-center gap-1.5 pt-1">
              {presets.map((p) => (
                <button
                  key={p.name}
                  type="button"
                  onClick={() => {
                    setRepoInput(p.url)
                    setQueryInput(p.query)
                    onSelectRepoAndQuery(p.url, p.query)
                  }}
                  className="text-[11px] px-2.5 py-1 rounded-full bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 hover:border-purple-400 text-purple-200 transition-all font-mono cursor-pointer"
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          {/* Col 3: Recent Activity */}
          <div className="glass-panel p-6 rounded-3xl border border-white/[0.08] space-y-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-sm">Recent Activity</h3>
              <span className="text-xs text-purple-400 font-mono">View all</span>
            </div>

            <div className="space-y-3">
              {[
                { dot: 'bg-emerald-400', title: 'Data analysis completed', time: '2 minutes ago' },
                { dot: 'bg-fuchsia-400', title: 'Investigation report generated', time: '15 minutes ago' },
                { dot: 'bg-purple-400', title: 'AST symbol scan completed', time: '32 minutes ago' },
                { dot: 'bg-indigo-400', title: 'SQLite cache synchronized', time: '1 hour ago' },
              ].map((act, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-2xl bg-[#090C16]/80 border border-white/[0.05] hover:border-purple-500/30 transition-all flex items-center justify-between cursor-pointer group"
                >
                  <div className="flex items-center space-x-3">
                    <span className={`w-2.5 h-2.5 rounded-full ${act.dot} shrink-0`} />
                    <div>
                      <div className="text-xs font-semibold text-white group-hover:text-purple-300 transition-colors">
                        {act.title}
                      </div>
                      <div className="text-[11px] text-slate-500">{act.time}</div>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-purple-400 transition-colors" />
                </div>
              ))}
            </div>

            <div className="text-[11px] text-slate-500 font-mono text-center pt-1">
              Deterministic Verification Audit: Active
            </div>
          </div>
        </div>

        {/* Bottom Row: Performance Analytics Bar Chart + Automation Workflows Graph */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Analytics Glowing Bar Chart */}
          <div className="glass-panel p-6 sm:p-7 rounded-3xl border border-white/[0.08] space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-base">Performance Analytics</h3>
                <p className="text-xs text-slate-400">Weekly query & archaeology throughput</p>
              </div>
              <div className="px-3 py-1 rounded-xl bg-purple-500/10 border border-purple-500/25 text-purple-300 text-xs font-mono">
                7 Days
              </div>
            </div>

            {/* Glowing Vertical Bars */}
            <div className="relative pt-6 pb-2">
              <div className="h-36 flex items-end justify-between gap-3 px-4">
                {[
                  { day: 'Mon', h: '45%' },
                  { day: 'Tue', h: '65%' },
                  { day: 'Wed', h: '82%' },
                  { day: 'Thu', h: '55%' },
                  { day: 'Fri', h: '94%', peak: true },
                  { day: 'Sat', h: '38%' },
                  { day: 'Sun', h: '48%' },
                ].map((bar) => (
                  <div key={bar.day} className="flex-1 flex flex-col items-center gap-2 group relative">
                    {bar.peak && (
                      <div className="absolute -top-10 px-2.5 py-1 rounded-lg bg-purple-600 text-white font-mono text-[10px] whitespace-nowrap shadow-lg shadow-purple-600/40 font-bold animate-bounce">
                        Peak: 9.2K Tasks
                      </div>
                    )}
                    <div className="w-full bg-white/5 rounded-2xl h-36 flex items-end p-1">
                      <div
                        style={{ height: bar.h }}
                        className={`w-full rounded-xl transition-all duration-500 ${
                          bar.peak
                            ? 'bg-gradient-to-t from-purple-600 via-fuchsia-500 to-indigo-400 shadow-lg shadow-purple-500/40'
                            : 'bg-gradient-to-t from-purple-700/60 to-purple-500/40 hover:from-purple-600 hover:to-fuchsia-500'
                        }`}
                      />
                    </div>
                    <span className="text-[11px] font-mono text-slate-400">{bar.day}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Automation Workflows Connected Node Chart */}
          <div className="glass-panel p-6 sm:p-7 rounded-3xl border border-white/[0.08] space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-base">Automation Workflows</h3>
                <p className="text-xs text-slate-400">Deterministic code understanding pipeline</p>
              </div>
              <span className="text-xs text-purple-400 font-mono">View all</span>
            </div>

            {/* Connected Nodes matching Reference Image */}
            <div className="py-2 flex flex-col sm:flex-row items-center gap-4 justify-between relative">
              {/* Trigger Node */}
              <div className="p-4 rounded-2xl bg-purple-950/40 border border-purple-500/40 shadow-lg shadow-purple-950/50 space-y-1 w-full sm:w-44 text-left">
                <div className="text-[10px] font-mono uppercase tracking-wider text-purple-400 font-bold">
                  Trigger
                </div>
                <div className="text-xs font-bold text-white">GitHub Repo Ingest</div>
                <div className="text-[10px] text-slate-400 font-mono">Shallow tree clone</div>
              </div>

              {/* Connecting Wave SVG */}
              <div className="hidden sm:block w-12 text-purple-400">
                <svg className="w-full h-8" viewBox="0 0 48 32">
                  <path d="M 0 16 C 24 16, 24 8, 48 8" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="3 3" />
                  <path d="M 0 16 C 24 16, 24 24, 48 24" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="3 3" />
                </svg>
              </div>

              {/* Action Nodes Stack */}
              <div className="space-y-2.5 w-full sm:flex-1">
                {[
                  { label: 'Action 1', text: 'Parse AST Classes & Callers', sub: 'Compiler call tree trace' },
                  { label: 'Action 2', text: 'Extract Git Revision Blame', sub: 'Author churn velocity' },
                  { label: 'Action 3', text: 'Line-by-Line Citation Audit', sub: 'Zero hallucination verify' },
                ].map((act, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-2xl bg-[#090C16] border border-white/[0.08] hover:border-purple-500/30 transition-all flex items-center justify-between"
                  >
                    <div>
                      <div className="text-[10px] font-mono text-purple-300 font-bold uppercase">{act.label}</div>
                      <div className="text-xs font-semibold text-white">{act.text}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{act.sub}</div>
                    </div>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
