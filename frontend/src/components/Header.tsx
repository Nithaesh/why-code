import React, { useState } from 'react'
import { FolderGit2, GitBranch, ArrowRight, RefreshCw, CheckCircle2, Bell, Sparkles } from 'lucide-react'

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
      setSuccessMsg('Switched repository successfully!')
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
      <header className="sticky top-0 z-50 backdrop-blur-2xl bg-[#070810]/85 border-b border-white/[0.07] transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between gap-4">
          {/* Logo & Brand matching reference image */}
          <div
            className="flex items-center space-x-3 cursor-pointer group"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-600 via-fuchsia-500 to-indigo-500 p-[1px] shadow-lg shadow-purple-500/25">
              <div className="w-full h-full bg-[#0B0D18] rounded-[15px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-purple-400 group-hover:scale-110 transition-transform" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold tracking-tight text-white text-base">WhyCode</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300">
                  v0.1.0
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono tracking-wide">
                AI CODEBASE ARCHAEOLOGY
              </div>
            </div>
          </div>

          {/* Center Navigation Links */}
          <nav className="hidden md:flex items-center space-x-7 text-xs font-medium text-slate-400">
            <a href="#overview" className="hover:text-purple-300 transition-colors">
              Overview
            </a>
            <button
              onClick={onNavigateToWorkbench}
              className="hover:text-purple-300 transition-colors cursor-pointer"
            >
              Workbench
            </button>
            <a href="#how-it-works" className="hover:text-purple-300 transition-colors">
              How It Works
            </a>
            <a href="#features" className="hover:text-purple-300 transition-colors">
              Architecture
            </a>
            <a href="#faq" className="hover:text-purple-300 transition-colors">
              FAQ
            </a>
          </nav>

          {/* Right Action Controls */}
          <div className="flex items-center space-x-3">
            {/* Active Repository Pill */}
            <button
              onClick={() => setModalOpen(true)}
              className="px-3.5 py-1.5 rounded-xl border border-purple-500/20 bg-purple-950/20 hover:border-purple-500/40 text-slate-200 hover:text-white transition-all flex items-center space-x-2 text-xs font-mono shadow-sm shadow-purple-950/40 cursor-pointer"
            >
              <FolderGit2 className="w-3.5 h-3.5 text-purple-400" />
              <span className="max-w-[130px] truncate text-purple-200">{currentRepo}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300">Switch</span>
            </button>

            {/* Model status pill with glowing dot */}
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl border border-white/[0.08] bg-[#0E111F]/80 text-xs font-mono">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-slate-300">{modelName}</span>
            </div>

            {/* Notification / docs icon */}
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              title="FastAPI Swagger Documentation"
              className="w-9 h-9 rounded-xl border border-white/[0.08] bg-[#0E111F]/80 hover:border-purple-500/40 hover:text-purple-300 text-slate-400 flex items-center justify-center transition-all cursor-pointer"
            >
              <Bell className="w-4 h-4" />
            </a>
          </div>
        </div>
      </header>

      {/* GitHub Clone / Switch Repository Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-lg p-7 rounded-3xl border border-purple-500/30 space-y-5 relative overflow-hidden shadow-2xl shadow-purple-950/50 animate-in fade-in zoom-in-95 duration-200">
            <div className="absolute top-0 right-0 w-60 h-60 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="flex items-center justify-between relative z-10">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300">
                  <GitBranch className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Load Any GitHub Repository</h3>
                  <p className="text-[11px] text-slate-400">Shallow clones and hot-swaps active AST indices</p>
                </div>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="w-7 h-7 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 flex items-center justify-center text-xs transition-colors cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
              <div>
                <label className="block text-xs font-mono text-purple-300 mb-1.5">
                  GitHub Repository Clone URL:
                </label>
                <input
                  type="text"
                  required
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://github.com/pallets/flask"
                  className="w-full bg-[#05060C] border border-white/10 rounded-xl px-4 py-2.5 text-xs sm:text-sm font-mono text-white placeholder-slate-500 focus:outline-none focus:border-purple-400 transition-colors"
                />
              </div>

              {errorMsg && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono">
                  {errorMsg}
                </div>
              )}

              {successMsg && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{successMsg}</span>
                </div>
              )}

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={cloneLoading || !urlInput.trim()}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-400 hover:to-indigo-400 text-white font-semibold text-xs transition-all shadow-lg shadow-purple-500/25 disabled:opacity-50 cursor-pointer flex items-center space-x-2"
                >
                  {cloneLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Cloning Tree...</span>
                    </>
                  ) : (
                    <>
                      <span>Clone & Index</span>
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
