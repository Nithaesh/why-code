import React from 'react'
import { ExternalLink, ShieldCheck } from 'lucide-react'

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#05060C] text-slate-400 text-xs py-16 border-t border-white/[0.06]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-white/[0.06]">
          {/* Col 1: Brand */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-500 to-indigo-600 flex items-center justify-center font-mono font-black text-white shadow-md shadow-purple-500/30 text-base">
                W
              </div>
              <span className="font-bold text-white tracking-tight text-base">WhyCode</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300">
                v0.1.0
              </span>
            </div>
            <p className="text-slate-400 max-w-sm leading-relaxed text-xs">
              Evidence-backed codebase history & software archaeology platform. Built with Python AST parsing, Git revision blame, hybrid RRF search, and deterministic citation verification.
            </p>
            <div className="flex items-center space-x-3 text-slate-400 font-mono text-[11px]">
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                <span>FastAPI Engine</span>
              </span>
              <span>•</span>
              <span>React 19 + Vite</span>
              <span>•</span>
              <span>SQLite Embeddings</span>
            </div>
          </div>

          {/* Col 2: Navigation */}
          <div className="space-y-3">
            <h4 className="font-mono text-purple-300 uppercase text-[11px] tracking-wider font-semibold">
              Archaeology Suite
            </h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <a href="#workbench" className="hover:text-purple-300 transition-colors">
                  Agent Archaeology
                </a>
              </li>
              <li>
                <a href="#workbench" className="hover:text-purple-300 transition-colors">
                  Grounded Q&A
                </a>
              </li>
              <li>
                <a href="#workbench" className="hover:text-purple-300 transition-colors">
                  AST Code Graph
                </a>
              </li>
              <li>
                <a href="#workbench" className="hover:text-purple-300 transition-colors">
                  Git Churn Hotspots
                </a>
              </li>
              <li>
                <a href="#workbench" className="hover:text-purple-300 transition-colors">
                  Hybrid Search
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Resources & Docs */}
          <div className="space-y-3">
            <h4 className="font-mono text-purple-300 uppercase text-[11px] tracking-wider font-semibold">
              Documentation & API
            </h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <a
                  href="/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-purple-300 transition-colors flex items-center space-x-1"
                >
                  <span>FastAPI Swagger</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a
                  href="/redoc"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-purple-300 transition-colors flex items-center space-x-1"
                >
                  <span>ReDoc Specification</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-purple-300 transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-purple-300 transition-colors">
                  Architecture Bento
                </a>
              </li>
              <li>
                <a href="#faq" className="hover:text-purple-300 transition-colors">
                  FAQ
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-slate-500 text-[11px] font-mono">
          <div>
            © {new Date().getFullYear()} WhyCode Platform. Engineered for deterministic code understanding.
          </div>
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>100% Offline Testable</span>
            </span>
          </div>
        </div>
      </div>
    </footer>
  )
}
