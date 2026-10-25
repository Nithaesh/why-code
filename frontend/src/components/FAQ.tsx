import React, { useState } from 'react'
import { ChevronDown, HelpCircle } from 'lucide-react'

interface FAQItem {
  question: string
  answer: string
}

export const FAQ: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  const faqs: FAQItem[] = [
    {
      question: 'How does WhyCode analyze any GitHub repository without cloning gigabytes of history?',
      answer:
        'WhyCode performs an optimized Git clone with a depth of 1 (or configured shallow depth) by default. It parses the actual AST syntax trees directly in memory and cross-references only the relevant commit logs, letting you clone and investigate massive repositories like Flask or Requests in seconds without filling your hard drive with disconnected history blobs.',
    },
    {
      question: 'How does the Citation Verifier mathematically eliminate hallucinations?',
      answer:
        'Standard LLM chat interfaces invent phantom file paths and lines. WhyCode operates a post-generation verification audit: every generated file citation (e.g. `path/to/file.py:40-65`) is parsed and compared against the on-disk file system and chunk boundaries. If lines are fictitious or non-existent, WhyCode marks the citation as UNVERIFIED, penalizes the grounding score, and flags the claim.',
    },
    {
      question: 'Can WhyCode run completely offline without paying for API calls?',
      answer:
        'Yes! All indexing, AST parsing, BM25 lexical tokenization, and vector storage happen in local SQLite database files. Additionally, WhyCode includes a deterministic DiskCache for all LLM and embedding calls. When running automated test suites or replaying past queries, WhyCode makes 0 external network requests, resulting in $0 API cost.',
    },
    {
      question: 'What programming languages and AST structures are supported?',
      answer:
        'WhyCode currently features deep AST parsing for Python, extracting classes, functions, asynchronous methods, parameter signatures, and hierarchical call trees. Furthermore, WhyCode indexes Git commit histories, diffs, and lexical token streams across all languages in your repository.',
    },
    {
      question: 'How is WhyCode different from Copilot or standard ChatGPT?',
      answer:
        'Copilot and ChatGPT operate on limited immediate file context or simple semantic search. WhyCode is a stateful software archaeology system: it autonomously formulates multi-hop hypotheses, queries AST caller hierarchies, correlates Git churn velocity, and enforces a line-by-line citation audit so you never act on imagined code architecture.',
    },
  ]

  const toggle = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx)
  }

  return (
    <section id="faq" className="py-24 border-b border-white/[0.06] relative">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 relative z-10">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300 text-xs font-mono">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Frequently Asked Questions</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
            Everything you need to know.
          </h2>
          <p className="text-base text-slate-400 leading-relaxed font-normal">
            Clear technical answers on architecture, citation verification, and GitHub repository analysis.
          </p>
        </div>

        <div className="space-y-3.5">
          {faqs.map((faq, idx) => {
            const isOpen = openIndex === idx
            return (
              <div
                key={idx}
                className="glass-panel rounded-3xl border border-white/[0.08] transition-all duration-200 overflow-hidden shadow-lg"
              >
                <button
                  type="button"
                  onClick={() => toggle(idx)}
                  className="w-full p-6 text-left flex items-center justify-between gap-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
                >
                  <span className="text-base sm:text-lg font-medium text-white">{faq.question}</span>
                  <div
                    className={`w-8 h-8 rounded-full border border-white/10 flex items-center justify-center shrink-0 text-slate-400 transition-transform duration-300 ${
                      isOpen ? 'rotate-180 text-purple-300 border-purple-500/40 bg-purple-500/10' : ''
                    }`}
                  >
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </button>
                {isOpen && (
                  <div className="px-6 pb-6 text-sm text-slate-400 leading-relaxed border-t border-white/[0.04] pt-4 font-normal">
                    {faq.answer}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
