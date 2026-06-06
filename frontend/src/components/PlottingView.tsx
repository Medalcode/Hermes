import { useState, useEffect } from 'react'
import type { AppState } from '../App'
import Plot from 'react-plotly.js'
import { BarChart } from 'lucide-react'

type Props = {
  session: AppState;
}

export default function PlottingView({ session }: Props) {
  const [plotType, setPlotType] = useState('correlation')
  const [plotCol, setPlotCol] = useState('')
  const [plotX, setPlotX] = useState('')
  const [plotY, setPlotY] = useState('')
  const [plotData, setPlotData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Set defaults when session changes
    if (session.columns.length > 0) {
      if (!plotCol) setPlotCol(session.numeric_columns[0] || session.columns[0])
      if (!plotX) setPlotX(session.numeric_columns[0] || session.columns[0])
      if (!plotY) setPlotY(session.numeric_columns[1] || session.columns[1] || session.columns[0])
    }
  }, [session])

  const handlePlot = async () => {
    if (!session.df_json) {
      setError("Carga un dataset primero.")
      return
    }
    setLoading(true)
    setError(null)
    
    const formData = new FormData()
    formData.append('df_json', session.df_json)
    formData.append('type', plotType)
    if (plotType === 'distribution' && plotCol) formData.append('col', plotCol)
    if ((plotType === 'regression' || plotType === 'cluster') && plotX && plotY) {
      formData.append('x', plotX)
      formData.append('y', plotY)
    }

    try {
      const res = await fetch('/api/plot', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        setPlotData(data)
      } else {
        setError(data.error || 'Error al generar el gráfico.')
      }
    } catch (err) {
      setError('Error de red.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Visualización Interactiva</h2>
      <div className="card">
        <div className="flex items-center gap-4 mb-4" style={{ flexWrap: 'wrap' }}>
          <select value={plotType} onChange={e => setPlotType(e.target.value)} style={{ width: '250px' }}>
            <option value="correlation">Correlación (Heatmap)</option>
            <option value="distribution">Distribución</option>
            <option value="regression">Regresión</option>
            <option value="cluster">Ver Clusters</option>
          </select>

          {plotType === 'distribution' && (
            <select value={plotCol} onChange={e => setPlotCol(e.target.value)} style={{ width: '200px' }}>
              {session.numeric_columns.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          )}

          {(plotType === 'regression' || plotType === 'cluster') && (
            <>
              <select value={plotX} onChange={e => setPlotX(e.target.value)} style={{ width: '200px' }}>
                <option value="" disabled>Eje X</option>
                {session.numeric_columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <select value={plotY} onChange={e => setPlotY(e.target.value)} style={{ width: '200px' }}>
                <option value="" disabled>Eje Y</option>
                {session.numeric_columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </>
          )}

          <button onClick={handlePlot} className="btn btn-primary" disabled={loading}>
            {loading ? 'Generando...' : 'Generar Gráfico'}
          </button>
        </div>
        {error && <p style={{ color: '#ef4444' }}>{error}</p>}
      </div>

      <div className="card" style={{ minHeight: '500px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'white' }}>
        {plotData ? (
          <Plot
            data={plotData.data}
            layout={{ ...plotData.layout, autosize: true, margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 } }}
            useResizeHandler={true}
            style={{ width: '100%', height: '100%' }}
            config={{ responsive: true, displayModeBar: false }}
          />
        ) : (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center' }}>
            <BarChart size={48} style={{ opacity: 0.2, margin: '0 auto 16px' }} />
            <p>Selecciona los parámetros y haz clic en "Generar Gráfico"</p>
          </div>
        )}
      </div>
    </div>
  )
}
