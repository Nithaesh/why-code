import React, { useState } from 'react'
import { FolderGit2, GitBranch, ArrowRight, RefreshCw, CheckCircle2 } from 'lucide-react'

interface HeaderProps {
  currentRepo: string
  modelName: string
  onCloneRepo: (url: string) => Promise<void>
  cloneLoading: boolean
  onNavigateToWorkbench: () => void
}

export const Header: React.FC<HeaderProps> = ({
  currentRepo,
  modelName,
  onCloneRepo,
  cloneLoading,
  onNavigateToWorkbench,
}) => {
  const [modalOpen, setModalOpen] = useState(false)
  const [urlInput, setUrlInput] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!urlInput.trim()) return
    setErrorMsg(null)
    setSuccessMsg(null)
    try {
      await onCloneRepo(urlInput.trim())
      setSuccessMsg(`Switched repository successfully!`)
      setTimeout(() => {
        setModalOpen(false)
        setUrlInput('')
        setSuccessMsg(null)
      }, 1200)
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to clone repository')
    }
  }

  return (
    <>
      <header className="sticky top-0 z-50 backdrop-blur-2xl bg-[#07090E]/80 border-b border-white/[0.06] transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-400 via-sky-400 to-blue-600 flex items-center justify-center font-mono font-black text-black shadow-md shadow-cyan-500/20 text-base tracking-tighter">
              W
            </div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold tracking-tight text-white text-base">WhyCode</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-white/10 bg-white/[0.04] text-slate-400">
                v0.1.0
              </span>
            </div>
          </div>

          {/* Center Navigation Links (Apple/Google Style) */}
          <nav className="hidden md:flex items-center space-x-8 text-xs font-medium text-slate-400">
            <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
            <a href="#features" className="hover:text-white transition-colors">Architecture</a>
            <a href="#workbench" onClick={onNavigateToWorkbench} className="hover:text-cyan-400 transition-colors">Live Workbench</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
            <a href="/docs" target="_blank" className="hover:text-white transition-colors flex items-center space-x-1">
              <span>Swagger API</span>
              <span className="text-[10px] text-cyan-400">↗</span>
            </a>
          </nav>

          {/* Right Controls: Active Repo & Live Cloner */}
          <div className="flex items-center space-x-3 text-xs font-mono">
            {/* Active Repo Chip */}
            <button
              onClick={() => setModalOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-white/[0.03] hover:bg-white/[0.07] border border-white/10 text-slate-300 hover:text-white transition-all cursor-pointer group"
              title="Click to switch or clone another GitHub repository"
            >
              <FolderGit2 className="w-3.5 h-3.5 text-cyan-400 group-hover:rotate-12 transition-transform" />
              <span className="font-medium truncate max-w-[140px]">{currentRepo || 'whycode'}</span>
              <span className="text-[10px] text-slate-500 group-hover:text-cyan-400 transition-colors">▾</span>
            </button>

            {/* Model Status Dot */}
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-black/40 border border-white/[0.06]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-[11px] text-slate-400">{modelName || 'gemini-3.5-flash-lite'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* GitHub Repo Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel max-w-lg w-full p-6 rounded-2xl border border-white/10 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <div className="flex items-center space-x-2">
                <GitBranch className="w-4 h-4 text-cyan-400" />
                <h3 className="font-semibold text-white text-sm">Analyze Any GitHub Repository</h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-500 hover:text-white transition-colors text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <p className="text-slate-400 text-xs leading-relaxed">
              WhyCode will shallow-clone the repository into local memory, extract its Python AST symbol graph, index its code chunks, and enable instant grounded Q&A and multi-hop investigations.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4 pt-1">
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">GitHub Repository URL:</label>
                <input
                  type="text"
                  required
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://github.com/pallets/flask"
                  className="w-full bg-[#05080F] border border-white/10 rounded-xl px-3.5 py-2.5 text-xs font-mono text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 transition-colors"
                />
              </div>

              {/* Quick Select Presets */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] font-mono text-slate-500">Popular:</span>
                {['https://github.com/pallets/flask', 'https://github.com/psf/requests', 'https://github.com/tiangolo/fastapi'].map(
                  (sample) => (
                    <button
                      key={sample}
                      type="button"
                      onClick={() => setUrlInput(sample)}
                      className="text-[10px] px-2.5 py-1 rounded-full bg-white/[0.03] hover:bg-cyan-500/10 border border-white/10 text-slate-300 font-mono transition-colors cursor-pointer"
                    >
                      {sample.split('/').pop()}
                    </button>
                  )
                )}
              </div>

              {errorMsg && (
                <div className="p-3 rounded-xl text-xs font-mono bg-rose-500/10 text-rose-300 border border-rose-500/30">
                  {errorMsg}
                </div>
              )}

              {successMsg && (
                <div className="p-3 rounded-xl text-xs font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{successMsg}</span>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={cloneLoading || !urlInput.trim()}
                  className="px-5 py-2 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-black font-semibold text-xs transition-all disabled:opacity-50 flex items-center space-x-1.5 cursor-pointer shadow-md shadow-cyan-400/20"
                >
                  {cloneLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Cloning & Indexing...</span>
                    </>
                  ) : (
                    <>
                      <span>Clone & Analyze</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
