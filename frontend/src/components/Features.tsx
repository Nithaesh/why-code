import React from 'react'
import { Layers, Search, ShieldCheck, Flame, Cpu, Zap, CheckCircle2 } from 'lucide-react'

export const Features: React.FC = () => {
  return (
    <section id="features" className="py-24 border-b border-white/[0.06] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300 text-xs font-mono">
            <Cpu className="w-3.5 h-3.5" />
            <span>Architecture & Engine</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
            Engineered for deterministic precision.
          </h2>
          <p className="text-base text-slate-400 leading-relaxed font-normal">
            Most codebase tools paste entire files into an LLM window and hope for the best. 
            WhyCode couples compiler AST analysis with Git version trees for verifiable answers.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Large Bento (span 2 cols) */}
          <div className="md:col-span-2 p-8 rounded-3xl glass-panel border border-white/[0.08] hover:border-purple-500/40 transition-all duration-300 relative overflow-hidden flex flex-col justify-between shadow-xl">
            <div className="space-y-4 relative z-10">
              <div className="w-11 h-11 rounded-2xl bg-purple-500/10 border border-purple-500/25 flex items-center justify-center text-purple-300 shadow-sm shadow-purple-950/40">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="text-2xl font-bold text-white tracking-tight">
                Syntactic AST Call Trees & Inverted Hierarchies
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed max-w-xl">
                Inspect every class, method, function signature, parameter, and caller across your entire codebase. 
                WhyCode traverses downstream callers and upstream callees directly from the compiler AST, allowing you to anticipate breaking changes before they hit production.
              </p>
            </div>

            <div className="mt-8 bg-[#05060C] p-4 rounded-2xl border border-white/[0.06] font-mono text-xs text-slate-300 space-y-1.5 overflow-x-auto shadow-inner">
              <div className="text-slate-500">// Upstream callers detected for AuthHandler.verify_jwt:</div>
              <div className="text-purple-300 font-medium">↳ api.v1.endpoints.auth_login (app/api/endpoints.py:84)</div>
              <div className="text-indigo-300">↳ middleware.session_guard (app/middleware/auth.py:22)</div>
              <div className="text-slate-400">↳ tests.unit.test_auth_tokens (tests/test_auth.py:112)</div>
            </div>
          </div>

          {/* Card 2: Citation Verifier */}
          <div className="p-8 rounded-3xl glass-panel border border-white/[0.08] hover:border-emerald-500/40 transition-all duration-300 flex flex-col justify-between shadow-xl">
            <div className="space-y-4">
              <div className="w-11 h-11 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 shadow-sm shadow-emerald-950/40">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-xl font-bold text-white tracking-tight">
                Quantitative Citation Verification
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Zero hallucination tolerance. Every citation is parsed for valid file paths, actual line boundaries, and AST symbol existence.
              </p>
            </div>

            <div className="mt-6 pt-4 border-t border-white/[0.06] space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Audit Confidence</span>
                <span className="text-emerald-400 font-bold">100% Verified</span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                <div className="bg-emerald-400 h-full w-full rounded-full" />
              </div>
            </div>
          </div>

          {/* Card 3: Hybrid Search */}
          <div className="p-8 rounded-3xl glass-panel border border-white/[0.08] hover:border-purple-500/40 transition-all duration-300 flex flex-col justify-between shadow-xl">
            <div className="space-y-4">
              <div className="w-11 h-11 rounded-2xl bg-purple-500/10 border border-purple-500/25 flex items-center justify-center text-purple-300 shadow-sm shadow-purple-950/40">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-xl font-bold text-white tracking-tight">
                Reciprocal Rank Fusion
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Blends BM25 keyword matching with dense embedding cosine vectors so variable names and semantic concepts both rank at the top.
              </p>
            </div>

            <div className="mt-6 bg-[#05060C] p-3 rounded-2xl border border-white/[0.06] font-mono text-xs text-purple-300 shadow-inner">
              Score = RRF(BM25, Cosine, k=60)
            </div>
          </div>

          {/* Card 4: Git Churn Hotspots */}
          <div className="p-8 rounded-3xl glass-panel border border-white/[0.08] hover:border-fuchsia-500/40 transition-all duration-300 flex flex-col justify-between shadow-xl">
            <div className="space-y-4">
              <div className="w-11 h-11 rounded-2xl bg-fuchsia-500/10 border border-fuchsia-500/25 flex items-center justify-center text-fuchsia-400 shadow-sm shadow-fuchsia-950/40">
                <Flame className="w-5 h-5" />
              </div>
              <h3 className="text-xl font-bold text-white tracking-tight">
                Git Churn Velocity
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Pinpoint the most frequently modified symbols and unstable files in any repo to quickly find where technical debt accumulates.
              </p>
            </div>

            <div className="mt-6 flex items-center space-x-2 text-xs font-mono text-fuchsia-300">
              <Flame className="w-4 h-4 text-fuchsia-400" />
              <span>Ranked by modification frequency</span>
            </div>
          </div>

          {/* Card 5: Deterministic Local SQLite */}
          <div className="p-8 rounded-3xl glass-panel border border-white/[0.08] hover:border-indigo-500/40 transition-all duration-300 flex flex-col justify-between shadow-xl">
            <div className="space-y-4">
              <div className="w-11 h-11 rounded-2xl bg-indigo-500/10 border border-indigo-500/25 flex items-center justify-center text-indigo-300 shadow-sm shadow-indigo-950/40">
                <Zap className="w-5 h-5" />
              </div>
              <h3 className="text-xl font-bold text-white tracking-tight">
                Deterministic SQLite Cache
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Zero external database dependencies. All embeddings, chunk manifests, and LLM responses are indexed locally in SQLite for $0 test costs.
              </p>
            </div>

            <div className="mt-6 flex items-center space-x-2 text-xs font-mono text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>Full offline development ready</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
