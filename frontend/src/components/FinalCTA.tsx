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
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-gradient-to-tr from-purple-600/20 via-fuchsia-600/15 to-transparent rounded-full blur-[160px] pointer-events-none" />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center relative z-10 space-y-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300 text-xs font-mono">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Universal Codebase Archaeology</span>
        </div>

        <h2 className="text-4xl sm:text-6xl font-bold tracking-tight text-white leading-tight">
          Ready to understand{' '}
          <span className="bg-gradient-to-r from-purple-300 via-fuchsia-200 to-white bg-clip-text text-transparent">
            any codebase?
          </span>
        </h2>

        <p className="text-base sm:text-lg text-slate-400 max-w-xl mx-auto leading-relaxed font-normal">
          No credit card required. Point to any public GitHub repository or inspect your local tree with 100% citation-grounded verification.
        </p>

        {/* Action input bar */}
        <form onSubmit={handleSubmit} className="max-w-xl mx-auto pt-4">
          <div className="glass-panel p-2.5 rounded-3xl border border-purple-500/30 flex flex-col sm:flex-row items-center gap-2 shadow-2xl shadow-purple-950/50">
            <div className="relative flex-1 w-full">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-purple-400">
                <GithubIcon className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                className="w-full bg-[#05060C]/90 border border-white/5 rounded-2xl pl-10 pr-4 py-2.5 text-xs sm:text-sm font-mono text-white placeholder-slate-500 focus:outline-none focus:border-purple-400 transition-colors"
              />
            </div>
            <button
              type="submit"
              className="w-full sm:w-auto px-6 py-2.5 rounded-2xl bg-gradient-to-r from-purple-500 via-fuchsia-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 text-white font-semibold text-xs sm:text-sm transition-all shadow-lg shadow-purple-500/30 whitespace-nowrap flex items-center justify-center space-x-2 cursor-pointer"
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
