import { useState, type FormEvent } from 'react'
import './IngestionPanel.css'

type IngestionSummary = {
  pages_processed: number
  chunks_created: number
  entities_extracted: number
  relations_extracted: number
  claims_generated: number
  graph_ingestion: string
}

type CrawledPage = {
  url: string
  title: string
  depth: number
  content_preview: string
}

type CrawlResponse = {
  status: string
  start_url: string
  pages_crawled: number
  dataset: string
  ingestion: IngestionSummary
  pages: CrawledPage[]
}

type IngestionPanelProps = {
  onIngested?: () => void
}

const API_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

function IngestionPanel({ onIngested }: IngestionPanelProps) {
  const [url, setUrl] = useState('')
  const [maxDepth, setMaxDepth] = useState(0)
  const [maxPages, setMaxPages] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<CrawlResponse | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    let parsedUrl: URL

    try {
      parsedUrl = new URL(url.trim())
    } catch {
      setError('Please enter a valid website URL.')
      return
    }

    if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
      setError('Only HTTP and HTTPS URLs are supported.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/crawl`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: parsedUrl.toString(),
          max_depth: maxDepth,
          max_pages: maxPages,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : `Ingestion failed with status ${response.status}.`,
        )
      }

      setResult(data as CrawlResponse)
      onIngested?.()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to connect to the Graphitti backend.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="ingestion-section">
      <div className="ingestion-heading">
        <div>
          <span className="section-kicker">00 / KNOWLEDGE INGESTION</span>
          <h2>Connect a website</h2>
          <p>
            Turn website content into searchable knowledge and connected
            relationships.
          </p>
        </div>

        <span className="ingestion-icon" aria-hidden="true">
          ↗
        </span>
      </div>

      <form className="ingestion-form" onSubmit={handleSubmit}>
        <label htmlFor="website-url">Website URL</label>

        <div className="website-input-row">
          <input
            id="website-url"
            type="url"
            placeholder="https://docs.example.com/"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            required
            disabled={loading}
          />

          <button
            className="primary-button ingestion-submit"
            type="submit"
            disabled={loading || !url.trim()}
          >
            {loading ? 'Processing…' : 'Ingest website'}
            <span aria-hidden="true">{loading ? '…' : '↗'}</span>
          </button>
        </div>

        <div className="ingestion-options">
          <div>
            <label htmlFor="crawl-depth">Crawl depth</label>
            <select
              id="crawl-depth"
              value={maxDepth}
              onChange={(event) => setMaxDepth(Number(event.target.value))}
              disabled={loading}
            >
              <option value={0}>0 — Starting page only</option>
              <option value={1}>1 — Direct links</option>
              <option value={2}>2 — Two levels deep</option>
            </select>
          </div>

          <div>
            <label htmlFor="crawl-pages">Maximum pages</label>
            <input
              id="crawl-pages"
              type="number"
              min={1}
              max={20}
              value={maxPages}
              onChange={(event) => {
                const value = Number(event.target.value)
                if (Number.isInteger(value) && value >= 1 && value <= 20) {
                  setMaxPages(value)
                }
              }}
              disabled={loading}
              required
            />
          </div>
        </div>

        <p className="ingestion-hint">
          Start with 1–3 pages while testing. Processing may take a few
          minutes depending on the content and model initialization.
        </p>
      </form>

      {loading && (
        <div className="ingestion-progress" role="status" aria-live="polite">
          <span className="ingestion-spinner" />
          <div>
            <strong>Building your knowledge graph</strong>
            <p>
              Crawling, extracting content, detecting entities and preparing
              graph claims. Keep this page open until the request finishes.
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="ingestion-error" role="alert">
          <strong>Ingestion failed</strong>
          <p>{error}</p>
          <small>
            Check that the backend and Neo4j are running, then try again.
          </small>
        </div>
      )}

      {result && (
        <div className="ingestion-result" role="status" aria-live="polite">
          <div className="ingestion-result-heading">
            <div>
              <span className="section-kicker">INGESTION REPORT</span>
              <h3>Website processed</h3>
            </div>
            <span className="success-badge">
              {result.status.toUpperCase()}
            </span>
          </div>

          <a
            className="ingestion-source-link"
            href={result.start_url}
            target="_blank"
            rel="noreferrer"
          >
            {result.start_url} ↗
          </a>

          <div className="ingestion-metrics">
            <div>
              <span>Pages</span>
              <strong>{result.pages_crawled}</strong>
            </div>
            <div>
              <span>Chunks</span>
              <strong>{result.ingestion.chunks_created}</strong>
            </div>
            <div>
              <span>Entities</span>
              <strong>{result.ingestion.entities_extracted}</strong>
            </div>
            <div>
              <span>Relations</span>
              <strong>{result.ingestion.relations_extracted}</strong>
            </div>
            <div>
              <span>Claims</span>
              <strong>{result.ingestion.claims_generated}</strong>
            </div>
          </div>

          <div className="ingestion-graph-status">
            <span className="status-dot" />
            Graph ingestion: {result.ingestion.graph_ingestion}
          </div>

          {result.pages.length > 0 && (
            <div className="ingestion-page-list">
              <h4>Crawled pages</h4>
              {result.pages.slice(0, 5).map((page) => (
                <a
                  key={page.url}
                  href={page.url}
                  target="_blank"
                  rel="noreferrer"
                  className="ingestion-page"
                >
                  <span>
                    <strong>{page.title || page.url}</strong>
                    <small>{page.url}</small>
                  </span>
                  <span aria-hidden="true">↗</span>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default IngestionPanel