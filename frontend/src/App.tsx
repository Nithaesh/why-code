import React, { useState, useEffect } from 'react'
import { Header } from './components/Header'
import { Hero } from './components/Hero'
import { HowItWorks } from './components/HowItWorks'
import { Features } from './components/Features'
import { Workbench } from './components/Workbench'
import type {
  InvestigationResult,
  AskResult,
  SymbolResult,
  HotspotItem,
  SearchChunk,
} from './components/Workbench'
import { FAQ } from './components/FAQ'
import { FinalCTA } from './components/FinalCTA'
import { Footer } from './components/Footer'

interface HealthData {
  status: string
  version: string
  repo_path: string
  provider: string
  model: string
  has_api_key: boolean
}

export function App() {
  const [activeTab, setActiveTab] = useState<'investigate' | 'ask' | 'symbol' | 'churn' | 'search'>('investigate')
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(false)
  const [cloneLoading, setCloneLoading] = useState(false)

  // Tab 1: Investigate
  const [invQuery, setInvQuery] = useState('')
  const [invSteps, setInvSteps] = useState(3)
  const [invData, setInvData] = useState<InvestigationResult | null>(null)

  // Tab 2: Ask
  const [askQuery, setAskQuery] = useState('')
  const [askMode, setAskMode] = useState<'hybrid' | 'lexical' | 'semantic'>('hybrid')
  const [askData, setAskData] = useState<AskResult | null>(null)

  // Tab 3: Symbol
  const [symbolQuery, setSymbolQuery] = useState('')
  const [symbolData, setSymbolData] = useState<SymbolResult | null>(null)

  // Tab 4: Churn
  const [churnData, setChurnData] = useState<HotspotItem[]>([])

  // Tab 5: Search
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState<'hybrid' | 'lexical' | 'semantic'>('hybrid')
  const [searchResults, setSearchResults] = useState<SearchChunk[]>([])

  // Fetch Health
  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/v1/health')
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      }
    } catch {
      setHealth(null)
    }
  }

  useEffect(() => {
    fetchHealth()
  }, [])

  // Auto-fetch Churn Hotspots
  const fetchChurn = async () => {
    try {
      const res = await fetch('/api/v1/churn?limit=10')
      if (res.ok) {
        const data = await res.json()
        setChurnData(data.hotspots)
      }
    } catch (err) {
      console.error('Failed to fetch churn:', err)
    }
  }

  useEffect(() => {
    if (activeTab === 'churn') {
      fetchChurn()
    }
  }, [activeTab])

  // Handle GitHub Repo Clone / Switch
  const handleCloneRepo = async (url: string) => {
    setCloneLoading(true)
    try {
      const res = await fetch('/api/v1/repo/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Clone failed')
      await fetchHealth()
      // Reset past query state for new repo
      setInvData(null)
      setAskData(null)
      setSymbolData(null)
      setSearchResults([])
      if (activeTab === 'churn') {
        fetchChurn()
      }
    } finally {
      setCloneLoading(false)
    }
  }

  // Handle Selection from Hero / Final CTA
  const handleSelectRepoAndQuery = async (repoUrl: string, initialQuery: string) => {
    if (repoUrl.trim()) {
      try {
        await handleCloneRepo(repoUrl.trim())
      } catch (err: any) {
        alert(err.message || 'Failed to clone repository')
      }
    }

    if (initialQuery.trim()) {
      setInvQuery(initialQuery)
      setAskQuery(initialQuery)
      setActiveTab('investigate')
    }

    // Scroll seamlessly to workbench
    const workbenchEl = document.getElementById('workbench')
    if (workbenchEl) {
      workbenchEl.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const navigateToWorkbench = () => {
    const workbenchEl = document.getElementById('workbench')
    if (workbenchEl) {
      workbenchEl.scrollIntoView({ behavior: 'smooth' })
    }
  }

  // Handle Investigation
  const handleInvestigate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!invQuery.trim()) return
    setLoading(true)
    setInvData(null)

    try {
      const res = await fetch('/api/v1/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: invQuery, max_steps: invSteps }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Investigation failed')
      }
      const data = await res.json()
      setInvData(data)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Handle Ask Q&A
  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!askQuery.trim()) return
    setLoading(true)
    setAskData(null)

    try {
      const res = await fetch('/api/v1/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: askQuery, mode: askMode, top_k: 4 }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Q&A failed')
      }
      const data = await res.json()
      setAskData(data)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Handle Symbol Lookup
  const handleSymbol = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbolQuery.trim()) return
    setLoading(true)
    setSymbolData(null)

    try {
      const res = await fetch(`/api/v1/symbol/${encodeURIComponent(symbolQuery.trim())}`)
      if (!res.ok) throw new Error('Symbol lookup failed')
      const data = await res.json()
      setSymbolData(data)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Handle Code Search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setLoading(true)
    setSearchResults([])

    try {
      const res = await fetch('/api/v1/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, mode: searchMode, top_k: 5 }),
      })
      if (!res.ok) throw new Error('Search failed')
      const data = await res.json()
      setSearchResults(data.results)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const repoName = health?.repo_path ? health.repo_path.split(/[\\/]/).pop() || health.repo_path : 'Local Repo'

  return (
    <div className="min-h-screen bg-[#06070B] text-slate-100 flex flex-col font-sans selection:bg-purple-500 selection:text-white">
      {/* 1. Header with Repository Switcher Modal & System Health */}
      <Header
        currentRepo={repoName}
        modelName={health?.model || 'Gemini 2.5 Flash'}
        onCloneRepo={handleCloneRepo}
        cloneLoading={cloneLoading}
        onNavigateToWorkbench={navigateToWorkbench}
      />

      {/* 2. Hero: Universal GitHub Q&A Centerpiece with Presets & Trust Metrics */}
      <Hero
        onSelectRepoAndQuery={handleSelectRepoAndQuery}
        currentRepo={repoName}
      />

      {/* 3. Interactive Workbench: 5 Capabilities */}
      <Workbench
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        invQuery={invQuery}
        setInvQuery={setInvQuery}
        invSteps={invSteps}
        setInvSteps={setInvSteps}
        invData={invData}
        handleInvestigate={handleInvestigate}
        askQuery={askQuery}
        setAskQuery={setAskQuery}
        askMode={askMode}
        setAskMode={setAskMode}
        askData={askData}
        handleAsk={handleAsk}
        symbolQuery={symbolQuery}
        setSymbolQuery={setSymbolQuery}
        symbolData={symbolData}
        handleSymbol={handleSymbol}
        churnData={churnData}
        fetchChurn={fetchChurn}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        searchMode={searchMode}
        setSearchMode={setSearchMode}
        searchResults={searchResults}
        handleSearch={handleSearch}
        loading={loading}
        repoName={repoName}
      />

      {/* 4. How It Works: The 4-Phase Archaeology Pipeline */}
      <HowItWorks />

      {/* 5. Features: Apple/Awwwards Architecture Bento Grid */}
      <Features />

      {/* 6. Frequently Asked Questions */}
      <FAQ />

      {/* 7. Dramatic Final Call to Action */}
      <FinalCTA onSelectRepoAndQuery={handleSelectRepoAndQuery} />

      {/* 8. Refined Editorial Footer */}
      <Footer />
    </div>
  )
}
export default App
