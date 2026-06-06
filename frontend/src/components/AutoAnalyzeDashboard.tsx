import { useState } from 'react'
import type { AppState } from '../App'
import { CheckCircle2, AlertTriangle, Lightbulb, Brain, Cpu, Sparkles } from 'lucide-react'

type Props = {
  session: AppState;
  updateSession: (s: Partial<AppState>) => void;
}

export default function AutoAnalyzeDashboard({ session, updateSession }: Props) {
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!session.df_json) {
      setError("Primero debes cargar un archivo en la pestaña 'Carga'.")
      return
    }
    
    setLoading(true)
    setError(null)
    setReport(null)

    const formData = new FormData()
    formData.append('df_json', session.df_json)

    try {
      const res = await fetch('/api/auto-analyze', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        setReport(data.report)
        if (data.df_json) {
          updateSession({
            df_json: data.df_json,
            columns: data.columns,
            numeric_columns: data.numeric_columns,
            shape: data.shape
          })
        }
      } else {
        setError(data.error || 'Error en el análisis.')
      }
    } catch (err) {
      setError('Error de red.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Analista Inteligente (Auto-Analyze)</h2>
      
      <div className="card" style={{ textAlign: 'center' }}>
        <p style={{ fontSize: '1.1rem', marginBottom: '24px' }}>
          Obtén un diagnóstico automático, detección de problemas, sugerencias de algoritmos y conclusiones de negocio con un solo clic.
        </p>
        <button onClick={handleAnalyze} className="btn btn-primary" style={{ padding: '16px 32px', fontSize: '1.1rem' }} disabled={loading}>
          {loading ? (
            <span className="flex items-center gap-2"><div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div> Analizando...</span>
          ) : (
            <span className="flex items-center gap-2"><Sparkles /> Generar Reporte Ejecutivo</span>
          )}
        </button>
        {error && <p style={{ color: '#ef4444', marginTop: '16px' }}>{error}</p>}
      </div>

      {report && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Diagnóstico */}
          {report.diagnostico_dataset && (
            <div className="card">
              <h3 className="flex items-center gap-2" style={{ color: 'var(--primary-color)' }}>
                <Cpu /> Perfil del Dataset
              </h3>
              <div className="grid-2 mt-4">
                <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px' }}>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)' }}>Filas</p>
                  <p style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-main)' }}>{report.diagnostico_dataset.rows}</p>
                </div>
                <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px' }}>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)' }}>Columnas</p>
                  <p style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-main)' }}>{report.diagnostico_dataset.columns}</p>
                </div>
              </div>
            </div>
          )}

          {/* Problemas */}
          <div className="card" style={{ borderLeft: '4px solid #ff4757' }}>
            <h3 className="flex items-center gap-2" style={{ color: '#ff4757' }}>
              <AlertTriangle /> Problemas Detectados
            </h3>
            {report.problemas_detectados && report.problemas_detectados.length > 0 ? (
              <ul style={{ paddingLeft: '24px', marginTop: '16px' }}>
                {report.problemas_detectados.map((issue: any, i: number) => (
                  <li key={i} style={{ marginBottom: '8px' }}>
                    <strong>{issue.column}</strong>: {issue.issue}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="flex items-center gap-2 mt-4" style={{ color: '#2ed573' }}>
                <CheckCircle2 size={18} /> El dataset parece estar limpio de nulos y atípicos graves.
              </p>
            )}
          </div>

          {/* Recomendaciones */}
          {report.transformaciones_recomendadas && report.transformaciones_recomendadas.length > 0 && (
            <div className="card" style={{ borderLeft: '4px solid #ffa502' }}>
              <h3 className="flex items-center gap-2" style={{ color: '#ffa502' }}>
                <Lightbulb /> Sugerencias de Limpieza
              </h3>
              <ul style={{ paddingLeft: '24px', marginTop: '16px' }}>
                {report.transformaciones_recomendadas.map((rec: any, i: number) => (
                  <li key={i} style={{ marginBottom: '8px' }}>
                    <strong>{rec.column}:</strong> {rec.recommendation} <em style={{ color: 'var(--text-muted)' }}>({rec.reason})</em>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Insights de Negocio */}
          {report.conclusiones_negocio && report.conclusiones_negocio.length > 0 && (
            <div className="card" style={{ borderLeft: '4px solid #3742fa', backgroundColor: '#f1f2f6' }}>
              <h3 className="flex items-center gap-2" style={{ color: '#3742fa' }}>
                <Sparkles /> Conclusiones Analíticas (Insights)
              </h3>
              <ul style={{ paddingLeft: '24px', marginTop: '16px' }}>
                {report.conclusiones_negocio.map((insight: string, i: number) => (
                  <li key={i} style={{ marginBottom: '8px' }}>{insight}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Modelos Sugeridos */}
          {report.modelos_sugeridos && report.modelos_sugeridos.length > 0 && (
            <div className="card" style={{ borderLeft: '4px solid #2f3542' }}>
              <h3 className="flex items-center gap-2" style={{ color: '#2f3542' }}>
                <Brain /> Sugerencias de Machine Learning
              </h3>
              <div className="grid-2 mt-4">
                {report.modelos_sugeridos.map((mod: any, i: number) => (
                  <div key={i} style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <p style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>{mod.task}</p>
                    <p style={{ fontSize: '0.875rem', color: 'var(--primary-color)', fontWeight: 500, marginBottom: '8px' }}>
                      {mod.models.join(" • ")}
                    </p>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0 }}>{mod.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
