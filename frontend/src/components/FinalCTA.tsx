import React, { useState } from 'react'
import { Sparkles, ArrowRight } from 'lucide-react'
import { GithubIcon } from './GithubIcon'

interface FinalCTAProps {
  onSelectRepoAndQuery: (repoUrl: string, initialQuery: string) => void
}

export const FinalCTA: React.FC<FinalCTAProps> = ({ onSelectRepoAndQuery }) => {
  const [repoUrl, setRepoUrl] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!repoUrl.trim()) return
    onSelectRepoAndQuery(repoUrl.trim(), 'Explain high level architecture and entry points')
  }

  return (
    <section className="py-28 relative overflow-hidden border-b border-white/[0.06]">
      {/* Dramatic ambient radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-cyan-500/15 via-blue-500/10 to-transparent rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center relative z-10 space-y-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-cyan-400/25 bg-cyan-400/[0.06] text-cyan-300 text-xs font-mono">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Universal Codebase Archaeology</span>
        </div>

        <h2 className="text-4xl sm:text-6xl font-bold tracking-tight text-white leading-tight">
          Ready to understand{' '}
          <span className="bg-gradient-to-r from-cyan-300 via-sky-200 to-white bg-clip-text text-transparent">
            any codebase?
          </span>
        </h2>

        <p className="text-base sm:text-lg text-slate-400 max-w-xl mx-auto leading-relaxed font-normal">
          No credit card required. Point to any public GitHub repository or inspect your local tree with 100% citation-grounded verification.
        </p>

        {/* Action input bar */}
        <form onSubmit={handleSubmit} className="max-w-xl mx-auto pt-4">
          <div className="glass-panel p-2 rounded-2xl border border-white/10 flex flex-col sm:flex-row items-center gap-2 shadow-2xl">
            <div className="relative flex-1 w-full">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <GithubIcon className="w-4 h-4 text-slate-400" />
              </div>
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                className="w-full bg-[#05080F]/90 border border-white/5 rounded-xl pl-10 pr-4 py-2.5 text-xs sm:text-sm font-mono text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-colors"
              />
            </div>
            <button
              type="submit"
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-black font-semibold text-xs sm:text-sm transition-all shadow-lg shadow-cyan-500/20 whitespace-nowrap flex items-center justify-center space-x-2 cursor-pointer"
            >
              <span>Investigate Repo</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </section>
  )
}
