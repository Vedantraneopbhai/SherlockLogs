import { useState } from 'react'
import axios from 'axios'
import Head from 'next/head'

export default function Home() {
  const [logFile, setLogFile] = useState(null)
  const [playbookFile, setPlaybookFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleAnalyze = async () => {
    if (!logFile) {
      setError('Please upload a log file to analyze')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('logfile', logFile)
    if (playbookFile) {
      formData.append('playbook', playbookFile)
    }

    try {
      const response = await axios.post('http://127.0.0.1:8000/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const getStats = () => {
    if (!result?.findings) return null
    const findings = result.findings
    const totalEvents = findings.length
    const failedEvents = findings.filter(f => f.status === 'Failed').length
    const successEvents = findings.filter(f => f.status === 'Accepted').length
    const uniqueIPs = [...new Set(findings.map(f => f.ip))].length
    return { totalEvents, failedEvents, successEvents, uniqueIPs }
  }

  const stats = result ? getStats() : null

  return (
    <>
      <Head>
        <title>SherlockLogs | Incident Response Assistant</title>
        <meta name="description" content="AI-powered security log analysis and incident response" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Animated gradient orbs */}
      <div className="gradient-orb gradient-orb-1"></div>
      <div className="gradient-orb gradient-orb-2"></div>
      <div className="gradient-orb gradient-orb-3"></div>
      <div className="grid-pattern"></div>
      
      <div className="container">
        {/* Header */}
        <header className="header">
          <div className="logo-container">
            <div className="logo-icon">🔍</div>
            <h1 className="title">SherlockLogs</h1>
          </div>
          <p className="subtitle">AI-Powered Security Log Analysis & Incident Response</p>
          <div className="cyber-badge">
            <span>🛡️</span>
            <span>THREAT DETECTION ACTIVE</span>
          </div>
        </header>

        {/* Upload Section */}
        <section className="upload-section">
          <h2 className="section-title">
            <span className="section-icon">📁</span>
            Upload Files for Analysis
          </h2>
          
          <div className="upload-grid">
            {/* Log File Upload */}
            <label className={`upload-card ${logFile ? 'has-file' : ''}`}>
              <input
                type="file"
                accept=".log,.txt"
                onChange={(e) => setLogFile(e.target.files[0])}
              />
              <div className="upload-icon">📋</div>
              <div className="upload-label">Security Log File</div>
              <div className="upload-hint">auth.log, syslog, or any .log/.txt file</div>
              {logFile && <div className="file-name">✓ {logFile.name}</div>}
            </label>

            {/* Playbook File Upload */}
            <label className={`upload-card ${playbookFile ? 'has-file' : ''}`}>
              <input
                type="file"
                accept=".md,.txt"
                onChange={(e) => setPlaybookFile(e.target.files[0])}
              />
              <div className="upload-icon">📖</div>
              <div className="upload-label">Incident Playbook (Optional)</div>
              <div className="upload-hint">Custom response playbook (.md or .txt)</div>
              {playbookFile && <div className="file-name">✓ {playbookFile.name}</div>}
            </label>
          </div>

          {/* Analyze Button */}
          <button
            className={`analyze-btn ${loading ? 'loading' : ''}`}
            onClick={handleAnalyze}
            disabled={loading || !logFile}
            style={{ marginTop: '1.5rem' }}
          >
            {loading ? (
              <>
                <div className="loading-spinner"></div>
                <span>Analyzing Threats...</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>Analyze & Generate Report</span>
              </>
            )}
          </button>
        </section>

        {/* Error Display */}
        {error && (
          <div className="error-container">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{error}</span>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <div className="results-section">
            {/* Stats Grid */}
            {stats && (
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{stats.totalEvents}</div>
                  <div className="stat-label">Total Events</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ background: 'linear-gradient(135deg, #ef4444, #f97316)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{stats.failedEvents}</div>
                  <div className="stat-label">Failed Attempts</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{stats.successEvents}</div>
                  <div className="stat-label">Successful Logins</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ background: 'linear-gradient(135deg, #8b5cf6, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{stats.uniqueIPs}</div>
                  <div className="stat-label">Unique IPs</div>
                </div>
              </div>
            )}

            {/* Narrative Card */}
            <div className="result-card">
              <div className="result-header">
                <div className="result-icon narrative">📝</div>
                <div>
                  <div className="result-title">Incident Narrative</div>
                  <div className="result-subtitle">AI-generated story of what happened</div>
                </div>
              </div>
              <div className="narrative-content">
                {result.narrative}
              </div>
            </div>

            {/* Recommendations Card */}
            {result.recs && result.recs.length > 0 && (
              <div className="result-card">
                <div className="result-header">
                  <div className="result-icon recommendations">🎯</div>
                  <div>
                    <div className="result-title">Response Recommendations</div>
                    <div className="result-subtitle">Playbook-based incident response steps</div>
                  </div>
                </div>
                <ul className="recommendations-list">
                  {result.recs.map((rec, idx) => (
                    <li key={idx} className="recommendation-item">
                      <span className="recommendation-bullet">{idx + 1}</span>
                      <span className="recommendation-text">
                        <strong>{rec.title}</strong><br/>{rec.content}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Findings Table */}
            {result.findings && result.findings.length > 0 && (
              <div className="result-card">
                <div className="result-header">
                  <div className="result-icon findings">🔎</div>
                  <div>
                    <div className="result-title">Detailed Findings</div>
                    <div className="result-subtitle">Parsed log events with threat indicators</div>
                  </div>
                </div>
                <div className="findings-container">
                  <table className="findings-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>User</th>
                        <th>IP Address</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.findings.slice(0, 20).map((finding, idx) => (
                        <tr key={idx}>
                          <td>{finding.timestamp || 'N/A'}</td>
                          <td>{finding.user || 'unknown'}</td>
                          <td>{finding.ip || 'N/A'}</td>
                          <td>
                            <span className={`status-badge ${finding.status === 'Failed' ? 'failed' : 'success'}`}>
                              {finding.status === 'Failed' ? '✗' : '✓'} {finding.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {result.findings.length > 20 && (
                    <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '1rem' }}>
                      Showing 20 of {result.findings.length} events
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <footer className="footer">
          <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            <span style={{ background: 'var(--gradient-cyber)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontWeight: '600' }}>SherlockLogs</span> — Transforming security logs into actionable intelligence
          </p>
          <p>
            Powered by <a href="#">FastAPI</a> • <a href="#">Gemini AI</a> • <a href="#">RAG</a>
          </p>
        </footer>
      </div>
    </>
  )
}
