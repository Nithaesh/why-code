import React from 'react'
import { GitBranch, Layers, Search, ShieldCheck, Sparkles } from 'lucide-react'

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Point to Any GitHub Repository',
      tagline: 'Instant shallow clone & checkout',
      description:
        'Enter any public or enterprise GitHub URL. WhyCode clones the exact tree revision without bloating your machine with gigabytes of detached object blobs.',
      icon: GitBranch,
      codeSnippet: '$ whycode clone https://github.com/pallets/flask\n✓ Cloned master (depth=1)\n✓ 142 Python source files detected',
      accent: 'cyan',
    },
    {
      num: '02',
      title: 'Syntactic AST & Git Graph Extraction',
      tagline: 'AST parser + commit blame trace',
      description:
        'Extracts classes, methods, docstrings, and call-graph hierarchies. Cross-references git blame logs to track author churn and modification velocity over time.',
      icon: Layers,
      codeSnippet: 'Flask.route() -> App.add_url_rule()\n├── Callers: Blueprint.route, testing.client\n└── Churn: 18 revisions across 4 releases',
      accent: 'blue',
    },
    {
      num: '03',
      title: 'Multi-Hop Agent Investigation',
      tagline: 'Hypothesis testing & hybrid search',
      description:
        'The ReAct archaeology agent explores AST symbol dependencies, performs hybrid lexical and semantic code search, and recursively gathers corroborating diffs.',
      icon: Search,
      codeSnippet: '[Step 1] Inspect AST callers of verify_token\n[Step 2] Search git commits matching "auth"\n[Step 3] Diff commit b8f3a1 vs current tree',
      accent: 'sky',
    },
    {
      num: '04',
      title: 'Audited Citation Verification',
      tagline: 'Zero hallucination guarantee',
      description:
        'Every factual claim and file reference is strictly audited against on-disk lines. If a referenced chunk or symbol does not exist, confidence drops and the claim is flagged.',
      icon: ShieldCheck,
      codeSnippet: 'Confidence: 96.4%\n✓ flask/app.py:1200-1240 [VERIFIED]\n✓ flask/scaffold.py:45-80  [VERIFIED]\n0 Hallucinated references',
      accent: 'emerald',
    },
  ]

  return (
    <section id="how-it-works" className="py-24 border-b border-white/[0.06] relative overflow-hidden">
      {/* Background radial glow */}
      <div className="absolute top-1/3 left-1/4 w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-sky-400/20 bg-sky-400/[0.05] text-sky-300 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Archaeology Pipeline</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
            How WhyCode explains any codebase.
          </h2>
          <p className="text-base text-slate-400 leading-relaxed font-normal">
            Traditional AI guesses how code works based on outdated pretraining. WhyCode executes a deterministic 4-phase
            software archaeology pipeline on active source trees.
          </p>
        </div>

        {/* 4 Step Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {steps.map((step) => {
            const Icon = step.icon
            return (
              <div
                key={step.num}
                className="group p-6 sm:p-8 rounded-2xl glass-panel border border-white/[0.08] hover:border-cyan-400/30 transition-all duration-300 relative overflow-hidden flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-3xl font-black text-cyan-400/40 group-hover:text-cyan-400/80 transition-colors">
                      {step.num}
                    </span>
                    <div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center text-cyan-300">
                      <Icon className="w-5 h-5" />
                    </div>
                  </div>

                  <div>
                    <div className="text-xs font-mono text-cyan-400/80 uppercase tracking-wider mb-1">
                      {step.tagline}
                    </div>
                    <h3 className="text-xl font-semibold text-white tracking-tight">
                      {step.title}
                    </h3>
                  </div>

                  <p className="text-sm text-slate-400 leading-relaxed">
                    {step.description}
                  </p>
                </div>

                {/* Simulated Console Snippet */}
                <div className="mt-6 pt-4 border-t border-white/[0.06]">
                  <div className="bg-[#05080E] rounded-xl p-3.5 border border-white/[0.05] font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed overflow-x-auto">
                    {step.codeSnippet}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
