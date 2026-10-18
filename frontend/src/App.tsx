import { useEffect, useState } from 'react'
import IngestionPanel from './IngestionPanel'
import './App.css'
const API_BASE_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

type QueryCitation = {
  source_url: string
  source_sentence: string
  chunk_id: string
  confidence: number
  claim_id: string | null
  subject?: string | null
  predicate?: string | null
  object?: string | null
}

type QueryPlanStep = {
  step_id: number
  operation: string
  target: string | null
  entity: string | null
  predicate: string | null
}

type QueryResult = {
  chunk_id: string
  text: string
  score: number
  source_url: string
  section_heading: string
  strategy: string
  claim_id: string | null
  subject: string | null
  predicate: string | null
  object: string | null
  confidence: number
}

type QueryResponse = {
  query: string
  answer: string | null
  intent: string
  status: string
  confidence: number
  attempts: number
  latency_ms: number
  citations: QueryCitation[]
  termination_reason: string | null

  plan: {
    intent: string
    termination_reason: string | null
    steps: QueryPlanStep[]
  } | null

  results: QueryResult[]
}

type GraphNode = {
  id: string
  name: string
  entity_type: string | null
}

type GraphEdge = {
  source_id: string
  source: string
  predicate: string
  target_id: string
  target: string
  confidence: number | null
  claim_id: string | null
  source_url: string | null
}

type GraphSnapshot = {
  status: string
  counts: {
    pages: number
    chunks: number
    entities: number
    claims: number
    relations: number
  }
  nodes: GraphNode[]
  edges: GraphEdge[]
}

type BenchmarkStrategyKey =
  | 'bm25'
  | 'dense'
  | 'graph'
  | 'hybrid_rrf'

type BenchmarkSummary = {
  num_queries: number
  avg_recall_at_1: number
  avg_recall_at_3: number
  avg_recall_at_5: number
  mrr: number
  avg_latency_ms: number
}

type BenchmarkSnapshot = {
  status: string
  strategies: Partial<
    Record<BenchmarkStrategyKey, BenchmarkSummary>
  >
  multi_hop: {
    num_queries: number
    path_accuracy: number
    avg_latency_ms: number
  }
}

const quickQueries = [
  'What does FastAPI depend on?',
  'Which server is used to serve FastAPI applications?',
  'What does FastAPI depend on that also uses HTTPX?',
]

const strategyDefinitions = [
  {
    key: 'bm25',
    name: 'BM25',
    description: 'Keyword-based retrieval',
  },
  {
    key: 'dense',
    name: 'Dense',
    description: 'Semantic vector search',
  },
  {
    key: 'graph',
    name: 'Graph',
    description: 'Knowledge graph traversal',
  },
  {
    key: 'hybrid_rrf',
    name: 'Hybrid RRF',
    description: 'Rank fusion across retrievers',
  },
] as const

function App() {
  const [query, setQuery] = useState(quickQueries[2])
  const [hasPreview, setHasPreview] = useState(false)
  const [activeNav, setActiveNav] = useState('Overview')
  const [isLoading, setIsLoading] = useState(false)
  const [queryResponse, setQueryResponse] =
  useState<QueryResponse | null>(null)
  const [queryError, setQueryError] = useState('')

  const [graphData, setGraphData] =
  useState<GraphSnapshot | null>(null)
  const [graphRefreshKey, setGraphRefreshKey] = useState(0)

  const [benchmarkData, setBenchmarkData] =
  useState<BenchmarkSnapshot | null>(null)

const [benchmarkLoading, setBenchmarkLoading] =
  useState(true)

const [benchmarkError, setBenchmarkError] =
  useState('')

const [graphLoading, setGraphLoading] = useState(true)

const [graphError, setGraphError] = useState('')

const [selectedGraphNodeId, setSelectedGraphNodeId] =
  useState<string | null>(null)

useEffect(() => {
  let active = true

  const loadGraph = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/graph`,
      )

      if (!response.ok) {
        throw new Error(
          `Graph API returned ${response.status}`,
        )
      }

      const data = (await response.json()) as GraphSnapshot

      if (active) {
        setGraphData(data)
        setGraphError('')
      }
    } catch (error) {
      if (active) {
        setGraphError(
          error instanceof Error
            ? error.message
            : 'Unable to load graph data.',
        )
      }
    } finally {
      if (active) {
        setGraphLoading(false)
      }
    }
  }

  void loadGraph()

  return () => {
    active = false
  }
}, [graphRefreshKey])

  const graphNodesForView = (() => {
  const uniqueNodes = new Map<string, GraphNode>()

  for (const edge of graphData?.edges ?? []) {
    uniqueNodes.set(edge.source_id, {
      id: edge.source_id,
      name: edge.source,
      entity_type: null,
    })

    uniqueNodes.set(edge.target_id, {
      id: edge.target_id,
      name: edge.target,
      entity_type: null,
    })
  }

  return Array.from(uniqueNodes.values()).slice(0, 12)
})()

const preferredGraphPositions: Record<
  string,
  { x: number; y: number }
> = {
  fastapi: { x: 280, y: 145 },
  pydantic: { x: 155, y: 55 },
  starlette: { x: 430, y: 55 },
  uvicorn: { x: 120, y: 245 },
  httpx: { x: 450, y: 245 },
  put: { x: 355, y: 250 },
  orjson: { x: 55, y: 155 },
  orjsonresponse: { x: 65, y: 55 },
}

const graphPositions = new Map<
  string,
  { x: number; y: number }
>()

let fallbackIndex = 0

graphNodesForView.forEach((node) => {
  const preferred =
    preferredGraphPositions[node.name.toLowerCase()]

  if (preferred) {
    graphPositions.set(node.id, preferred)
    return
  }

  const angle =
    -Math.PI / 2 +
    (2 * Math.PI * fallbackIndex) /
      Math.max(graphNodesForView.length, 1)

  fallbackIndex += 1

  graphPositions.set(node.id, {
    x: 280 + 175 * Math.cos(angle),
    y: 145 + 96 * Math.sin(angle),
  })
})

const graphEdgesForView = (graphData?.edges ?? [])
  .filter(
    (edge) =>
      graphPositions.has(edge.source_id) &&
      graphPositions.has(edge.target_id),
  )
  .slice(0, 12)

const selectedGraphNode =
  graphNodesForView.find(
    (node) => node.id === selectedGraphNodeId,
  ) ?? null

const selectedGraphRelations = (
  graphData?.edges ?? []
).filter(
  (edge) =>
    edge.source_id === selectedGraphNodeId ||
    edge.target_id === selectedGraphNodeId,
)

const queryPathEdges: GraphEdge[] = (() => {
  if (
    !queryResponse ||
    queryResponse.intent !== 'MULTI_HOP' ||
    !graphData
  ) {
    return []
  }

  const steps = queryResponse.plan?.steps ?? []

  const firstStep = steps.find(
    (step) => step.operation === 'TRAVERSE',
  )

  const secondStep = steps.find(
    (step) => step.operation === 'FILTER_PATH',
  )

  if (
    !firstStep?.entity ||
    !firstStep.predicate ||
    !secondStep?.predicate ||
    !secondStep.target
  ) {
    return []
  }

  const firstEdges = graphData.edges.filter(
    (edge) =>
      edge.source.toLowerCase() ===
        firstStep.entity!.toLowerCase() &&
      edge.predicate === firstStep.predicate,
  )

  for (const firstEdge of firstEdges) {
    const secondEdge = graphData.edges.find(
      (edge) =>
        edge.source_id === firstEdge.target_id &&
        edge.predicate === secondStep.predicate &&
        edge.target.toLowerCase() ===
          secondStep.target!.toLowerCase(),
    )

    if (secondEdge) {
      return [firstEdge, secondEdge]
    }
  }

  return []
})()

useEffect(() => {
  let active = true

  const loadBenchmark = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/benchmark`,
      )

      if (!response.ok) {
        throw new Error(
          `Benchmark API returned ${response.status}`,
        )
      }

      const data =
        (await response.json()) as BenchmarkSnapshot

      if (active) {
        setBenchmarkData(data)
        setBenchmarkError('')
      }
    } catch (error) {
      if (active) {
        setBenchmarkError(
          error instanceof Error
            ? error.message
            : 'Unable to load benchmark data.',
        )
      }
    } finally {
      if (active) {
        setBenchmarkLoading(false)
      }
    }
  }

  void loadBenchmark()

  return () => {
    active = false
  }
}, [])
  const handlePreview = async () => {
  const trimmedQuery = query.trim()

  if (!trimmedQuery || isLoading) return

  setIsLoading(true)
  setHasPreview(false)
  setQueryResponse(null)
  setQueryError('')

  try {
    const response = await fetch(
      `${API_BASE_URL}/query`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: trimmedQuery,
        }),
      },
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        typeof data.detail === 'string'
          ? data.detail
          : `Request failed: ${response.status}`,
      )
    }

    setQueryResponse(data as QueryResponse)
    setHasPreview(true)
  } catch (error) {
    setQueryError(
      error instanceof Error
        ? error.message
        : 'Unable to connect to the Graphitti API.',
    )
    setHasPreview(true)
  } finally {
    setIsLoading(false)
  }
}

  const handleQueryChange = (
    event: React.ChangeEvent<HTMLTextAreaElement>,
  ) => {
    setQuery(event.target.value)
    setHasPreview(false)
    setQueryResponse(null)
    setQueryError('')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="Graphitti home">
          <div className="brand-mark">
            <svg viewBox="0 0 40 40" fill="none" aria-hidden="true">
              <path
                d="M10 11L29 10L31 29L11 30L10 11Z"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path
                d="M10 11L20 20L29 10M20 20L31 29M20 20L11 30"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <circle cx="10" cy="11" r="3" fill="#65E6D0" />
              <circle cx="29" cy="10" r="3" fill="#A78BFA" />
              <circle cx="31" cy="29" r="3" fill="#65E6D0" />
              <circle cx="11" cy="30" r="3" fill="#A78BFA" />
              <circle cx="20" cy="20" r="3.5" fill="currentColor" />
            </svg>
          </div>

          <span className="brand-copy">
            <strong>graphitti</strong>
            <small>GRAPH INTELLIGENCE</small>
          </span>
        </a>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="side-nav" aria-label="Main navigation">
          {[
            ['Overview', '⌂'],
            ['Knowledge graph', '◎'],
            ['Retrieval lab', '⌘'],
            ['Agent traces', '⌁'],
            ['Benchmarks', '▥'],
          ].map(([label, icon]) => (
            <button
              key={label}
              className={`nav-item ${activeNav === label ? 'active' : ''}`}
              onClick={() => setActiveNav(label)}
              type="button"
            >
              <span className="nav-icon">{icon}</span>
              <span>{label}</span>
              {label === 'Knowledge graph' && (
                <span className="nav-count">43</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <div className="connection-heading">
              <span className="status-dot" />
              <span>Neo4j database</span>
            </div>
            <strong>Container running</strong>
            <small>localhost:7687</small>
          </div>

          <div className="connection-card api-card">
            <div className="connection-heading">
              <span className="status-dot status-pending" />
              <span>Application API</span>
            </div>
            <strong>Integration pending</strong>
            <small>Local frontend preview</small>
          </div>

          <div className="sidebar-footer">
            <span className="avatar">G</span>
            <div className="user-copy">
              <strong>Graphitti</strong>
              <small>Local environment</small>
            </div>
            <span className="footer-dots">···</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Workspace</span>
            <span className="breadcrumb-separator">/</span>
            <strong>{activeNav}</strong>
          </div>

          <div className="topbar-right">
            <span className="environment-badge">
              <span className="status-dot" />
              LOCAL ENVIRONMENT
            </span>
            <button
              className="icon-button"
              title="Workspace information"
              type="button"
              onClick={() =>
                window.alert(
                  'Graphitti is running in local preview mode. Backend API integration is pending.',
                )
              }
            >
              ?
            </button>
          </div>
        </header>

        <div className="page-content">
          <section className="welcome-section">
            <div className="eyebrow">
              <span className="eyebrow-line" />
              GRAPH-NATIVE WEB INTELLIGENCE
            </div>

            <div className="welcome-row">
              <div>
                <h1>
                  Intelligence,
                  <br />
                  <span>connected.</span>
                </h1>
                <p className="welcome-description">
                  Explore relationships, retrieve evidence and trace
                  answers through your knowledge graph.
                </p>
              </div>

              <div className="version-card">
                <div className="version-orbit">✳</div>
                <div>
                  <small>PLATFORM</small>
                  <strong>Graphitti Core</strong>
                  <span>Local development</span>
                </div>
              </div>
            </div>
          </section>

          <IngestionPanel
  onIngested={() => setGraphRefreshKey((key) => key + 1)}
/>
          <section className="query-section">
            <div className="section-heading">
              <div>
                <span className="section-kicker">01 / QUERY ENGINE</span>
                <h2>Ask your knowledge graph</h2>
              </div>
              <span className="preview-badge">UI PREVIEW</span>
            </div>

            <div className="query-box">
              <label htmlFor="query-input" className="query-label">
                Your question
              </label>

              <textarea
                id="query-input"
                value={query}
                onChange={handleQueryChange}
                placeholder="Ask a question about your knowledge graph..."
                rows={3}
              />

              <div className="query-footer">
                <span className="query-hint">
                  ↳ Natural language · Multi-hop questions supported
                </span>

                <button
  type="button"
  className="primary-button"
  onClick={handlePreview}
  disabled={!query.trim() || isLoading}
  aria-busy={isLoading}
>
  {isLoading ? 'Querying graph...' : 'Run query'}
  <span aria-hidden="true">
    {isLoading ? '…' : '↗'}
  </span>
</button>
              </div>
            </div>

            <div className="quick-queries">
              <span>TRY A QUERY</span>
              {quickQueries.map((item) => (
                <button
                  key={item}
                  type="button"
                  className="query-chip"
                  onClick={() => {
                    setQuery(item)
                    setHasPreview(false)
                  }}
                >
                  {item}
                </button>
              ))}
            </div>

            {hasPreview && (
  <div className="api-response" role="status" aria-live="polite">
    {queryError ? (
      <div className="api-error">
        <strong>Query failed</strong>
        <p>{queryError}</p>
        <small>
          Verify that the Graphitti backend is running at
          {' '}http://127.0.0.1:8000.
        </small>
      </div>
    ) : queryResponse ? (
      <>
        <div className="api-response-header">
          <div>
            <span className="section-kicker">LIVE API RESPONSE</span>
            <h3>Answer</h3>
          </div>

          <span
            className={
              queryResponse.status === 'COMPLETED'
                ? 'success-badge'
                : 'preview-badge'
            }
          >
            {queryResponse.status}
          </span>
        </div>

        <p className="api-answer">
          {queryResponse.answer || 'No answer returned.'}
        </p>

        <div className="api-response-metrics">
          <div>
            <span>Intent</span>
            <strong>{queryResponse.intent}</strong>
          </div>

          <div>
            <span>Confidence</span>
            <strong>
              {(queryResponse.confidence * 100).toFixed(1)}%
            </strong>
          </div>

          <div>
            <span>Latency</span>
            <strong>{queryResponse.latency_ms.toFixed(2)} ms</strong>
          </div>

          <div>
            <span>Attempts</span>
            <strong>{queryResponse.attempts}</strong>
          </div>
        </div>

        <div className="api-citations">
          <h4>Evidence & sources ({queryResponse.citations.length})</h4>

          {queryResponse.citations.length === 0 ? (
            <p>No source citations were returned.</p>
          ) : (
            queryResponse.citations.map((citation, index) => (
              <article
                className="api-citation"
                key={`${citation.chunk_id}-${index}`}
              >
                <span className="evidence-label">
                  SOURCE {index + 1}
                </span>

                <>
  {citation.subject && citation.predicate && citation.object && (
    <p className="citation-relation">
      <strong>{citation.subject}</strong>
      {' — '}
      <span>{citation.predicate}</span>
      {' → '}
      <strong>{citation.object}</strong>
    </p>
  )}

  <p className="citation-source-excerpt">
    <span className="citation-excerpt-label">SOURCE EXCERPT</span>
    {citation.source_sentence}
  </p>
</>

                <div className="api-citation-footer">
                  <span>
                    Confidence: {(citation.confidence * 100).toFixed(1)}%
                  </span>

                  <a
                    href={citation.source_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open source ↗
                  </a>
                </div>
              </article>
            ))
          )}
        </div>
      </>
    ) : (
      <p>No response data received from the API.</p>
    )}
  </div>
)}
          </section>

          <section className="metrics-section">
            <div className="section-heading compact-heading">
              <div>
                <span className="section-kicker">02 / GRAPH SNAPSHOT</span>
                <h2>Your knowledge base</h2>
              </div>
              <span className="muted-label">Last local sync</span>
            </div>

            <div className="metrics-grid">
              <article className="metric-card">
                <div className="metric-top">
                  <span className="metric-icon teal-icon">▤</span>
                  <span className="metric-unit">CHUNKS</span>
                </div>
                <strong className="metric-value">
  {graphLoading ? '…' : (graphData?.counts.chunks ?? '—')}
</strong>
                <span className="metric-caption">Semantic text units</span>
                <div className="metric-footer">
                  <span className="metric-line teal-line" />
                  <span>Processed corpus</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-top">
                  <span className="metric-icon purple-icon">◎</span>
                  <span className="metric-unit">ENTITIES</span>
                </div>
                <strong className="metric-value">
  {graphLoading ? '…' : (graphData?.counts.entities ?? '—')}
</strong>
                <span className="metric-caption">Unique graph nodes</span>
                <div className="metric-footer">
                  <span className="metric-line purple-line" />
                  <span>Entity-linked</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-top">
                  <span className="metric-icon blue-icon">◇</span>
                  <span className="metric-unit">CLAIMS</span>
                </div>
                <strong className="metric-value">
  {graphLoading ? '…' : (graphData?.counts.claims ?? '—')}
</strong>
                <span className="metric-caption">Stored source claims</span>
                <div className="metric-footer">
                  <span className="metric-line blue-line" />
                  <span>With provenance</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-top">
                  <span className="metric-icon amber-icon">⌘</span>
                  <span className="metric-unit">RELATIONS</span>
                </div>
                <strong className="metric-value">
  {graphLoading ? '…' : (graphData?.counts.relations ?? '—')}
</strong>
                <span className="metric-caption">Unique semantic edges</span>
                <div className="metric-footer">
                  <span className="metric-line amber-line" />
                  <span>Typed relationships</span>
                </div>
              </article>
            </div>
          </section>

          <section className="analysis-grid">
            <article className="panel graph-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-kicker">03 / KNOWLEDGE GRAPH</span>
                  <h2>Relationship explorer</h2>
                </div>
                <span className="small-status">
  <span
    className={`status-dot ${
      graphError ? 'status-pending' : ''
    }`}
  />
  {graphLoading
    ? 'LOADING GRAPH'
    : graphError
      ? 'GRAPH UNAVAILABLE'
      : 'LIVE NEO4J DATA'}
</span>
              </div>

              <div className="graph-canvas">
                <div className="graph-background-grid" />

                {graphLoading ? (
  <div className="graph-load-state">
    Loading live Neo4j graph…
  </div>
) : graphError ? (
  <div className="graph-load-state graph-load-error">
    Unable to load graph: {graphError}
  </div>
) : graphNodesForView.length > 0 ? (
  <svg
    className="graph-lines"
    viewBox="0 0 560 305"
    preserveAspectRatio="xMidYMid meet"
    role="img"
    aria-label="Live knowledge graph retrieved from Neo4j"
  >
    <defs>
      <marker
        id="arrow-teal"
        markerWidth="7"
        markerHeight="7"
        refX="5"
        refY="3"
        orient="auto"
      >
        <path d="M0,0 L6,3 L0,6 Z" fill="#65e6d0" />
      </marker>

      <marker
        id="arrow-purple"
        markerWidth="7"
        markerHeight="7"
        refX="5"
        refY="3"
        orient="auto"
      >
        <path d="M0,0 L6,3 L0,6 Z" fill="#a78bfa" />
      </marker>
    </defs>

    {/* Actual directed relationships from Neo4j */}
    {graphEdgesForView.map((edge, index) => {
      const source = graphPositions.get(edge.source_id)
      const target = graphPositions.get(edge.target_id)

      if (!source || !target) {
        return null
      }

      const isUses = edge.predicate === 'USES'

      const hasReverseEdge = graphEdgesForView.some(
  (candidate) =>
    candidate.source_id === edge.target_id &&
    candidate.target_id === edge.source_id,
)

const sourceName = edge.source.toLowerCase()
const targetName = edge.target.toLowerCase()

const labelT =
  targetName === 'put'
    ? 0.68
    : sourceName === 'orjson' &&
        targetName === 'orjsonresponse'
      ? 0.38
      : hasReverseEdge
        ? 0.32
        : 0.55

const labelX =
  source.x + (target.x - source.x) * labelT

const labelY =
  source.y + (target.y - source.y) * labelT
      const labelWidth = Math.max(
        47,
        edge.predicate.length * 5.4 + 12,
      )

      return (
        <g
          key={`${edge.source_id}-${edge.predicate}-${edge.target_id}-${index}`}
        >
          <line
            x1={source.x}
            y1={source.y}
            x2={target.x}
            y2={target.y}
            className={`edge ${isUses ? 'edge-purple' : 'edge-teal'}`}
            markerEnd={
              isUses
                ? 'url(#arrow-purple)'
                : 'url(#arrow-teal)'
            }
          />

          <g className="edge-label">
            <rect
              x={labelX - labelWidth / 2}
y={labelY - 10}
              width={labelWidth}
              height={20}
              rx={5}
            />

            <text
              x={labelX}
y={labelY + 4}
            >
              {edge.predicate}
            </text>
          </g>
        </g>
      )
    })}

    {/* Actual entities returned by the graph API */}
    {graphNodesForView.map((node) => {
      const position = graphPositions.get(node.id)

      if (!position) {
        return null
      }

      const normalizedName = node.name.toLowerCase()

      const nodeClass =
        normalizedName === 'fastapi'
          ? 'node-main'
          : normalizedName === 'pydantic'
            ? 'node-pydantic'
            : normalizedName === 'starlette'
              ? 'node-starlette'
              : normalizedName === 'httpx'
                ? 'node-httpx'
                : normalizedName === 'uvicorn'
                  ? 'node-uvicorn'
                  : ''

      const isMain = nodeClass === 'node-main'

      return (
        <g
  key={node.id}
  className={`graph-node ${nodeClass}`}
  transform={`translate(${position.x} ${position.y})`}
  role="button"
  tabIndex={0}
  aria-label={`Select ${node.name}`}
  onClick={() => setSelectedGraphNodeId(node.id)}
  onKeyDown={(event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      setSelectedGraphNodeId(node.id)
    }
  }}
>
          <circle r={isMain ? 32 : 23} />

          {isMain && (
            <circle
              r={24}
              className="node-inner"
            />
          )}

          <text
            x={0}
            y={4}
          >
            {node.name.slice(0, 1).toUpperCase()}
          </text>

          <text
            x={0}
            y={isMain ? 51 : 38}
            className="node-label"
          >
            {node.name}
          </text>
        </g>
      )
    })}
  </svg>
) : (
  <div className="graph-load-state">
    No semantic relationships are available to display.
  </div>
)}

                <div className="graph-legend">
                  <span>
                    <i className="legend-dot teal-dot" />
                    Dependency
                  </span>
                  <span>
                    <i className="legend-dot purple-dot" />
                    Usage
                  </span>
                </div>
              </div>

              <div className="panel-bottom">
                <span>
  {graphLoading
    ? 'Loading entities…'
    : `${graphNodesForView.length} displayed entities`}
</span>
<span>·</span>
<span>
  {graphLoading
    ? 'Loading edges…'
    : `${graphEdgesForView.length} displayed relationships`}
</span>
<span className="panel-bottom-note">
  {graphData
    ? `Live graph · ${graphData.counts.relations} total semantic edges`
    : graphError
      ? 'Unable to load live graph'
      : 'Loading live graph'}
</span>


              </div>

              {selectedGraphNode && (
  <div className="selected-node-panel">
    <div className="selected-node-header">
      <div>
        <span className="section-kicker">
          SELECTED ENTITY
        </span>

        <h3>{selectedGraphNode.name}</h3>

        <code>{selectedGraphNode.id}</code>
      </div>

      <button
        type="button"
        className="node-clear-button"
        onClick={() => setSelectedGraphNodeId(null)}
      >
        Clear selection
      </button>
    </div>

    <div className="selected-node-summary">
      <span>
        {selectedGraphRelations.length} connected relationships
      </span>

      <span>
        {selectedGraphRelations.filter(
          (edge) => edge.source_id === selectedGraphNode.id,
        ).length} outgoing
      </span>

      <span>
        {selectedGraphRelations.filter(
          (edge) => edge.target_id === selectedGraphNode.id,
        ).length} incoming
      </span>
    </div>

    <div className="selected-node-relations">
      {selectedGraphRelations.length === 0 ? (
        <p>No semantic relationships found for this entity.</p>
      ) : (
        selectedGraphRelations.map((edge) => (
          <div
            className="selected-relation-row"
            key={`${edge.source_id}-${edge.predicate}-${edge.target_id}`}
          >
            <span className="relation-direction">
              {edge.source_id === selectedGraphNode.id
                ? 'OUTGOING'
                : 'INCOMING'}
            </span>

            <strong>{edge.source}</strong>

            <span className="relation-predicate">
              {edge.predicate}
            </span>

            <strong>{edge.target}</strong>

            {edge.claim_id && (
              <small>Claim: {edge.claim_id}</small>
            )}

            {edge.source_url && (
              <a
                href={edge.source_url}
                target="_blank"
                rel="noreferrer"
              >
                Source ↗
              </a>
            )}
          </div>
        ))
      )}
    </div>
  </div>
)}
            </article>

            <article className="panel evidence-panel">
  <div className="panel-heading">
    <div>
      <span className="section-kicker">04 / QUERY EVIDENCE</span>
      <h2>
        {queryResponse?.intent === 'MULTI_HOP'
          ? 'Multi-hop path'
          : 'Retrieved evidence'}
      </h2>
    </div>

    {queryResponse ? (
      <span
        className={
          queryResponse.status === 'COMPLETED'
            ? 'success-badge'
            : 'preview-badge'
        }
      >
        {queryResponse.status}
      </span>
    ) : (
      <span className="preview-badge">AWAITING QUERY</span>
    )}
  </div>

  <div className="evidence-query">
    <span className="evidence-label">LATEST QUERY</span>
    <p>
      {queryResponse?.query ??
        'Run a query to inspect its evidence and graph path.'}
    </p>
  </div>

  {!queryResponse ? (
    <div className="path-list">
      <p>
        Your latest query's graph path, retrieved evidence,
        and source details will appear here.
      </p>
    </div>
  ) : queryResponse.intent === 'MULTI_HOP' ? (
    <>
    <div className="path-list">
      {queryPathEdges.length > 0 ? (
        <>
          <div className="path-item">
            <span className="path-number">01</span>
            <div className="path-content">
              <strong>{queryPathEdges[0].source}</strong>
              <span>Source entity</span>
            </div>
            <span className="path-node-dot teal-dot" />
          </div>

          {queryPathEdges.map((edge, index) => (
            <div
              key={`${edge.source_id}-${edge.predicate}-${edge.target_id}`}
            >
              <div className="path-connector">
                <span />
                <code>{edge.predicate}</code>
              </div>

              <div className="path-item">
                <span className="path-number">
                  {String(index + 2).padStart(2, '0')}
                </span>

                <div className="path-content">
                  <strong>{edge.target}</strong>
                  <span>
                    {index === queryPathEdges.length - 1
                      ? 'Target entity'
                      : 'Intermediate entity'}
                  </span>
                </div>

                <span
                  className={`path-node-dot ${
                    index === queryPathEdges.length - 1
                      ? 'teal-dot'
                      : 'purple-dot'
                  }`}
                />
              </div>
            </div>
          ))}
        </>
      ) : (
        <p>
          No matching path was found in the currently loaded graph
          snapshot for this query. Check the returned evidence below.
        </p>
      )}
          </div>

      {queryResponse.citations.length > 0 && (
        <div className="api-citations multi-hop-citations">
          <h4>
            Supporting source evidence ({queryResponse.citations.length})
          </h4>

          {queryResponse.citations.slice(0, 4).map((citation, index) => (
            <article
              className="api-citation"
              key={`${citation.chunk_id}-${index}`}
            >
              <span className="evidence-label">
                SOURCE {index + 1}
              </span>

              <>
  {citation.subject && citation.predicate && citation.object && (
    <p className="citation-relation">
      <strong>{citation.subject}</strong>
      {' — '}
      <span>{citation.predicate}</span>
      {' → '}
      <strong>{citation.object}</strong>
    </p>
  )}

  <p className="citation-source-excerpt">
    <span className="citation-excerpt-label">SOURCE EXCERPT</span>
    {citation.source_sentence}
  </p>
</>

              <div className="api-citation-footer">
                <span>
                  Confidence: {(citation.confidence * 100).toFixed(1)}%
                </span>

                <a
                  href={citation.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open source ↗
                </a>
              </div>
            </article>
          ))}
        </div>
      )}
    </>
    ) : (
      <div className="api-citations">
      <h4>
        Source evidence ({queryResponse.citations.length})
      </h4>

      {queryResponse.citations.length === 0 ? (
        <p>No citations were returned for this query.</p>
      ) : (
        queryResponse.citations.slice(0, 4).map((citation, index) => (
          <article
            className="api-citation"
            key={`${citation.chunk_id}-${index}`}
          >
            <span className="evidence-label">
              SOURCE {index + 1}
            </span>

            <>
  {citation.subject && citation.predicate && citation.object && (
    <p className="citation-relation">
      <strong>{citation.subject}</strong>
      {' — '}
      <span>{citation.predicate}</span>
      {' → '}
      <strong>{citation.object}</strong>
    </p>
  )}

  <p className="citation-source-excerpt">
    <span className="citation-excerpt-label">SOURCE EXCERPT</span>
    {citation.source_sentence}
  </p>
</>

            <div className="api-citation-footer">
              <span>
                Confidence: {(citation.confidence * 100).toFixed(1)}%
              </span>

              <a
                href={citation.source_url}
                target="_blank"
                rel="noreferrer"
              >
                Open source ↗
              </a>
            </div>
          </article>
        ))
      )}
    </div>
  )}

  <div className="evidence-footer">
    <div>
      <span className="evidence-label">ANSWER CONFIDENCE</span>
      <strong>
        {(queryResponse?.confidence ?? 0) * 100}%
        <small>
          {queryResponse
            ? ` · ${queryResponse.latency_ms.toFixed(1)} ms`
            : ''}
        </small>
      </strong>
    </div>

    {queryResponse && (
      <span
        className={
          queryResponse.status === 'COMPLETED'
            ? 'success-badge'
            : 'preview-badge'
        }
      >
        {queryResponse.status}
      </span>
    )}
  </div>
</article>
          </section>

          <section className="retrieval-section">
            <div className="section-heading compact-heading">
              <div>
                <span className="section-kicker">05 / RETRIEVAL ABLATION</span>
                <h2>Retrieval performance</h2>
              </div>
              <span className="muted-label"><h2>
  Benchmark snapshot · {
    benchmarkLoading
      ? 'Loading…'
      : benchmarkData?.strategies.bm25
        ? `${benchmarkData.strategies.bm25.num_queries} queries`
        : 'Unavailable'
  }
</h2> </span>
            </div>

            <div className="strategy-grid">
  {strategyDefinitions.map((strategy) => {
    const summary = benchmarkData?.strategies[strategy.key]
    const mrr = summary?.mrr ?? 0

    return (
      <article className="strategy-card" key={strategy.key}>
        <div className="strategy-heading">
          <span>{strategy.name}</span>
          <span className="strategy-indicator" />
        </div>

        <strong>
          {benchmarkLoading
            ? '…'
            : summary
              ? summary.mrr.toFixed(4)
              : '—'}
        </strong>

        <p>{strategy.description}</p>

        <div className="score-track">
          <div
            className="score-fill"
            style={{
              width: `${Math.max(0, Math.min(1, mrr)) * 100}%`,
            }}
          />
        </div>

        <small>
          {benchmarkLoading
            ? 'Loading benchmark…'
            : summary
              ? `R@3 ${(summary.avg_recall_at_3 * 100).toFixed(1)}% · ${summary.avg_latency_ms.toFixed(2)} ms`
              : benchmarkError || 'Benchmark data unavailable'}
        </small>
      </article>
    )
  })}
</div>

{benchmarkData && (
  <p className="data-disclaimer">
    Multi-hop accuracy: {(benchmarkData.multi_hop.path_accuracy * 100).toFixed(1)}%
    {' · '}
    {benchmarkData.multi_hop.num_queries} queries
    {' · '}
    {benchmarkData.multi_hop.avg_latency_ms.toFixed(2)} ms avg latency
  </p>
)}

{benchmarkError && (
  <p className="data-disclaimer" role="status">
    Unable to load live benchmark data: {benchmarkError}
  </p>
)}

            <p className="data-disclaimer">
              Retrieval metrics are loaded from the local backend API using the latest saved benchmark results. Re-run the benchmark and refresh the page to see updated results.
            </p>
          </section>

          <footer className="page-footer">
            <span>GRAPHITTI CORE</span>
            <span>Graph-native intelligence for connected knowledge.</span>
            <span>LOCAL DEVELOPMENT</span>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App