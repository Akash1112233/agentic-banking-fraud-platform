import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ArrowUpRight, CheckCircle2, CircleDot, Network, RefreshCw, Search, ShieldCheck } from 'lucide-react'

type Alert = { id: number; transaction_id: string; risk_probability: number; status: string; created_at: string }
type Evidence = { alert: Record<string, unknown> | null; transaction: Record<string, unknown> | null; graph: { paths?: Array<Record<string, unknown>> } | null; explanation: { top_positive?: Array<Record<string, unknown>>; top_negative?: Array<Record<string, unknown>>; risk_probability?: number; source?: string } | null }
type Investigation = { transaction_id: string; status: string; summary: string; evidence: Evidence; limitations: string[]; llm_status?: string; llm_interpretation?: { conclusion?: string; rationale?: string; recommended_action?: string; confidence?: string; evidence_used?: string[]; limitations?: string[] } | null }

const formatProbability = (value: number) => `${(value * 100).toFixed(1)}%`
const display = (value: unknown) => value === null || value === undefined || value === '' ? '—' : String(value)

export default function App() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [investigation, setInvestigation] = useState<Investigation | null>(null)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadAlerts = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/v1/alerts?status=open&limit=100')
      if (!response.ok) throw new Error(`Alerts request failed (${response.status})`)
      const body = await response.json()
      setAlerts(body.items ?? [])
      if (!selectedId && body.items?.length) setSelectedId(body.items[0].transaction_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not reach the AML API')
    } finally { setLoading(false) }
  }

  const loadInvestigation = async (transactionId: string) => {
    if (!transactionId) return
    setError('')
    try {
      const response = await fetch(`/api/v1/investigations/${encodeURIComponent(transactionId)}`)
      if (!response.ok) throw new Error(`Investigation request failed (${response.status})`)
      setInvestigation(await response.json())
    } catch (err) { setError(err instanceof Error ? err.message : 'Investigation unavailable') }
  }

  useEffect(() => { void loadAlerts() }, [])
  useEffect(() => { void loadInvestigation(selectedId) }, [selectedId])

  const filteredAlerts = useMemo(() => alerts.filter(alert => alert.transaction_id.toLowerCase().includes(query.toLowerCase())), [alerts, query])
  const selectedAlert = alerts.find(alert => alert.transaction_id === selectedId)
  const transaction = investigation?.evidence.transaction ?? {}
  const explanation = investigation?.evidence.explanation
  const llmInterpretation = investigation?.llm_interpretation
  const graphPaths = investigation?.evidence.graph?.paths ?? []

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand"><div className="brand-mark"><ShieldCheck size={20} /></div><div><strong>AML Investigator</strong><span>Evidence Console</span></div></div>
      <div className="topbar-status"><span className="status-dot" /> API connected <button className="icon-button" onClick={loadAlerts} title="Refresh alerts"><RefreshCw size={17} /></button></div>
    </header>
    <main className="workspace">
      <section className="page-intro"><div><p className="eyebrow">Financial crime operations</p><h1>Open investigations</h1><p className="subtitle">Review model alerts with transaction, graph, and explainability evidence.</p></div><div className="review-badge"><CheckCircle2 size={16} /> Phases 1–8 connected</div></section>
      {error && <div className="error-banner"><AlertTriangle size={17} /> {error}</div>}
      <section className="dashboard-grid">
        <aside className="alert-panel panel">
          <div className="panel-heading"><div><p className="eyebrow">Queue</p><h2>{alerts.length} open alerts</h2></div><CircleDot size={19} className="muted" /></div>
          <div className="search-box"><Search size={16} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search transaction ID" /></div>
          <div className="alert-list">
            {loading && <div className="empty-state">Loading alert queue…</div>}
            {!loading && !filteredAlerts.length && <div className="empty-state">No matching alerts.</div>}
            {filteredAlerts.map(alert => <button key={alert.transaction_id} className={`alert-row ${selectedId === alert.transaction_id ? 'selected' : ''}`} onClick={() => setSelectedId(alert.transaction_id)}><div className="alert-row-top"><span className="transaction-id">{alert.transaction_id}</span><ArrowUpRight size={15} /></div><div className="alert-row-bottom"><span className="risk-pill">{formatProbability(alert.risk_probability)} risk</span><span>{alert.status}</span></div></button>)}
          </div>
        </aside>
        <section className="detail-panel">
          {!investigation && <div className="panel empty-detail"><Network size={38} /><h2>Select an alert</h2><p>Choose an item from the queue to retrieve its evidence.</p></div>}
          {investigation && <>
            <div className="investigation-header panel"><div><p className="eyebrow">Investigation / {investigation.status}</p><h2>{investigation.transaction_id}</h2><p className="summary">{investigation.summary}</p></div><div className="risk-score"><span>Risk score</span><strong>{formatProbability(Number(explanation?.risk_probability ?? selectedAlert?.risk_probability ?? 0))}</strong><div className="risk-track"><i style={{ width: `${Math.min(100, Number(explanation?.risk_probability ?? selectedAlert?.risk_probability ?? 0) * 100)}%` }} /></div></div></div>
            <div className="evidence-grid">
              <article className="evidence-card panel"><div className="card-title"><span className="card-icon teal"><CircleDot size={16} /></span><div><h3>Transaction evidence</h3><small>PostgreSQL</small></div></div><div className="kv-grid"><span>From account</span><strong>{display(transaction.from_account)}</strong><span>To account</span><strong>{display(transaction.to_account)}</strong><span>Amount paid</span><strong>{display(transaction.amount_paid)}</strong><span>Payment format</span><strong>{display(transaction.payment_format)}</strong></div></article>
              <article className="evidence-card panel"><div className="card-title"><span className="card-icon gold"><Network size={16} /></span><div><h3>Graph evidence</h3><small>Neo4j</small></div></div>{graphPaths.length ? <div className="path-list">{graphPaths.slice(0, 4).map((path, index) => <div className="path-item" key={index}><span>{display(path.sender)}</span><b>→</b><span>{display(path.receiver)}</span><em>{display(path.hops)} hops</em></div>)}</div> : <p className="unavailable">No graph path was returned for this investigation.</p>}</article>
              <article className="evidence-card panel explanation-card"><div className="card-title"><span className="card-icon coral"><ArrowUpRight size={16} /></span><div><h3>Model explanation</h3><small>{display(explanation?.source)}</small></div></div><div className="contribution-columns"><div><label>Raises risk</label>{(explanation?.top_positive ?? []).slice(0, 3).map(item => <div className="contribution positive" key={String(item.feature)}><span>{String(item.feature)}</span><strong>+{Number(item.contribution).toFixed(3)}</strong></div>)}</div><div><label>Lowers risk</label>{(explanation?.top_negative ?? []).slice(0, 3).map(item => <div className="contribution negative" key={String(item.feature)}><span>{String(item.feature)}</span><strong>{Number(item.contribution).toFixed(3)}</strong></div>)}</div></div></article>
            </div>
            <article className="analyst-card panel"><div className="card-title"><span className="card-icon teal"><ShieldCheck size={16} /></span><div><h3>LLM analyst interpretation</h3><small>{investigation.llm_status === 'available' ? 'Grounded in retrieved evidence' : `Status: ${display(investigation.llm_status)}`}</small></div></div>{llmInterpretation ? <div className="analyst-content"><strong>{display(llmInterpretation.conclusion)}</strong><p>{display(llmInterpretation.rationale)}</p><div className="recommended-action"><b>Recommended action</b><span>{display(llmInterpretation.recommended_action)}</span></div></div> : <p className="unavailable">Start Ollama with qwen3:14b to generate a plain-language analyst interpretation.</p>}</article>
            {!!investigation.limitations.length && <div className="limitations panel"><AlertTriangle size={16} /><div><strong>Evidence limitations</strong><span>{investigation.limitations.join(' • ')}</span></div></div>}
          </>}
        </section>
      </section>
    </main>
  </div>
}
