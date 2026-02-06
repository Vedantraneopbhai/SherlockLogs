import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import Head from 'next/head'

export default function Home() {
  const [logFile, setLogFile] = useState(null)
  const canvasRef = useRef(null)
  const trailRef = useRef([])
  const [playbookFile, setPlaybookFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)
  const [searchFilter, setSearchFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [dragActive, setDragActive] = useState(false)
  const [analysisStage, setAnalysisStage] = useState('')

  // Fetch history on mount
  useEffect(() => {
    fetchHistory()
  }, [])

  // Mouse trail effect
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    let animationId
    let mouseX = 0
    let mouseY = 0
    
    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    
    const handleMouseMove = (e) => {
      mouseX = e.clientX
      mouseY = e.clientY
      trailRef.current.push({
        x: mouseX,
        y: mouseY,
        time: Date.now(),
        size: Math.random() * 10 + 5
      })
      // Keep only last 50 points
      if (trailRef.current.length > 50) {
        trailRef.current.shift()
      }
    }
    
    const drawTrail = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const now = Date.now()
      
      // Filter out old points (older than 1 second)
      trailRef.current = trailRef.current.filter(p => now - p.time < 1000)
      
      for (let i = 0; i < trailRef.current.length; i++) {
        const point = trailRef.current[i]
        const age = now - point.time
        const opacity = Math.max(0, 1 - age / 1000)
        const size = point.size * opacity
        
        // Create gradient for each point
        const gradient = ctx.createRadialGradient(
          point.x, point.y, 0,
          point.x, point.y, size * 2
        )
        
        // Cyber gradient colors
        const hue = (i * 5 + Date.now() / 20) % 360
        gradient.addColorStop(0, `hsla(${hue}, 100%, 70%, ${opacity * 0.8})`)
        gradient.addColorStop(0.4, `hsla(${(hue + 30) % 360}, 100%, 50%, ${opacity * 0.4})`)
        gradient.addColorStop(1, `hsla(${(hue + 60) % 360}, 100%, 50%, 0)`)
        
        ctx.beginPath()
        ctx.arc(point.x, point.y, size * 2, 0, Math.PI * 2)
        ctx.fillStyle = gradient
        ctx.fill()
      }
      
      // Draw connecting lines between points
      if (trailRef.current.length > 1) {
        ctx.beginPath()
        ctx.moveTo(trailRef.current[0].x, trailRef.current[0].y)
        for (let i = 1; i < trailRef.current.length; i++) {
          const point = trailRef.current[i]
          const age = now - point.time
          const opacity = Math.max(0, 1 - age / 1000) * 0.3
          ctx.lineTo(point.x, point.y)
        }
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.2)'
        ctx.lineWidth = 2
        ctx.stroke()
      }
      
      animationId = requestAnimationFrame(drawTrail)
    }
    
    window.addEventListener('mousemove', handleMouseMove)
    drawTrail()
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('resize', resizeCanvas)
      cancelAnimationFrame(animationId)
    }
  }, [])

  const fetchHistory = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/history')
      setHistory(response.data.analyses || [])
    } catch (err) {
      console.error('Failed to fetch history:', err)
    }
  }

  const handleAnalyze = async () => {
    if (!logFile) {
      setError('Please upload a log file to analyze')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    // Simulate analysis stages
    const stages = [
      'Uploading file...',
      'Parsing log entries...',
      'Detecting threats...',
      'Generating narrative...',
      'Fetching recommendations...'
    ]
    
    let stageIndex = 0
    const stageInterval = setInterval(() => {
      if (stageIndex < stages.length) {
        setAnalysisStage(stages[stageIndex])
        stageIndex++
      }
    }, 1500)

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
      fetchHistory() // Refresh history after new analysis
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      clearInterval(stageInterval)
      setAnalysisStage('')
      setLoading(false)
    }
  }

  // Drag and drop handlers
  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.name.endsWith('.log') || file.name.endsWith('.txt')) {
        setLogFile(file)
      }
    }
  }, [])

  // Load demo sample
  const loadDemo = async () => {
    try {
      const response = await fetch('/sample.log')
      const text = await response.text()
      const blob = new Blob([text], { type: 'text/plain' })
      const file = new File([blob], 'sample.log', { type: 'text/plain' })
      setLogFile(file)
    } catch (err) {
      // If sample file doesn't exist, create a mock one
      const sampleLog = `Feb  6 10:15:01 server sshd[12345]: Failed password for invalid user admin from 192.168.1.100 port 54321 ssh2
Feb  6 10:15:05 server sshd[12346]: Failed password for invalid user root from 192.168.1.100 port 54322 ssh2
Feb  6 10:15:10 server sshd[12347]: Failed password for invalid user test from 192.168.1.100 port 54323 ssh2
Feb  6 10:15:15 server sshd[12348]: Accepted password for admin from 192.168.1.50 port 54324 ssh2
Feb  6 10:16:01 server sshd[12349]: Failed password for invalid user guest from 10.0.0.50 port 54325 ssh2
Feb  6 10:16:05 server sshd[12350]: Failed password for root from 10.0.0.50 port 54326 ssh2`
      const blob = new Blob([sampleLog], { type: 'text/plain' })
      const file = new File([blob], 'sample_demo.log', { type: 'text/plain' })
      setLogFile(file)
    }
  }

  // Export results as JSON
  const exportJSON = () => {
    if (!result) return
    const dataStr = JSON.stringify(result, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sherlock-report-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Calculate threat severity
  const getThreatSeverity = () => {
    if (!result?.findings) return null
    const findings = result.findings
    const failedEvents = findings.filter(f => f.status === 'Failed').length
    const uniqueIPs = [...new Set(findings.filter(f => f.status === 'Failed').map(f => f.ip))].length
    
    if (failedEvents > 50 || uniqueIPs > 10) return { level: 'CRITICAL', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' }
    if (failedEvents > 20 || uniqueIPs > 5) return { level: 'HIGH', color: '#f97316', bg: 'rgba(249, 115, 22, 0.15)' }
    if (failedEvents > 5 || uniqueIPs > 2) return { level: 'MEDIUM', color: '#eab308', bg: 'rgba(234, 179, 8, 0.15)' }
    return { level: 'LOW', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' }
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

  // Filter findings
  const getFilteredFindings = () => {
    if (!result?.findings) return []
    return result.findings.filter(f => {
      const matchesSearch = searchFilter === '' || 
        (f.user && f.user.toLowerCase().includes(searchFilter.toLowerCase())) ||
        (f.ip && f.ip.includes(searchFilter)) ||
        (f.timestamp && f.timestamp.includes(searchFilter))
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'failed' && f.status === 'Failed') ||
        (statusFilter === 'success' && f.status === 'Accepted')
      return matchesSearch && matchesStatus
    })
  }

  const stats = result ? getStats() : null
  const severity = result ? getThreatSeverity() : null
  const filteredFindings = getFilteredFindings()

  return (
    <>
      <Head>
        <title>SherlockLogs | Incident Response Assistant</title>
        <meta name="description" content="AI-powered security log analysis and incident response" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Mouse trail canvas */}
      <canvas ref={canvasRef} className="mouse-trail-canvas" />
      
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
        <section className="upload-section" onDragEnter={handleDrag}>
          <div className="section-header-row">
            <h2 className="section-title">
              <span className="section-icon">📁</span>
              Upload Files for Analysis
            </h2>
            <div className="section-actions">
              <button className="action-btn demo-btn" onClick={loadDemo}>
                <span>🎮</span> Try Demo
              </button>
              <button 
                className={`action-btn history-btn ${showHistory ? 'active' : ''}`} 
                onClick={() => setShowHistory(!showHistory)}
              >
                <span>📜</span> History ({history.length})
              </button>
            </div>
          </div>

          {/* History Panel */}
          {showHistory && (
            <div className="history-panel">
              <h3 className="history-title">Recent Analyses</h3>
              {history.length === 0 ? (
                <p className="history-empty">No previous analyses found</p>
              ) : (
                <div className="history-list">
                  {history.slice(0, 5).map((item) => (
                    <div key={item.id} className="history-item">
                      <div className="history-item-info">
                        <span className="history-file">{item.file_path?.split(/[/\\]/).pop() || 'Unknown file'}</span>
                        <span className="history-date">{new Date(item.created_at).toLocaleString()}</span>
                      </div>
                      <div className="history-preview">{item.narrative?.slice(0, 100)}...</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {/* Drag & Drop Zone */}
          {dragActive && (
            <div 
              className="drag-overlay"
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="drag-content">
                <span className="drag-icon">📥</span>
                <span>Drop your log file here</span>
              </div>
            </div>
          )}
          
          <div className="upload-grid" onDragOver={handleDrag}>
            {/* Log File Upload */}
            <label className={`upload-card ${logFile ? 'has-file' : ''} ${dragActive ? 'drag-active' : ''}`}>
              <input
                type="file"
                accept=".log,.txt"
                onChange={(e) => setLogFile(e.target.files[0])}
              />
              <div className="upload-icon">📋</div>
              <div className="upload-label">Security Log File</div>
              <div className="upload-hint">Drag & drop or click to upload (.log, .txt)</div>
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
                <span>{analysisStage || 'Analyzing Threats...'}</span>
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
            {/* Export & Severity Header */}
            <div className="results-header">
              <div className="severity-badge" style={{ background: severity?.bg, borderColor: severity?.color }}>
                <span className="severity-dot" style={{ background: severity?.color }}></span>
                <span style={{ color: severity?.color }}>Threat Level: {severity?.level}</span>
              </div>
              <button className="export-btn" onClick={exportJSON}>
                <span>📥</span> Export JSON
              </button>
            </div>

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
                
                {/* Search and Filter Controls */}
                <div className="filter-controls">
                  <div className="search-box">
                    <span className="search-icon">🔍</span>
                    <input
                      type="text"
                      placeholder="Search by user, IP, or timestamp..."
                      value={searchFilter}
                      onChange={(e) => setSearchFilter(e.target.value)}
                      className="search-input"
                    />
                    {searchFilter && (
                      <button className="clear-search" onClick={() => setSearchFilter('')}>✕</button>
                    )}
                  </div>
                  <div className="status-filter">
                    <button 
                      className={`filter-btn ${statusFilter === 'all' ? 'active' : ''}`}
                      onClick={() => setStatusFilter('all')}
                    >
                      All
                    </button>
                    <button 
                      className={`filter-btn failed ${statusFilter === 'failed' ? 'active' : ''}`}
                      onClick={() => setStatusFilter('failed')}
                    >
                      Failed
                    </button>
                    <button 
                      className={`filter-btn success ${statusFilter === 'success' ? 'active' : ''}`}
                      onClick={() => setStatusFilter('success')}
                    >
                      Success
                    </button>
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
                      {filteredFindings.slice(0, 20).map((finding, idx) => (
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
                  {filteredFindings.length > 20 && (
                    <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '1rem' }}>
                      Showing 20 of {filteredFindings.length} filtered events
                    </p>
                  )}
                  {filteredFindings.length === 0 && (
                    <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                      No events match your filter criteria
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
